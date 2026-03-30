from pypika import Criterion, Parameter, PostgreSQLQuery, Table, functions as fn
from pypika.enums import SqlTypes
from pypika.terms import ValueWrapper

from src.command.commands.media import MediaStatus, MediableType
from src.pypika_query_builder import (
    CustomOrder, assignment_table, 
    assignment_submission_table, course_table, 
    enrollment_table, lesson_table, module_table,
    media_asset_table, user_table
)
from src.query.dto.base import PageMeta, Paginated, get_sort_order
from src.query.dto.entity_list import (
    AssignmentDetailWithDue, 
    AssignmentSubmissionDetail, AssignmentSubmissionFilters, 
    CourseDetail, CourseFilters, EnrollmentDetail, 
    EnrollmentFilters, LessonDetail, ModuleDetail, 
    TraineeDetail, TraineeFilters, UserDetail, UserFilters
)
from src.query.repositories.base import BaseQueryRepository, map_to_dto
from src.query.repositories.paginate import PaginatorMixin



class EntityListQueryRepository(BaseQueryRepository, PaginatorMixin):
    
    @map_to_dto(dto=ModuleDetail, dto_mode="list")
    async def modules(self, course_id: int) -> list[ModuleDetail]:
        
        sql = PostgreSQLQuery\
            .from_(module_table)\
            .where(
                Criterion.all(
                    terms=[
                        module_table.course_id == Parameter("$1"),
                        module_table.deleted_at.isnull()
                    ]
                )
            ).orderby(
                module_table.position_string
            ).select(
                module_table.id,
                module_table.title
            ).get_sql()
        
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(course_id, )
        )
        
        return await self.db.execute(executable, fetch_returns="all")
    
    
    @map_to_dto(dto=LessonDetail, dto_mode="list")
    async def lessons(self, module_id: int) -> list[LessonDetail]:
        
        sql = PostgreSQLQuery\
            .from_(lesson_table)\
            .join(media_asset_table)\
            .on(
                Criterion.all(
                    terms=[
                        media_asset_table.mediable_id == lesson_table.id,
                        media_asset_table.mediable_type == Parameter("$1"),
                        media_asset_table.status == Parameter("$2")    
                    ]
                )
            ).where(
                Criterion.all(
                    terms=[
                        lesson_table.module_id == Parameter("$3"),
                        lesson_table.deleted_at.isnull()
                    ]
                )
            ).orderby(
                lesson_table.position_string
            ).select(
                lesson_table.id,
                lesson_table.title,
                media_asset_table.id.as_("media_id"),
                media_asset_table.mime_type
            ).get_sql()    
    
        executable = self.db.query_builder.build_executable(
            sql=sql, values=(
                MediableType.LESSON,
                MediaStatus.UPLOADED,
                module_id
            )
        )
        
        return await self.db.execute(executable, fetch_returns="all")
        
    
    @map_to_dto(dto=AssignmentDetailWithDue, dto_mode="list")
    async def assignments(self, course_id: int) -> list[AssignmentDetailWithDue]:
        
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
            sql=sql, values=(course_id, )
        )
        
        return await self.db.execute(executable, fetch_returns="all")


    async def trainees(
        self, 
        course_id: int,
        filters: TraineeFilters,
        page_meta: PageMeta
    ) -> Paginated[TraineeDetail]:
        
        sql = PostgreSQLQuery\
            .from_(course_table)\
            .join(enrollment_table)\
            .on(course_table.id == enrollment_table.course_id)\
            .join(user_table)\
            .on(user_table.id == enrollment_table.user_id)\
            .where(
                Criterion.all(
                    terms=[
                        course_table.id == Parameter("$1"),
                        course_table.deleted_at.isnull(),
                        enrollment_table.deleted_at.isnull()
                    ]
                )
            ).select(
                user_table.id.as_("trainee_id"),
                user_table.username.as_("name"),
                user_table.email.as_("email"),
                user_table.role.as_("role"),
                fn.Cast(
                    enrollment_table.created_at,
                    SqlTypes.DATE
                ).as_("enrollment_date")
            )
            
        if filters.name:
            sql = sql.where(user_table.username.like(f"{filters.name}%"))
        
        else:
            
            if filters.sort_by_enrollment_date:
                sql = sql.orderby(enrollment_table.created_at, order=get_sort_order(filters.sort_by_enrollment_date))
            
            elif filters.sort_by_username:
                sql = sql.orderby(user_table.username, order=get_sort_order(filters.sort_by_username)) 
        
        
        return await self.paginate_query(
            sql=sql,
            values=(course_id, ),
            dto_class=TraineeDetail,
            page_meta=page_meta
        )


    async def users(
        self,
        filters: UserFilters,
        page_meta: PageMeta
    ) -> Paginated[UserDetail]:
        
        sql = PostgreSQLQuery\
            .from_(user_table)\
            .select(
                user_table.id,
                user_table.username.as_("name"),
                user_table.email,
                user_table.role,
                user_table.last_login,
                user_table.created_at,
                # Need to add user status here.
            )
        
        if filters.name_or_email:
            sql = sql.where(
                Criterion.any(
                    terms=[
                        user_table.username.like(f"{filters.name_or_email}%"),
                        user_table.email.like(f"{filters.name_or_email}%")
                    ]
                )
            ).orderby(user_table.username, order=CustomOrder.asc_nulls_last)
            
        
        else:
            
            # Add role check. 
            if filters.role:
                sql = sql.where(user_table.role == filters.role)
            
            # Add Sort Order
            if filters.sort_by_created_at:
                sql = sql.orderby(user_table.created_at, order=get_sort_order(filters.sort_by_created_at))
            
            elif filters.sort_by_username:
                sql = sql.orderby(user_table.username, order=get_sort_order(filters.sort_by_username))
        
        return await self.paginate_query(
            sql=sql,
            values=tuple(),
            dto_class=UserDetail,
            page_meta=page_meta
        )


    async def enrollments(
        self,
        filters: EnrollmentFilters,
        page_meta: PageMeta
    ) -> Paginated[EnrollmentDetail]:
    
        sql = PostgreSQLQuery\
            .from_(enrollment_table)\
            .join(course_table)\
            .on(enrollment_table.course_id == course_table.id)\
            .join(user_table)\
            .on(enrollment_table.user_id == user_table.id)\
            .select(
                enrollment_table.id,
                user_table.username.as_("name"),
                user_table.email,
                user_table.role,
                course_table.title.as_("course_name"),
                enrollment_table.status.as_("status"),
                fn.Cast(
                    enrollment_table.created_at,
                    SqlTypes.DATE
                ).as_("enrollment_date")
            )
            
        if filters.name_or_email:
            sql = sql.where(
                Criterion.any(
                    terms=[
                        user_table.username.like(f"{filters.name_or_email}%"),
                        user_table.email.like(f"{filters.name_or_email}%"),
                    ]
                )
            ).orderby(user_table.username, order=CustomOrder.asc_nulls_last)
       
        else:
            # Add role and status filters.
            if filters.role:
                sql = sql.where(user_table.role == filters.role)
            if filters.status:
                sql = sql.where(enrollment_table.status == filters.status)
                
            # Add sort order.
            if filters.sort_by_enrollment_date:
                sql = sql.orderby(enrollment_table.created_at, order=get_sort_order(filters.sort_by_enrollment_date))
            
            elif filters.sort_by_course_name:
                sql = sql.orderby(course_table.title, order=get_sort_order(filters.sort_by_course_name))

        
        return await self.paginate_query(
            sql=sql,
            values=tuple(),
            dto_class=EnrollmentDetail,
            page_meta=page_meta
        )
        

    async def courses(
        self,
        filters: CourseFilters,
        page_meta: PageMeta
    ) -> Paginated[CourseDetail]:
        
        trainee_count_query = PostgreSQLQuery\
            .from_(enrollment_table)\
            .groupby(enrollment_table.course_id)\
            .select(
                enrollment_table.course_id, # Used to join.
                fn.Count(enrollment_table.user_id).as_("no_of_trainees")
            )
        
        trainee_count_cte = Table("trainee_count_cte") # reference table.
        
        sql = PostgreSQLQuery\
            .with_(trainee_count_query, trainee_count_cte._table_name)\
            .from_(course_table)\
            .join(user_table)\
            .on(course_table.trainer_id == user_table.id)\
            .left_join(trainee_count_cte)\
            .on(trainee_count_cte.course_id == course_table.id)\
            .select(
                course_table.id,
                course_table.title,
                course_table.short_description,
                user_table.username.as_("trainer_name"),
                fn.Cast(course_table.created_at, SqlTypes.DATE).as_("created_at"),
                fn.Coalesce(
                    trainee_count_cte.no_of_trainees,
                    ValueWrapper(0)
                ).as_("no_of_trainees")
            )
            
        if filters.course_name_or_trainer_name:
            sql = sql.where(
                Criterion.any(
                    terms=[
                        # Course title is stored in Upper case letters.
                        course_table.title.ilike(f"{filters.course_name_or_trainer_name}%"),
                        user_table.username.ilike(f"{filters.course_name_or_trainer_name}%")
                    ]
                )
            )
            
        else:
            # Add sort order
            if filters.sort_by_no_of_trainees:
                sql = sql.orderby(trainee_count_cte.no_of_trainees, order=get_sort_order(filters.sort_by_no_of_trainees))
            
            elif filters.sort_by_created_at:
                sql = sql.orderby(course_table.created_at, order=get_sort_order(filters.sort_by_created_at))
        
            elif filters.sort_by_course_name:
                sql = sql.orderby(course_table.title, order=get_sort_order(filters.sort_by_course_name))     
        
        
        return await self.paginate_query(
            sql=sql,
            values=tuple(),
            dto_class=CourseDetail,
            page_meta=page_meta
        )


    async def assignment_submissions(
        self, 
        assignment_id: int,
        filters: AssignmentSubmissionFilters,
        page_meta: PageMeta
    ) -> Paginated[AssignmentSubmissionDetail]:
        
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
            sql = sql.orderby(assignment_submission_table.score, order=get_sort_order(filters.sort_by_grade))
        
        return await self.paginate_query(
            sql=sql,
            values=(
                MediableType.ASSIGNMENT_SUBMISSION,
                MediaStatus.UPLOADED,
                assignment_id
            ),
            dto_class=AssignmentSubmissionDetail,
            page_meta=page_meta
        )
