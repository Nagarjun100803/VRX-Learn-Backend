import asyncio
from datetime import UTC, datetime
from typing import ClassVar, Optional, Type
from uuid import uuid4

from asyncpg import Connection

from src.auth import Entity
from src.command.commands.assignment_submissions import (
    AssignmentSubmission,
    AssignmentSubmissionAttachmentMetadata,
    AssignmentSubmissionAttachmentStatusUpdate,
    AssignmentSubmissionContext,
    AssignmentSubmissionCreate,
    AssignmentSubmissionCreateWithAttemptAndStatus,
    AssignmentSubmissionDetailContext,
    AssignmentSubmissionFeedbackUpdate,
    AssignmentSubmissionGet,
    AssignmentSubmissionGetCore,
    AssignmentSubmissionStatus,
    AssignmentSubmissionVerify,
    AssignmentSubmissionVerifyWithStatus,
    AssignmentSubmissionWithMedia,
)
from src.command.commands.assignments import AssignmentGet
from src.command.commands.base import AttachmentUploadContext, MediaContext
from src.command.commands.media import (
    MediableType,
    MediaCreate,
    MediaStatus,
    MediaStatusUpdateByMediable,
)
from src.command.repositories import (
    AssignmentRepository,
    AssignmentSubmissionRepository,
)
from src.command.services.base import BaseService
from src.command.services.media import AttachmentResolver, MediaService
from src.core.storage import FileMetadata, S3Bucket
from src.exceptions import (
    AssignmentNotFoundError,
    AssignmentSubmissionAlreadyVerified,
    AssignmentSubmissionMediaNotFoundError,
    AssignmentSubmissionMediaNotUploadedError,
    AssignmentSubmissionNotFoundError,
    AssignmentSubmissionNotGraded,
    EntityNotFoundError,
    InvalidScoreError,
    MaxAttemptsReachedError,
)


