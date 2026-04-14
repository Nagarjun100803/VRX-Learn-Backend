from src.events.broker import router
from src.events.dependencies import CacheInvalidatorServiceDependency
from src.events.events import (
    AssignmentCreatedEvent,
    AssignmentDeletedEvent,
    AssignmentSubmissionCreatedEvent,
    AssignmentUpdatedEvent,
    CourseCreatedEvent,
    CourseDeletedEvent,
    CourseUpdatedEvent,
    EnrollmentCreatedEvent,
    EnrollmentDeletedEvent,
    EnrollmentUpdatedEvent,
    LessonCreatedEvent,
    LessonDeletedEvent,
    LessonUpdatedEvent,
    ModuleCreatedEvent,
    ModuleDeletedEvent,
    ModuleUpdatedEvent,
    UserCreatedEvent,
    UserDeletedEvent,
)


# ── Subscribers ──────────────────────────────────────────────────────
#
# User
@router.subscriber("user.created")
async def handle_user_created(
    event: UserCreatedEvent, cache_invalidator: CacheInvalidatorServiceDependency
):
    await cache_invalidator.on_user_created(event)


@router.subscriber("user.deleted")
async def handle_user_deleted(
    event: UserDeletedEvent, cache_invalidator: CacheInvalidatorServiceDependency
):
    await cache_invalidator.on_user_deleted(event)


# Course
@router.subscriber("course.created")
async def handle_course_created(
    event: CourseCreatedEvent, cache_invalidator: CacheInvalidatorServiceDependency
):
    await cache_invalidator.on_course_created(event)


@router.subscriber("course.updated")
async def handle_course_updated(event: CourseUpdatedEvent): ...


@router.subscriber("course.deleted")
async def handle_course_deleted(
    event: CourseDeletedEvent, cache_invalidator: CacheInvalidatorServiceDependency
):
    await cache_invalidator.on_course_deleted(event)


# Module
@router.subscriber("module.created")
async def handle_module_created(
    event: ModuleCreatedEvent, cache_invalidator: CacheInvalidatorServiceDependency
):
    await cache_invalidator.on_module_created(event)


@router.subscriber("module.updated")
async def handle_module_updated(event: ModuleUpdatedEvent): ...


@router.subscriber("module.deleted")
async def handle_module_deleted(
    event: ModuleDeletedEvent, cache_invalidator: CacheInvalidatorServiceDependency
):
    await cache_invalidator.on_module_deleted(event)


# Lesson
@router.subscriber("lesson.created")
async def handle_lesson_created(
    event: LessonCreatedEvent, cache_invalidator: CacheInvalidatorServiceDependency
):
    await cache_invalidator.on_lesson_created(event)


@router.subscriber("lesson.updated")
async def handle_lesson_updated(event: LessonUpdatedEvent): ...


@router.subscriber("lesson.deleted")
async def handle_lesson_deleted(
    event: LessonDeletedEvent, cache_invalidator: CacheInvalidatorServiceDependency
):
    await cache_invalidator.on_lesson_deleted(event)


# Enrollment
@router.subscriber("enrollment.created")
async def handle_enrollment_created(
    event: EnrollmentCreatedEvent, cache_invalidator: CacheInvalidatorServiceDependency
):
    await cache_invalidator.on_enrollment_created(event)


@router.subscriber("enrollment.updated")
async def handle_enrollment_updated(event: EnrollmentUpdatedEvent): ...


@router.subscriber("enrollment.deleted")
async def handle_enrollment_deleted(
    event: EnrollmentDeletedEvent, cache_invalidator: CacheInvalidatorServiceDependency
):
    await cache_invalidator.on_enrollment_deleted(event)


@router.subscriber("assignment.created")
async def handle_assignment_created(
    event: AssignmentCreatedEvent, cache_invalidator: CacheInvalidatorServiceDependency
):
    await cache_invalidator.on_assignment_created(event)


@router.subscriber("assignment.updated")
async def handle_assignment_updated(event: AssignmentUpdatedEvent): ...


@router.subscriber("assignment.deleted")
async def handle_assignment_deleted(
    event: AssignmentDeletedEvent, cache_invalidator: CacheInvalidatorServiceDependency
):
    await cache_invalidator.on_assignment_deleted(event)


# Assignment Submission
@router.subscriber("assignment_submission.created")
async def handle_assignment_submission_created(
    event: AssignmentSubmissionCreatedEvent,
    cache_invalidator: CacheInvalidatorServiceDependency,
):
    await cache_invalidator.on_assignment_submission_created(event)
