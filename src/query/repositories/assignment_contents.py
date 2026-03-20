from typing import Optional

import sqlparse

from src.command.commands.assignment_submissions import AssignmentSubmission, AssignmentSubmissionStatus
from src.command.commands.media import MediaStatus, MediableType
from src.query.dto.assignment_contents import AssignmentSubmissionFilters, TraineeAssignmentContent, TraineeAssignmentCore, TrainerAssignmentContent, TrainerAssignmentCore, TrainerSubmissionDetail
from src.query.repositories.base import BaseQueryRepository, PageMeta, map_to_dto



class TraineeAssignmentContentQueryRepository(BaseQueryRepository):
        
    @map_to_dto(dto=TraineeAssignmentCore, dto_mode="list")
    async def assignments(self, course_id: int, trainee_id: int) -> list[TraineeAssignmentCore]:
        
        sql = """
            WITH submissions_cte AS(
                SELECT
                    asub.assignment_id --used in where clause in a case statement.
                FROM
                    assignment_submissions as asub
                JOIN
                    media_assets AS me
                ON
                    me.mediable_id = asub.id AND
                    me.mediable_type = $1 AND
                    me.status = $2
                WHERE
                    asub.created_by = $3 AND
                    asub.deleted_at IS NULL
            )

            -- cte end.
            SELECT
                a.id,
                a.title,
                CASE 
                    WHEN EXISTS(
                        SELECT
                            1
                        FROM
                            submissions_cte AS subcte
                        WHERE
                            subcte.assignment_id = a.id
                    ) THEN true
                    ELSE false
                END AS is_completed
            FROM
                assignments AS a
            WHERE
                a.course_id = $4 AND
                a.deleted_at IS NULL
            ORDER BY
                a.due_date
        """
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(
                MediableType.ASSIGNMENT_SUBMISSION,
                MediaStatus.UPLOADED,
                trainee_id,
                course_id
            )
        )
        
        return await self.db.execute(executable, fetch_returns="all")
        
    
    @map_to_dto(dto=TraineeAssignmentContent, dto_mode="single")
    async def assignment_contents(self, assignment_id: int, trainee_id: int) -> Optional[TraineeAssignmentContent]:
        sql = """
            WITH submissions_cte AS(
                SELECT
                    asub.assignment_id, -- Used to join
                    asub.created_at, -- for ordering.
                    JSONB_BUILD_OBJECT(
                        'id', asub.id,
                        'filename',  me.filename,
                        'score', asub.score,
                        'status', asub.status,
                        'attempt', asub.attempt,
                        'submitted_at', asub.created_at,
                        'media_id', me.id
                    ) as submission
                FROM
                    assignment_submissions AS asub
                JOIN
                    media_assets as me
                ON
                    asub.id = me.mediable_id AND
                    me.mediable_type = $1
                WHERE
                    asub.deleted_at IS NULL AND
                    me.deleted_at IS NULL AND
                    asub.created_by = $2
            )

            --- cte end.
            SELECT
                JSONB_BUILD_OBJECT(
                    'id', a.id,
                    'title', a.title,
                    'max_score', a.max_score,
                    'max_attempts', a.number_of_attempts,
                    'due_date', a.due_date,
                    'instructions', a.instructions
                ) AS assignment,

                CASE 
                    WHEN me.id IS NOT NULL THEN
                        JSONB_BUILD_OBJECT(
                            'media_id', me.id,
                            'filename', me.filename
                        )
                    ELSE NULL
                END AS attachment,

                COALESCE(
                    (
                        SELECT
                            JSONB_AGG(subcte.submission ORDER BY subcte.created_at)
                        FROM
                            submissions_cte as subcte
                        WHERE
                            subcte.assignment_id = a.id
                    ), '[]'::jsonb
                ) AS submissions

            FROM
                assignments AS a
            LEFT JOIN
                media_assets AS me
            ON
                a.id = me.mediable_id AND
                me.mediable_type = $3 AND
                me.status = $4
            WHERE
                a.id = $5 AND
                a.deleted_at IS NULL AND
                me.deleted_at IS NULL
        """
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(
                MediableType.ASSIGNMENT_SUBMISSION,
                trainee_id,
                MediableType.ASSIGNMENT,
                MediaStatus.UPLOADED,
                assignment_id
            )
        )
        
        return await self.db.execute(executable, fetch_returns="one")


