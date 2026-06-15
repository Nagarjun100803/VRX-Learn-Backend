import asyncio

from src.command.commands.enrollments import EnrollmentCreate
from src.command.services.enrollments import EnrollmentService
from src.settings import settings

# TODO: Later need to move this file into dedicated module for e.g workflows.


class UserOnboardService:
    def __init__(self, enrollment_service: EnrollmentService):
        self.enrollment_service = enrollment_service

    async def onboard_user(self, user_id: int) -> None:
        """
        Onboards a user by creating enrollments for the free courses.
        """
        try:
            free_course_ids = settings.free_course.ids
            enrollment_create_tasks = [
                self.enrollment_service.create(
                    EnrollmentCreate(
                        user_id=user_id,
                        course_id=course_id,
                        expire_at=settings.free_course.expires_at,
                        created_by=user_id,  # self-enrollment.
                    )
                )
                for course_id in free_course_ids
            ]
            await asyncio.gather(*enrollment_create_tasks)

        except Exception as e:
            print(f"Error onboarding user: {e}")
