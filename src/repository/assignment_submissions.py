from typing import ClassVar, Optional, Union
from asyncpg import Connection, Record
from src.repository.base import BaseRepository
from src.commands.assignment_submissions import (
    AssignmentSubmissionContext, AssignmentSubmissionCreateWithAttemptAndStatus, AssignmentSubmissionFeedbackUpdate, AssignmentSubmissionGet, 
    AssignmentSubmission, AssignmentSubmissionGetCore, AssignmentSubmissionVerifyWithStatus
)
from src.commands.media import MediaStatus, MediableType



class AssignmentSubmissionRepository(BaseRepository[AssignmentSubmission]):
    
    tablename: ClassVar[str] = "assignment_submissions"

    
    def _to_domain(self, row: Optional[Record]) -> Optional[AssignmentSubmission]:
        if row is None: 
            return None
        return AssignmentSubmission(**row)
    
    
    async def add(
        self, 
        cmd: AssignmentSubmissionCreateWithAttemptAndStatus, 
        connection: Optional[Connection] = None
    ) -> AssignmentSubmission:
        return await super().add(cmd, connection)
    
    
    async def update(
        self, 
        cmd: Union[
            AssignmentSubmissionVerifyWithStatus,
            AssignmentSubmissionFeedbackUpdate
        ], 
        connection: Optional[Connection] = None
    ) -> Optional[AssignmentSubmission]:
        
        return await super().update(cmd, connection)
         
    
    async def delete(
        self, 
        cmd, 
        connection: Optional[Connection] = None
    ):
        raise NotImplementedError("Deleting assignment submissions is not implemented")
    
    
    async def get(
        self, 
        query: Union[
            AssignmentSubmissionGetCore, 
            AssignmentSubmissionGet
        ], 
        connection: Optional[Connection] = None
    ) -> Optional[AssignmentSubmission]:
        
        return await super().get(query, connection)
    
    
    async def count_attempts(
        self,
        user_id: int,
        assignment_id: int
    ) -> int:
        
        """
            Count the number of attempts a user has made for a specific assignment.
                - Only counts attempts that have an associated media asset with status "UPLOADED".
                - This ensures that only valid attempts (where the user has successfully uploaded a submission) are counted.
            
        """
        
        
        sql = """
            SELECT
                COUNT(*) as number_of_attempts
            FROM
                assignment_submissions AS s
            WHERE
                s.created_by = $1 AND 
                s.assignment_id = $2 AND
                s.deleted_at IS NULL AND
                EXISTS(
                    SELECT
                        1
                    FROM
                        media_assets AS m
                    WHERE
                        m.mediable_id = s.id AND
                        m.mediable_type = $3 AND
                        m.status = $4 AND
                        m.deleted_at IS NULL
                )
            ;
        """
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=( 
                user_id, 
                assignment_id,
                MediableType.ASSIGNMENT_SUBMISSION.value,
                MediaStatus.UPLOADED.value
            )
        )

        result = await self.db.execute(executable, fetch_returns="one")
        
        return result["number_of_attempts"]
        
    
        
    async def submission_context(
        self, 
        submission_id: int
    ) -> Optional[AssignmentSubmissionContext]:
        
        """
            Get submission with assignment and media context.
            
            Submission and assignment are required.
            Media is optional (upload might fail).
        """
        
        sql = """
            SELECT
                row_to_json(s.*)::jsonb AS submission,
                row_to_json(a.*)::jsonb AS assignment,
                row_to_json(m.*)::jsonb AS media
            FROM
                assignment_submissions AS s
            INNER JOIN
                assignments AS a
            ON
                a.id = s.assignment_id
            LEFT JOIN
                media_assets AS m
            ON
                m.mediable_id = s.id
                AND m.mediable_type = $1
            WHERE
                s.id = $2
                AND s.deleted_at IS NULL
        """
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(
                MediableType.ASSIGNMENT_SUBMISSION.value,
                submission_id
            )
        )
        
        result = await self.db.execute(executable, fetch_returns="one")
        
        if result is None:
            return None
        return AssignmentSubmissionContext(**result)
        
        
        