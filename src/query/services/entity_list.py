from src.auth import Action, AuthService, Entity, require_authorization
from src.query.dto.entity_list import AssignmentDetail, AssignmentDetailWithDue, LessonDetail, ModuleDetail
from src.query.dto.request_schemas import CourseViewRequestSchema, ModuleViewRequestSchema
from src.query.repositories.entity_list import EntityListQueryRepository


class TraineeEntityListQueryService:
    
    def __init__(
        self,
        entity_list_query_repo: EntityListQueryRepository,
        auth_service: AuthService
    ) -> None:
        
        self.entity_list_query_repo = entity_list_query_repo
        self.auth_service = auth_service
        
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        parent_id_field="course_id",
        object_name="query"
    )
    async def list_assignments(self, query: CourseViewRequestSchema) -> list[AssignmentDetail]:
        assignments: list[AssignmentDetailWithDue] = await self.entity_list_query_repo.assignments(course_id=query.course_id)
        return [
            AssignmentDetail(id=assignment.id, title=assignment.title) 
            for assignment in assignments
        ]



class TrainerEntityListQueryService:
    
    def __init__(
        self,
        entity_list_query_repo: EntityListQueryRepository,
        auth_service: AuthService
    ) -> None:
        
        self.entity_list_query_repo = entity_list_query_repo
        self.auth_service = auth_service
        
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.MODULE,
        user_id_field="viewer_id",
        parent_id_field="course_id",
        object_name="query"
    )
    async def list_modules(self, query: CourseViewRequestSchema) -> list[ModuleDetail]:
        return await self.entity_list_query_repo.modules(course_id=query.course_id)
    
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.LESSON,
        user_id_field="viewer_id",
        parent_id_field="module_id",
        object_name="query"
    )
    async def list_lessons(self, query: ModuleViewRequestSchema) -> list[LessonDetail]:
        return await self.entity_list_query_repo.lessons(module_id=query.module_id)
    
    
    @require_authorization(
        action=Action.VIEW,
        entity=Entity.ASSIGNMENT,
        user_id_field="viewer_id",
        parent_id_field="course_id",
        object_name="query"
    )
    async def list_assignments(self, query: CourseViewRequestSchema) -> list[AssignmentDetailWithDue]:
        return await self.entity_list_query_repo.assignments(course_id=query.course_id)

