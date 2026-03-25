from typing import Optional

from src.query.dto.dashboards import AdminCourseCard, AdminKPI, AssignedCourse, CourseCard, TrainerKPI
from src.query.repositories import (
    TraineeDashboardQueryRepository, TrainerDashboardQueryRepository
)
from src.query.repositories.dashboards import AdminDashboardQueryRepository


class TraineeDashboardQueryService:
    
    def __init__(
        self,
        trainee_dashboard_query_repo: TraineeDashboardQueryRepository,
    ) -> None:
        self.trainee_dashboard_query_repo = trainee_dashboard_query_repo
        

    async def list_enrolled_courses(self, trainee_id: int) -> list[CourseCard]:
        return await self.trainee_dashboard_query_repo.enrolled_courses(trainee_id)

    
    async def list_top_new_courses(self, n: int) -> list[CourseCard]:
        return await self.trainee_dashboard_query_repo.top_new_courses(n)
    
    
    async def get_current_course(self, trainee_id: int) -> Optional[CourseCard]:
        return await self.trainee_dashboard_query_repo.current_course(trainee_id)
        
        
        
class TrainerDashboardQueryService:
    
    def __init__(
        self,
        trainer_dashboard_query_repo: TrainerDashboardQueryRepository
    ) -> None:
        self.trainer_dashboard_query_repo = trainer_dashboard_query_repo
        
    async def get_kpis(self, trainer_id: int) -> TrainerKPI:
        return await self.trainer_dashboard_query_repo.kpis(trainer_id)
    

    async def list_assigned_courses(self, trainer_id: int) -> list[AssignedCourse]:
        return await self.trainer_dashboard_query_repo.assigned_courses(trainer_id)



class AdminDashboardQueryService:
    
    def __init__(
        self, 
        admin_dashboard_query_repo: AdminDashboardQueryRepository
    ) -> None:
        self.admin_dashboard_query_repo = admin_dashboard_query_repo
        
    
    async def get_kpis(self) -> AdminKPI:
        return await self.admin_dashboard_query_repo.kpis()
        
        
    async def list_top_enrolled_courses(self, n: int) -> list[AdminCourseCard]:
        return await self.admin_dashboard_query_repo.top_enrolled_courses(n)
    