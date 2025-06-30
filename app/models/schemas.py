from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from .enums import TaskStatus, TaskPriority


class SortOrder(str, Enum):
    """Sort order enumeration"""
    asc = "asc"
    desc = "desc"


class SortField(str, Enum):
    """Fields available for sorting"""
    id = "id"
    title = "title"
    status = "status"
    priority = "priority"
    created_at = "created_at"
    updated_at = "updated_at"
    due_date = "due_date"
    assigned_to = "assigned_to"


class TaskBase(BaseModel):
    """Base task schema with common fields"""
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    status: TaskStatus = Field(default=TaskStatus.pending, description="Task status")
    priority: TaskPriority = Field(default=TaskPriority.medium, description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task deadline")
    assigned_to: Optional[str] = Field(None, max_length=100, description="Assignee name")


class TaskCreate(TaskBase):
    """Schema for creating a new task"""
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v <= datetime.utcnow():
            raise ValueError('Due date must be in the future')
        return v


class TaskUpdate(BaseModel):
    """Schema for updating an existing task"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    priority: Optional[TaskPriority] = Field(None, description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task deadline")
    assigned_to: Optional[str] = Field(None, max_length=100, description="Assignee name")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip() if v else v

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v <= datetime.utcnow():
            raise ValueError('Due date must be in the future')
        return v


class BulkTaskUpdate(BaseModel):
    """Schema for bulk updating tasks"""
    task_ids: List[int] = Field(..., min_length=1, description="List of task IDs to update")
    update_data: TaskUpdate = Field(..., description="Data to update for all selected tasks")


class BulkTaskDelete(BaseModel):
    """Schema for bulk deleting tasks"""
    task_ids: List[int] = Field(..., min_length=1, description="List of task IDs to delete")


class TaskResponse(BaseModel):
    """Schema for task API responses"""
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: Optional[datetime]
    due_date: Optional[datetime]
    assigned_to: Optional[str]

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Schema for paginated task list responses"""
    tasks: list[TaskResponse]
    total: int
    skip: int
    limit: int
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation responses"""
    success: bool
    affected_count: int
    message: str
    task_ids: List[int]


class APIInfo(BaseModel):
    """Schema for API information"""
    title: str
    version: str
    description: str
    endpoints: Dict[str, str]


class HealthCheck(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    version: str


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str
    errors: Optional[list[Dict[str, Any]]] = None 