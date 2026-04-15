import asyncio
from datetime import UTC, datetime
from typing import ClassVar, Optional, Type, Union, cast
from uuid import uuid4

from asyncpg import Connection
from slugify import slugify

from src.auth import Action, AuthService, Entity, require_authorization
from src.command.commands.assignment_submissions import (
    AllowedAssignmentSubmissionFileType,
    AssignmentSubmission,
    AssignmentSubmissionContext,
    AssignmentSubmissionCreate,
    AssignmentSubmissionCreateWithAttemptAndStatus,
    AssignmentSubmissionDetail,
    AssignmentSubmissionFeedbackUpdate,
    AssignmentSubmissionGet,
    AssignmentSubmissionGetCore,
    AssignmentSubmissionStatus,
    AssignmentSubmissionUpload,
    AssignmentSubmissionVerify,
    AssignmentSubmissionVerifyWithStatus,
    AssignmentSubmissionWithMedia,
)
from src.command.commands.assignments import AssignmentGet
from src.command.commands.media import (
    MediableType,
    MediaCreate,
    MediaDetail,
    MediaStatus,
)
from src.command.repositories.assignment_submissions import (
    AssignmentSubmissionRepository,
)
from src.command.repositories.assignments import AssignmentRepository
from src.command.services.base import BaseService
from src.command.services.files import FileMetadata
from src.command.services.media import MediaService
from src.events.events import AssignmentSubmissionCreatedEvent
from src.events.publishers import assignment_submission_created_publisher
from src.exceptions import (
    AssignmentNotFoundError,
    AssignmentSubmissionAlreadyVerified,
    AssignmentSubmissionMediaNotFoundError,
    AssignmentSubmissionMediaNotUploadedError,
    AssignmentSubmissionNotFoundError,
    AssignmentSubmissionNotGraded,
    EntityNotFoundError,
    FileSizeExceededError,
    InvalidContentTypeError,
    InvalidScoreError,
    MaxAttemptsReachedError,
)

MAX_FILE_SIZE_FOR_ASSIGNMENT_SUBMISSION = 5 * 1024 * 1024  # 5 Mega Bytes.


