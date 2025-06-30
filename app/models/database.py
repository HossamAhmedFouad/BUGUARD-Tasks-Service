from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from .enums import TaskStatus, TaskPriority


class Task(SQLModel, table=True):
    """Database model for Task"""
    __tablename__ = "tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200, index=True)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: TaskStatus = Field(default=TaskStatus.pending, index=True)
    priority: TaskPriority = Field(default=TaskPriority.medium, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: Optional[datetime] = Field(default=None)
    due_date: Optional[datetime] = Field(default=None, index=True)
    assigned_to: Optional[str] = Field(default=None, max_length=100, index=True) 