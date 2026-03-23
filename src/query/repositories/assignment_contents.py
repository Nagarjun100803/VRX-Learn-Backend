import asyncio
from typing import Optional

from pypika import Case, Criterion, Parameter, PostgreSQLQuery, Table, functions as fn
from pypika.enums import SqlTypes
from pypika.terms import ExistsCriterion, ValueWrapper

from src.pypika_query_builder import (
    JsonbAgg, JsonbBuildObject, 
    assignment_table, assignment_submission_table, 
    media_asset_table, user_table
)
from src.command.commands.media import MediaStatus, MediableType
from src.query.dto.assignment_contents import (
    AssignmentSubmissionFilters, TraineeAssignmentContent, 
    TraineeAssignmentCore, TrainerAssignmentContent, 
    TrainerAssignmentCore, TrainerSubmissionDetail
)
from src.query.dto.base import PageMeta, Paginated
from src.query.repositories.base import BaseQueryRepository, map_to_dto



class TraineeAssignmentContentQueryRepository(BaseQueryRepository):
        
    @map_to_dto(dto=TraineeAssignmentCore, dto_mode="list")
    async def assignments(self, course_id: int, trainee_id: int) -> list[TraineeAssignmentCore]:
        
        submissions_query = PostgreSQLQuery\
            .from_(assignment_submission_table)\
            .join(media_asset_table)\
            .on(
                Criterion.all(
                    terms=[
                        assignment_submission_table.id == media_asset_table.mediable_id,
                        media_asset_table.mediable_type == Parameter("$1"),
                        media_asset_table.status == Parameter("$2")
                    ]
                )
            ).where(
                Criterion.all(
                    terms=[
                        assignment_submission_table.created_by == Parameter("$3"),
                        assignment_submission_table.deleted_at.isnull()
                    ]
                )
            ).select(assignment_submission_table.assignment_id) # Used inn where clause of a case statement.
        
        submission_cte = Table("submission_cte") # Reference table
        
        sql = PostgreSQLQuery\
            .with_(submissions_query, submission_cte._table_name)\
            .from_(assignment_table)\
            .where(
                Criterion.all(
                    terms=[
                        assignment_table.course_id == Parameter("$4"),
                        assignment_table.deleted_at.isnull()
                    ]
                )
            ).orderby(
                assignment_table.due_date
            ).select(
                assignment_table.id,
                assignment_table.title,

                Case().when(
                    ExistsCriterion(
                        PostgreSQLQuery\
                            .from_(submission_cte)\
                            .where(submission_cte.assignment_id == assignment_table.id)\
                            .select(ValueWrapper(1))
                    ),
                    ValueWrapper(True)
                ).else_(ValueWrapper(False)).as_("is_completed")
            ).get_sql()


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
        
        submissions_query = PostgreSQLQuery\
            .from_(assignment_submission_table)\
            .join(media_asset_table)\
            .on(
                Criterion.all(
                    terms=[
                        assignment_submission_table.id == media_asset_table.mediable_id,
                        media_asset_table.mediable_type == Parameter("$1"),
                        media_asset_table.status == Parameter("$2")
                    ]
                )
            ).where(
                Criterion.all(
                    terms=[
                        assignment_submission_table.created_by == Parameter("$3"),
                        assignment_submission_table.deleted_at.isnull(),
                        media_asset_table.deleted_at.isnull()
                    ]
                )
            ).select(
                assignment_submission_table.assignment_id, # For filtering inside of main query.,
                assignment_submission_table.created_at, # For ordering,
                JsonbBuildObject(
                    "id", assignment_submission_table.id,
                    "filename", media_asset_table.filename,
                    "score", assignment_submission_table.score,
                    "status", assignment_submission_table.status,
                    "attempt", assignment_submission_table.attempt,
                    "submitted_at", assignment_submission_table.created_at,
                    "media_id", media_asset_table.id
                ).as_("submission")
            )
            
        submission_cte = Table("submission_cte") # Reference table
        
        sql = PostgreSQLQuery\
            .with_(submissions_query, submission_cte._table_name)\
            .from_(assignment_table)\
            .left_join(media_asset_table)\
            .on(
                Criterion.all(
                    terms=[
                        assignment_table.id == media_asset_table.mediable_id,
                        media_asset_table.mediable_type == Parameter("$4"),
                        media_asset_table.status == Parameter("$5")
                    ]
                )
            ).where(
                Criterion.all(
                    terms=[
                        assignment_table.id == Parameter("$6"),
                        assignment_table.deleted_at.isnull(),
                        media_asset_table.deleted_at.isnull()
                    ]
                )
            ).select(
                
                JsonbBuildObject(
                    'id', assignment_table.id,
                    'title', assignment_table.title,
                    'max_score', assignment_table.max_score,
                    'max_attempts', assignment_table.number_of_attempts,
                    'due_date', assignment_table.due_date,
                    'instructions', assignment_table.instructions
                ).as_("assignment"),
                
                Case().when(
                    media_asset_table.id.isnotnull(),
                        JsonbBuildObject(
                            "media_id", media_asset_table.id,
                            "filename", media_asset_table.filename
                        )
                ).else_(ValueWrapper(None)).as_("attachment"),
                
                PostgreSQLQuery\
                    .from_(submission_cte)\
                    .where(submission_cte.assignment_id == assignment_table.id)\
                    .select(
                        fn.Coalesce(
                            JsonbAgg(submission_cte.submission)\
                                .filter(submission_cte.submission.isnotnull())\
                                .orderby(submission_cte.created_at),
                                
                                ValueWrapper("[]")
                            ).as_("submissions")
                )  
            ).get_sql()
            
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(
                MediableType.ASSIGNMENT_SUBMISSION,
                MediaStatus.UPLOADED,
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
        
        sql = PostgreSQLQuery\
            .from_(assignment_table)\
            .where(
                Criterion.all(
                    terms=[
                        assignment_table.course_id == Parameter("$1"),
                        assignment_table.deleted_at.isnull()
                    ]
                )
            ).orderby(
                assignment_table.due_date
            ).select(
                assignment_table.id,
                assignment_table.title,
                assignment_table.due_date
            ).get_sql()
 
        executable = self.db.query_builder.build_executable(
            sql, values=(course_id, )
        )
        
        return await self.db.execute(executable, fetch_returns="all")
        
    
    @map_to_dto(dto=TrainerAssignmentContent, dto_mode="single")
    async def assignment_contents(self, assignment_id: int) -> Optional[TrainerAssignmentContent]:
        
        sql = PostgreSQLQuery\
            .from_(assignment_table)\
            .left_join(media_asset_table)\
            .on(
                Criterion.all(
                    terms=[
                        assignment_table.id == media_asset_table.mediable_id,
                        media_asset_table.mediable_type == Parameter("$1"),
                        media_asset_table.status == Parameter("$2")
                    ]
                )
            ).where(
                Criterion.all(
                    terms=[
                        assignment_table.id == Parameter("$3"),
                        assignment_table.deleted_at.isnull(),
                        media_asset_table.deleted_at.isnull()
                    ]
                )
            ).select(
                JsonbBuildObject(
                    'id', assignment_table.id,
                    'title', assignment_table.title,
                    'max_score', assignment_table.max_score,
                    'max_attempts', assignment_table.number_of_attempts,
                    'due_date', assignment_table.due_date,
                    'instructions', assignment_table.instructions
                ).as_("assignment"),
                
                Case().when(
                    media_asset_table.id.isnotnull(),
                    JsonbBuildObject(
                        "media_id", media_asset_table.id,
                        "filename", media_asset_table.filename
                    )
                ).else_(ValueWrapper(None)).as_("attachment")
            ).get_sql()
           
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(
                MediableType.ASSIGNMENT,
                MediaStatus.UPLOADED,
                assignment_id
            )
        )
        
        return await self.db.execute(executable, fetch_returns="one")


    async def submissions(
        self, 
        assignment_id: int,
        filters: AssignmentSubmissionFilters,
        page_meta: PageMeta
    ) -> Paginated[TrainerSubmissionDetail]:
        
        sql = PostgreSQLQuery\
            .from_(assignment_submission_table)\
            .join(media_asset_table)\
            .on(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_id == assignment_submission_table.id,
                        media_asset_table.mediable_type == Parameter("$1"),
                        media_asset_table.status == Parameter("$2")
                    ]
                )
            ).join(user_table)\
            .on(user_table.id == assignment_submission_table.created_by)\
            .join(assignment_table)\
            .on(assignment_submission_table.assignment_id == assignment_table.id)\
            .select(
                assignment_submission_table.id,
                user_table.username,
                user_table.email,
                assignment_submission_table.attempt,
                assignment_table.number_of_attempts.as_("max_attempt"),
                assignment_submission_table.status,
                assignment_submission_table.score,
                assignment_table.max_score,
                assignment_submission_table.created_at.as_("submitted_at")
            ).where(
                Criterion.all(
                    terms=[
                        assignment_table.id == Parameter("$3"),
                        assignment_table.deleted_at.isnull(),
                        media_asset_table.deleted_at.isnull(),
                        assignment_submission_table.deleted_at.isnull()
                    ]
                )
            )
            
        # Add filter for the date range.
        if filters.from_date:
            sql = sql.where(fn.Cast(assignment_submission_table.created_at, SqlTypes.DATE).between(lower=filters.from_date, upper=filters.to_date))
        else:
            sql = sql.where(fn.Cast(assignment_submission_table.created_at, SqlTypes.DATE) <= filters.to_date)

        if filters.status:
            sql = sql.where(assignment_submission_table.status == filters.status)
        
        # Sort by grading
        if filters.sort_by_grade:
            sql = sql.orderby(assignment_submission_table.score, order=filters.order)
         
        
        count_sql = PostgreSQLQuery\
            .from_(sql)\
            .select(fn.Count("*").as_("total"))
        

        # Add a limit and offset to main sql.
        sql= sql.offset(page_meta.offset).limit(page_meta.limit)

        executable = self.db.query_builder.build_executable(
            sql=sql.get_sql(), 
            values=(
                MediableType.ASSIGNMENT_SUBMISSION, 
                MediaStatus.UPLOADED,
                assignment_id
            )
        )
        
        count_executable = self.db.query_builder.build_executable(
            sql=count_sql.get_sql(),
            values=(
                MediableType.ASSIGNMENT_SUBMISSION, 
                MediaStatus.UPLOADED,
                assignment_id
            )
        )
        
        assignment_submissions, count_of_assignment_submissions = await asyncio.gather(
            self.db.execute(executable, fetch_returns="all"),
            self.db.execute(count_executable, fetch_returns="one")
        )
        
        assignment_submissions = [
            TrainerSubmissionDetail.model_validate(
                dict(assignment_submission)
            ) 
            for assignment_submission in assignment_submissions
        ]
        
        return Paginated[TrainerSubmissionDetail](
            data=assignment_submissions,
            page=page_meta.page,
            limit=page_meta.limit,
            total_items=count_of_assignment_submissions["total"]
        )