class AssignmentSubmissionService(BaseService[AssignmentSubmission]):
    """
    Service responsible for managing assignment submissions.

    This service handles the lifecycle of a student's submission to an assignment,
    including creation, retrieval, grading verification, feedback updates,
    and submission file attachment workflows.

    The service enforces domain rules such as:
    - Maximum number of submission attempts
    - Assignment due date validation
    - Score validation against assignment limits
    - File upload validation for submission attachments
    - Authorization checks for contextual access

    Submissions are treated as immutable records once submitted. Updates are
    restricted to grading verification and feedback updates performed by
    authorized users.

    Key Responsibilities
    --------------------
    - Create assignment submissions
    - Enforce submission attempt limits
    - Validate submission status (on-time vs late)
    - Verify grading and scores
    - Attach uploaded submission files
    - Enforce authorization and access control

    Example
    -------
    ```python
    service = AssignmentSubmissionService(
        repo=submission_repo,
        assignment_repo=assignment_repo,
        media_service=media_service,
        auth_service=auth_service
    )

    submission = await service.create(
        AssignmentSubmissionCreate(
            assignment_id=10,
            created_by=42
        )
    )
    ```
    """

    # Class varibales
    _not_found_exc: ClassVar[Type[EntityNotFoundError]] = (
        AssignmentSubmissionNotFoundError
    )
    _entity: ClassVar[Entity] = Entity.ASSIGNMENT_SUBMISSION

    def __init__(
        self,
        repo: AssignmentSubmissionRepository,
        assignment_repo: AssignmentRepository,
        media_service: MediaService,
        auth_service: AuthService,
    ) -> None:
        """
        Initialize the AssignmentSubmissionService.

        Parameters
        ----------
        repo : AssignmentSubmissionRepository
            Repository responsible for persistence of assignment submissions.

        assignment_repo : AssignmentRepository
            Repository used to retrieve assignment metadata required for
            submission validation (due date, max attempts, score limits).

        media_service : MediaService
            Service responsible for managing file uploads associated with
            submissions.

        auth_service : AuthService
            Authorization service used to verify access permissions for
            submission operations.

        Notes
        -----
        The service depends on multiple repositories and services to enforce
        domain-level validation and maintain transactional integrity for
        submission and media operations.
        """

        self.repo = repo
        self.assignment_repo = assignment_repo
        self.media_service = media_service
        self.auth_service = auth_service

    async def _get_assignment_submission(
        self, id: int
    ) -> Optional[AssignmentSubmission]:
        """
        Retrieve an assignment submission by its identifier.

        This helper method fetches a submission entity from the repository
        without raising an exception if the submission does not exist.

        Parameters
        ----------
        id : int
            Unique identifier of the assignment submission.

        Returns
        -------
        Optional[AssignmentSubmission]
            The submission if found, otherwise ``None``.

        Example
        -------
        ```python
        submission = await service._get_assignment_submission(id=55)

        if submission is None:
            print("Submission not found")
        ```
        """
        return await self.repo.get(AssignmentSubmissionGetCore(id=id))

    async def _update_feedback(
        self, cmd: AssignmentSubmissionFeedbackUpdate
    ) -> AssignmentSubmission:
        """
        Update feedback for an already graded submission.

        Feedback can only be modified after the submission has been graded.
        Attempting to update feedback on an ungraded submission will raise
        an exception.

        Parameters
        ----------
        cmd : AssignmentSubmissionFeedbackUpdate
            Command containing the submission identifier and updated feedback.

        Returns
        -------
        AssignmentSubmission
            The updated submission entity.

        Raises
        ------
        AssignmentSubmissionNotFoundError
            If the submission does not exist.

        AssignmentSubmissionNotGraded
            If feedback is attempted on an ungraded submission.

        Example
        -------
        ```python
        updated = await service._update_feedback(
            AssignmentSubmissionFeedbackUpdate(
                id=12,
                feedback="Great work on the analysis section."
            )
        )
        ```
        """

        submission = await self._get_assignment_submission(id=cmd.id)
        if submission is None:
            raise AssignmentSubmissionNotFoundError(value=cmd.id)

        if submission.score is None:
            raise AssignmentSubmissionNotGraded(
                message="Cannot update feedback for an ungraded submission."
            )

        return self._require_entity(await self.repo.update(cmd))

    async def _verify_submission(
        self, cmd: AssignmentSubmissionVerify
    ) -> AssignmentSubmission:
        """
        Verify and grade a submission.

        This operation validates the submission state before assigning a score.
        The verification process ensures:

        - A submission exists
        - A media file is attached
        - The media file has been uploaded successfully
        - The submission has not already been graded
        - The score is within the allowed assignment range

        Once verified, the submission status is updated to ``GRADED``.

        Parameters
        ----------
        cmd : AssignmentSubmissionVerify
            Command containing the submission identifier and assigned score.

        Returns
        -------
        AssignmentSubmission
            The verified and graded submission.

        Raises
        ------
        AssignmentSubmissionNotFoundError
            If the submission does not exist.

        AssignmentSubmissionMediaNotFoundError
            If the submission has no attached media.

        AssignmentSubmissionMediaNotUploadedError
            If the media file has not yet been uploaded.

        AssignmentSubmissionAlreadyVerified
            If the submission has already been graded.

        InvalidScoreError
            If the provided score exceeds the assignment's maximum score.

        Example
        -------
        ```python
        graded = await service._verify_submission(
            AssignmentSubmissionVerify(
                id=21,
                score=85
            )
        )
        ```
        """

        submission_context: Optional[
            AssignmentSubmissionContext
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

    async def create(
        self, cmd: AssignmentSubmissionCreate, connection: Optional[Connection] = None
    ) -> AssignmentSubmission:
        """
        Create a new assignment submission.

        This method validates the submission attempt against assignment rules,
        including maximum allowed attempts and assignment due date. The attempt
        number is automatically calculated based on previous submissions.

        Submission status is determined as:
        - ``SUBMITTED`` if within due date
        - ``DONE_LATE`` if submitted after due date

        Parameters
        ----------
        cmd : AssignmentSubmissionCreate
            Command containing submission details.

        connection : Optional[Connection]
            Optional database connection used when part of an existing transaction.

        Returns
        -------
        AssignmentSubmission
            The created submission entity.

        Raises
        ------
        AssignmentNotFoundError
            If the assignment does not exist.

        MaxAttemptsReachedError
            If the student has exceeded the maximum allowed attempts.

        Example
        -------
        ```python
        submission = await service.create(
            AssignmentSubmissionCreate(
                assignment_id=10,
                created_by=42
            )
        )
        ```
        """

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

        submission = await self.repo.add(
            AssignmentSubmissionCreateWithAttemptAndStatus(
                **cmd.model_dump(), attempt=total_attempt + 1, status=status
            ),
            connection,
        )

        if submission is not None:
            # Publish assignment submission created event
            await assignment_submission_created_publisher.publish(
                AssignmentSubmissionCreatedEvent(
                    id=submission.id,
                    assignment_id=submission.assignment_id,
                    created_by=submission.created_by,  # type: ignore
                )
            )

        return cast(AssignmentSubmission, submission)

    @require_authorization(
        action=Action.UPDATE,
        entity=Entity.ASSIGNMENT_SUBMISSION,
        user_id_field="updated_by",
        entity_id_field="id",
        object_name="cmd",
    )
    async def update(
        self, cmd: Union[AssignmentSubmissionVerify, AssignmentSubmissionFeedbackUpdate]
    ) -> AssignmentSubmission:
        """
        Update an assignment submission.

        This method delegates updates based on command type:

        - ``AssignmentSubmissionVerify`` → verifies and grades the submission
        - ``AssignmentSubmissionFeedbackUpdate`` → updates instructor feedback

        Authorization checks are enforced via the ``require_authorization`` decorator.

        Parameters
        ----------
        cmd : Union[AssignmentSubmissionVerify, AssignmentSubmissionFeedbackUpdate]
            Command representing the update operation.

        Returns
        -------
        AssignmentSubmission
            The updated submission entity.

        Example
        -------
        ```python
        graded = await service.update(
            AssignmentSubmissionVerify(
                id=15,
                score=90
            )
        )
        ```
        """

        if isinstance(cmd, AssignmentSubmissionVerify):
            return await self._verify_submission(cmd)
        return self._require_entity(await self._update_feedback(cmd))

    async def delete(self, cmd):
        # NOTE: This method is not implemented.
        return await self.repo.delete(cmd)

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT_SUBMISSION,
        user_id_field="viewer_id",
        entity_id_field="id",
        object_name="query",
    )
    async def get(self, query: AssignmentSubmissionGet):
        """
        Retrieve a submission by identifier.

        Authorization checks ensure the requesting user has permission
        to view the submission.

        Parameters
        ----------
        query : AssignmentSubmissionGet
            Query containing the submission identifier and viewer context.

        Returns
        -------
        AssignmentSubmission
            The requested submission.

        Raises
        ------
        AssignmentSubmissionNotFoundError
            If the submission does not exist.

        Example
        -------
        ```python
        submission = await service.get(
            AssignmentSubmissionGet(
                id=14,
                viewer_id=42
            )
        )
        ```
        """
        return self._require_entity(await self.repo.get(query), value=query.id)

    async def get_with_media(
        self, query: AssignmentSubmissionGet
    ) -> AssignmentSubmissionWithMedia:

        submission = await self.repo.get_with_media(query)

        if submission is None:
            raise AssignmentSubmissionNotFoundError(value=query.id)

        return submission

    async def create_with_attachment(
        self, cmd: AssignmentSubmissionCreate, file_cmd: FileMetadata
    ) -> AssignmentSubmissionUpload:
        """
        Create a submission and generate an upload URL for the submission file.

        This method performs the following workflow:

        1. Validates file size and MIME type.
        2. Performs authorization to ensure the user can submit.
        3. Creates the submission record.
        4. Creates a media record associated with the submission.
        5. Generates a secure upload URL for the submission file.

        The submission and media record creation are executed within a
        single database transaction to ensure consistency.

        Parameters
        ----------
        cmd : AssignmentSubmissionCreate
            Command containing submission details.

        file_cmd : FileMetadata
            Metadata describing the uploaded file.

        Returns
        -------
        AssignmentSubmissionUploadURL
            Object containing the submission ID and a pre-signed upload URL.

        Raises
        ------
        FileSizeExceededError
            If the uploaded file exceeds the allowed size limit.

        InvalidContentTypeError
            If the file type is not permitted.

        Example
        -------
        ```python
        result = await service.create_with_attachment(
            cmd=AssignmentSubmissionCreate(
                assignment_id=10,
                created_by=42
            ),
            file_cmd=FileMetadata(
                filename="solution.pdf",
                content_type="application/pdf",
                size=120000
            )
        )

        print(result.upload_url)
        ```
        """

        # Valid file check.
        if file_cmd.size > MAX_FILE_SIZE_FOR_ASSIGNMENT_SUBMISSION:
            raise FileSizeExceededError(
                max_size=MAX_FILE_SIZE_FOR_ASSIGNMENT_SUBMISSION
            )

        if file_cmd.content_type not in AllowedAssignmentSubmissionFileType:
            raise InvalidContentTypeError(
                content_type=file_cmd.content_type,
                allowed_types=AllowedAssignmentSubmissionFileType,
            )

        # Perform authorization.
        # NOTE: Used direct authorization check instead of decorator to avoid database transaction.
        # We don't want a db to wait to create transaction until the authorization check is done.
        # This is because creating transaction before auth check will lead to unnecessary db locks and performance issues.

        await self.auth_service.authorize(
            action=Action.CREATE,
            entity=Entity.ASSIGNMENT_SUBMISSION,
            user_id=cmd.created_by,
            parent_id=cmd.assignment_id,
        )

        async with self.repo.db.transaction() as conn:
            # Create the assignment record.
            submission = await self.create(cmd, conn)

            assignment = await self.assignment_repo.get(
                AssignmentGet(id=cmd.assignment_id)
            )

            if assignment is None:
                raise AssignmentNotFoundError(value=cmd.assignment_id)

            slugged_filename = slugify(file_cmd.filename)

            key = f"courses/C-{assignment.course_id}/assignments/A-{assignment.id}/submissions/{str(uuid4())}/{slugged_filename}"

            media = MediaCreate(
                filename=file_cmd.filename,
                mime_type=file_cmd.content_type,
                file_size=file_cmd.size,
                mediable_id=submission.id,
                mediable_type=MediableType.ASSIGNMENT_SUBMISSION,
                is_private=True,
                status=MediaStatus.PENDING,
                created_by=cmd.created_by,
                key=key,
            )
            media_id, url = await self.media_service.prepare_upload_url(
                media, expire_mins=120, connection=conn
            )

        return AssignmentSubmissionUpload(
            assignment_submission=AssignmentSubmissionDetail(**submission.model_dump()),
            media=MediaDetail(
                media_id=media_id,
                filename=file_cmd.filename,
                mime_type=file_cmd.content_type,
                upload_url=url,
            ),
        )
