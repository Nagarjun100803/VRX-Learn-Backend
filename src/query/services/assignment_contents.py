from src.auth import Action, AuthService, Entity, require_authorization
from src.query.dto.assignment_contents import AssignmentSubmissionFilters, TraineeAssignmentContent, TraineeAssignmentCore, TrainerAssignmentContent, TrainerAssignmentCore, TrainerSubmissionDetail
from src.query.dto.base import PageMeta, Paginated
from src.query.dto.request_schemas import AssignmentViewRequestSchema, CourseViewRequestSchema
from src.query.repositories.assignment_contents import TraineeAssignmentContentQueryRepository, TrainerAssignmentContentQueryRepository


class TraineeAssignmentContentQueryService:
    
    def __init__(
        self,
        trainee_assignment_query_repo: TraineeAssignmentContentQueryRepository,
        auth_service: AuthService
    ) -> None:
        self.trainee_assignment_query_repo = trainee_assignment_query_repo
        self.auth_service = auth_service
        
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        parent_id_field="course_id",
        object_name="query"
    )
    async def list_assignments(self, query: CourseViewRequestSchema) -> list[TraineeAssignmentCore]:
        return await self.trainee_assignment_query_repo.assignments(course_id=query.course_id, trainee_id=query.viewer_id)
    
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        entity_id_field="assignment_id",
        object_name="query"
    )
    async def get_assignment_contents(self, query: AssignmentViewRequestSchema) -> TraineeAssignmentContent:
        return await self.trainee_assignment_query_repo.assignment_contents(assignment_id=query.assignment_id, trainee_id=query.viewer_id)
    

class TrainerAssignmentContentQueryService:
    
    def __init__(
        self,
        trainer_assignment_content_repo: TrainerAssignmentContentQueryRepository,
        auth_service: AuthService
    ) -> None:
        self.trainer_assignment_content_repo = trainer_assignment_content_repo
        self.auth_service = auth_service
        

    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        parent_id_field="course_id",
        object_name="query"
    )
    async def list_assignments(self, query: CourseViewRequestSchema) -> list[TrainerAssignmentCore]:
        return await self.trainer_assignment_content_repo.assignments(course_id=query.course_id)    
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        entity_id_field="assignment_id",
        object_name="query"
    )
    async def get_assignment_contents(self, query: AssignmentViewRequestSchema) -> TrainerAssignmentContent:
        return await self.trainer_assignment_content_repo.assignment_contents(assignment_id=query.assignment_id)
    
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT_SUBMISSION,
        user_id_field="viewer_id",
        parent_id_field="assignment_id",
        object_name="query"
    )
    async def list_submissions(
        self, 
        query: AssignmentViewRequestSchema,
        filters: AssignmentSubmissionFilters,
        page_meta: PageMeta 
    ) -> Paginated[TrainerSubmissionDetail]:
        
        return await self.trainer_assignment_content_repo.submissions(
            assignment_id=query.assignment_id,
            filters=filters,
            page_meta=page_meta
        )
