from src.events.broker import router

# ── Publishers ───────────────────────────────────────────────────────

# User
user_created_publisher = router.publisher("user.created")
user_deleted_publisher = router.publisher("user.deleted")

# Course
course_created_publisher = router.publisher("course.created")
course_updated_publisher = router.publisher("course.updated")
course_deleted_publisher = router.publisher("course.deleted")

# Module
module_created_publisher = router.publisher("module.created")
module_updated_publisher = router.publisher("module.updated")
module_reordered_publisher = router.publisher("module.reordered")
module_deleted_publisher = router.publisher("module.deleted")

# Lesson
lesson_created_publisher = router.publisher("lesson.created")
lesson_updated_publisher = router.publisher("lesson.updated")
lesson_reordered_publisher = router.publisher("lesson.reordered")
lesson_deleted_publisher = router.publisher("lesson.deleted")

# Enrollment
enrollment_created_publisher = router.publisher("enrollment.created")
enrollment_updated_publisher = router.publisher("enrollment.updated")
enrollment_deleted_publisher = router.publisher("enrollment.deleted")

# Assignment
assignment_created_publisher = router.publisher("assignment.created")
assignment_updated_publisher = router.publisher("assignment.updated")
assignment_deleted_publisher = router.publisher("assignment.deleted")

# Assignment Submission
assignment_submission_created_publisher = router.publisher(
    "assignment_submission.created"
)
assignment_submission_updated_publisher = router.publisher(
    "assignment_submission.updated"
)
assignment_submission_deleted_publisher = router.publisher(
    "assignment_submission.deleted"
)