class AssignmentSubmissionService(BaseService[AssignmentSubmission]):
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = (
        AssignmentSubmissionNotFoundError
    )
    _entity: ClassVar[Entity] = Entity.ASSIGNMENT_SUBMISSION

    def __init__(
        self,
        repo: AssignmentSubmissionRepository,
        assignment_repo: AssignmentRepository,
        media_service: MediaService,
        file_service: S3Bucket,
        attachment_resolver: AttachmentResolver,
    ) -> None:
        self.repo = repo
        self.assignment_repo = assignment_repo
        self.media_service = media_service
        self.file_service = file_service
        self.attachment_resolver = attachment_resolver

    async def _create_submission(
        self, cmd: AssignmentSubmissionCreate, connection: Optional[Connection] = None
    ) -> AssignmentSubmission:
        # Check if the user can submit the assignment.
        assignment, total_attempt = await asyncio.gather(
            self.assignment_repo.get(AssignmentGet(id=cmd.assignment_id)),
            self.repo.count_attempts(
                user_id=cmd.created_by, assignment_id=cmd.assignment_id
            ),
        )

        if not assignment:
            raise AssignmentNotFoundError(value=cmd.assignment_id)

        if total_attempt >= assignment.number_of_attempts:
            raise MaxAttemptsReachedError(max_attempts=assignment.number_of_attempts)

        due_date = assignment.due_date
        if due_date is not None and due_date < datetime.now(tz=UTC):
            status = AssignmentSubmissionStatus.DONE_LATE
        else:
            status = AssignmentSubmissionStatus.SUBMITTED

        return await self.repo.add(
            cmd=AssignmentSubmissionCreateWithAttemptAndStatus(
                **cmd.model_dump(), attempt=total_attempt + 1, status=status
            ),
            connection=connection,
        )

    async def _generate_storage_key(
        self,
        cmd: AssignmentSubmissionCreate,
        attachment: AssignmentSubmissionAttachmentMetadata,
    ):

        assignment_details = await self.assignment_repo.pick(
            columns=["id", "course_id"], fetch_all=False, id=cmd.assignment_id
        )
        if assignment_details is None:
            raise AssignmentNotFoundError(value=cmd.assignment_id)

        return f"courses/C-{assignment_details['course_id']}/assignments/A-{assignment_details['id']}/submissions/{str(uuid4())}/{attachment.filename}"

    async def _prepare_media_create_payload(
        self,
        assignment_submission_id: int,
        cmd: AssignmentSubmissionCreate,
        attachment: AssignmentSubmissionAttachmentMetadata,
    ) -> MediaCreate:

        key = await self._generate_storage_key(cmd=cmd, attachment=attachment)

        return MediaCreate(
            filename=attachment.filename,
            mime_type=attachment.content_type,
            file_size=attachment.size,
            mediable_id=assignment_submission_id,
            mediable_type=MediableType.ASSIGNMENT_SUBMISSION,
            key=key,
            created_by=cmd.created_by,
        )

    async def create(
        self,
        cmd: AssignmentSubmissionCreate,
        attachment: AssignmentSubmissionAttachmentMetadata,
    ) -> AttachmentUploadContext[AssignmentSubmissionContext]:

        async with self.repo.db.transaction() as tconn:
            submission = await self._create_submission(cmd=cmd, connection=tconn)
            media_cmd = await self._prepare_media_create_payload(
                assignment_submission_id=submission.id, cmd=cmd, attachment=attachment
            )
            media = await self.media_service.create(cmd=media_cmd, connection=tconn)

        url = await self.file_service.get_upload_url(
            metadata=FileMetadata(
                key=media.key, filename=media.filename, content_type=media.mime_type
            )
        )
        return AttachmentUploadContext[AssignmentSubmissionContext](
            data=AssignmentSubmissionContext(**submission.model_dump()),
            media=MediaContext(
                id=media.id,
                url=url,
                filename=media.filename,
                content_type=media.mime_type,
                size=media.file_size,
            ),
        )

    async def grade(self, cmd: AssignmentSubmissionVerify) -> AssignmentSubmission:
        submission_context: Optional[
            AssignmentSubmissionDetailContext
        ] = await self.repo.submission_context(submission_id=cmd.id)

        if submission_context is None:
            raise AssignmentSubmissionNotFoundError(value=cmd.id)

        if submission_context.media is None:
            raise AssignmentSubmissionMediaNotFoundError()

        if submission_context.media.status != MediaStatus.UPLOADED:
            raise AssignmentSubmissionMediaNotUploadedError()

        if submission_context.submission.score is not None:
            raise AssignmentSubmissionAlreadyVerified()

        if cmd.score > submission_context.assignment.max_score:
            raise InvalidScoreError(max_score=submission_context.assignment.max_score)

        return self._require_entity(
            await self.repo.update(
                AssignmentSubmissionVerifyWithStatus(
                    **cmd.model_dump(), status=AssignmentSubmissionStatus.GRADED
                )
            )
        )

    async def update_feedback(
        self, cmd: AssignmentSubmissionFeedbackUpdate
    ) -> AssignmentSubmission:

        submission = await self.repo.get(query=AssignmentSubmissionGetCore(id=cmd.id))
        if submission is None:
            raise AssignmentSubmissionNotFoundError(value=cmd.id)

        if submission.score is None:
            raise AssignmentSubmissionNotGraded(
                message="Cannot update feedback for an ungraded submission."
            )

        return self._require_entity(await self.repo.update(cmd))

    async def get(self, query: AssignmentSubmissionGet) -> AssignmentSubmission:
        return self._require_entity(await self.repo.get(query), value=query.id)

    async def get_with_media(
        self, query: AssignmentSubmissionGet
    ) -> AssignmentSubmissionWithMedia:

        submission = await self.repo.get_with_media(query)

        if submission is None:
            raise AssignmentSubmissionNotFoundError(value=query.id)

        return submission

    # NOTE: This method does not require authorization.
    # Because it is used by the trainee to mark an attachment as uploaded.
    async def mark_attachment_as_uploaded(
        self, cmd: AssignmentSubmissionAttachmentStatusUpdate
    ) -> None:
        await self.media_service.update(
            cmd=MediaStatusUpdateByMediable(
                mediable_id=cmd.id,
                mediable_type=MediableType.ASSIGNMENT_SUBMISSION,
                updated_by=cmd.updated_by,
            )
        )

    async def get_attachment_view_url(self, query: AssignmentSubmissionGet) -> str:
        return await self.attachment_resolver.get_attachment_url(
            mediable_id=query.id, mediable_type=MediableType.ASSIGNMENT_SUBMISSION
        )
