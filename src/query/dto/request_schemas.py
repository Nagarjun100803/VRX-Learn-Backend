from src.command.commands.base import AssignmentID, AssignmentSubmissionID, CourseID, LessonID, ModuleID, UserID
from src.query.dto.base import BaseDTO


class CourseViewRequestSchema(BaseDTO):
    """Request schema for viewing course related content."""
    course_id: CourseID
    viewer_id: UserID
    
    
class ModuleViewRequestSchema(BaseDTO):
    """Request schema for viewing module related content."""
    module_id: ModuleID
    viewer_id: UserID
    
    
class LessonViewRequestSchema(BaseDTO):
    """Request schema for viewing lesson related content."""
    lesson_id: LessonID
    viewer_id: UserID
    
    

class AssignmentViewRequestSchema(BaseDTO):
    """Request schema for viewing assignment related content."""
    assignment_id: AssignmentID
    viewer_id: UserID
    
    

class AssignmentSubmissionViewRequestSchema(BaseDTO):
    """Request schema for viewing assignment submission related content."""
    assignment_submission_id: AssignmentSubmissionID
    viewer_id: UserID
    
