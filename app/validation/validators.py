from datetime import datetime
from typing import Optional
from app.models.enums import TaskStatus, TaskPriority


class TaskValidator:
    """Custom validators for task business logic"""
    
    @staticmethod
    def validate_title(title: str) -> str:
        """Validate and sanitize task title"""
        if not title or not title.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        
        sanitized_title = title.strip()
        if len(sanitized_title) > 200:
            raise ValueError('Title cannot exceed 200 characters')
        
        return sanitized_title
    
    @staticmethod
    def validate_description(description: Optional[str]) -> Optional[str]:
        """Validate and sanitize task description"""
        if description is None:
            return None
        
        if len(description) > 1000:
            raise ValueError('Description cannot exceed 1000 characters')
        
        return description.strip() if description else None
    
    @staticmethod
    def validate_due_date(due_date: Optional[datetime]) -> Optional[datetime]:
        """Validate due date is in the future"""
        if due_date and due_date <= datetime.utcnow():
            raise ValueError('Due date must be in the future')
        return due_date
    
    @staticmethod
    def validate_assigned_to(assigned_to: Optional[str]) -> Optional[str]:
        """Validate and sanitize assignee"""
        if assigned_to is None:
            return None
        
        sanitized = assigned_to.strip()
        if len(sanitized) > 100:
            raise ValueError('Assignee name cannot exceed 100 characters')
        
        return sanitized if sanitized else None
    
    @staticmethod
    def validate_status_transition(current_status: TaskStatus, new_status: TaskStatus) -> bool:
        """Validate if status transition is allowed"""
        # Define valid status transitions
        valid_transitions = {
            TaskStatus.pending: [TaskStatus.in_progress, TaskStatus.cancelled],
            TaskStatus.in_progress: [TaskStatus.completed, TaskStatus.cancelled, TaskStatus.pending],
            TaskStatus.completed: [TaskStatus.in_progress],  # Allow reopening completed tasks
            TaskStatus.cancelled: [TaskStatus.pending, TaskStatus.in_progress]  # Allow reactivating cancelled tasks
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    @staticmethod
    def validate_priority(priority: TaskPriority) -> TaskPriority:
        """Validate task priority"""
        if priority not in TaskPriority:
            raise ValueError(f'Invalid priority: {priority}')
        return priority 