class TrainerAssignmentContentQueryRepository(BaseQueryRepository):
    
    @map_to_dto(dto=TrainerAssignmentCore, dto_mode="list")
    async def assignments(self, course_id: int) -> list[TrainerAssignmentCore]:
        sql = """
            SELECT
                a.id,
                a.title,
                a.due_date
            FROM
                assignments AS a
            WHERE
                a.course_id = $1 AND
                a.deleted_at IS NULL
            ORDER BY
                a.due_date
        """
        executable = self.db.query_builder.build_executable(
            sql, values=(course_id, )
        )
        
        return await self.db.execute(executable, fetch_returns="all")
        
    
    @map_to_dto(dto=TrainerAssignmentContent, dto_mode="single")
    async def assignment_contents(self, assignment_id: int) -> Optional[TrainerAssignmentContent]:
        sql = """
            SELECT
                JSONB_BUILD_OBJECT(
                    'id', a.id,
                    'title', a.title,
                    'max_score', a.max_score,
                    'max_attempts', a.number_of_attempts,
                    'due_date', a.due_date,
                    'instructions', a.instructions
                ) AS assignment,

                CASE 
                    WHEN me.id IS NOT NULL THEN
                        JSONB_BUILD_OBJECT(
                            'media_id', me.id,
                            'filename', me.filename
                        )
                    ELSE NULL
                END AS attachment
            FROM
                assignments AS a
            LEFT JOIN
                media_assets AS me
            ON
                a.id = me.mediable_id AND
                me.mediable_type = $1 AND
                me.status = $2
            WHERE
                a.id = $3 AND
                a.deleted_at IS NULL AND
                me.deleted_at IS NULL
        """
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(
                MediableType.ASSIGNMENT.value,
                MediaStatus.UPLOADED.value,
                assignment_id
            )
        )
        
        return await self.db.execute(executable, fetch_returns="one")


    @map_to_dto(dto=TrainerSubmissionDetail, dto_mode="list")
    async def submissions(
        self, 
        assignment_id: int,
        filters: AssignmentSubmissionFilters,
        page_meta: PageMeta
    ):
        
        sql = """
            SELECT
                asub.id AS id,
                u.username AS username,
                u.email AS email,
                asub.attempt AS attempt,
                a.number_of_attempts AS max_attempt,
                asub.status AS status,
                asub.score AS score,
                a.max_score AS max_score,
                asub.created_at AS submitted_at
            FROM
                assignment_submissions AS asub
            JOIN
                media_assets AS me
            ON
                me.mediable_id = asub.id AND
                me.mediable_type = $1 AND
                me.status = $2
            JOIN
                assignments AS a
            ON
                a.id = asub.assignment_id
            JOIN
                users AS u
            ON
                u.id = asub.created_by
        """
                
        fs = {
            "asub.assignment_id": assignment_id, 
            "asub.status": filters.status,
        }
        
        executable = self.db.query_builder.build_executable(
            sql=sql, 
            values=(
                MediableType.ASSIGNMENT_SUBMISSION, 
                MediaStatus.UPLOADED
            )
        ).where(filters=filters)
        
        if filters.sort_by_grade:
            order = "asub.score" if filters.sort_by_grade == "ASC" else "-asub.score"
            executable = executable.order_by(by=order)
        
        # Final limit offset.
        executable = executable.offset(page_meta.offset).limit(page_meta.limit)
        
        return await self.db.execute(executable, fetch_returns="all")
    
        
import asyncio
async def main() -> None:
    from src.dependencies import db
    
    await db.init_pool()
    
    r = TrainerAssignmentContentQueryRepository(db)
    
    res = await r.submissions(assignment_id=18)
    for r in res:
        print(r.model_dump_json(indent=4, by_alias=True))

    await db.close_pool()
    

if __name__ == "__main__":
    asyncio.run(main())
        
        
        
        