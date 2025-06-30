from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import Optional
from datetime import datetime

from app.database.connection import get_session
from app.models.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    APIInfo, HealthCheck, BulkTaskUpdate, BulkTaskDelete, 
    BulkOperationResponse, SortField, SortOrder
)
from app.models.enums import TaskStatus, TaskPriority
from app.services.task_service import TaskService
from app.core.config import settings

router = APIRouter()


def get_task_service(session: Session = Depends(get_session)) -> TaskService:
    """Dependency to get task service instance"""
    return TaskService(session)


@router.get("/", response_model=APIInfo)
async def root():
    """Root endpoint - Return API information and available endpoints"""
    return APIInfo(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        endpoints={
            "GET /": "API information",
            "GET /health": "Health check",
            "GET /tasks/statistics": "Get task statistics",
            "POST /tasks": "Create a new task",
            "GET /tasks": "List all tasks with optional filtering, sorting and pagination",
            "GET /tasks/{task_id}": "Retrieve a specific task",
            "PUT /tasks/{task_id}": "Update an existing task",
            "DELETE /tasks/{task_id}": "Delete a task",
            "PUT /tasks/bulk": "Bulk update multiple tasks",
            "DELETE /tasks/bulk": "Bulk delete multiple tasks",
            "GET /tasks/status/{status}": "Get tasks by status",
            "GET /tasks/priority/{priority}": "Get tasks by priority"
        }
    )


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version
    )


@router.get("/tasks/statistics")
async def get_task_statistics(
    task_service: TaskService = Depends(get_task_service)
):
    """Get task statistics"""
    return task_service.get_task_statistics()


# IMPORTANT: Bulk routes must come before parameterized routes to avoid conflicts
@router.put("/tasks/bulk", response_model=BulkOperationResponse)
async def bulk_update_tasks(
    bulk_update: BulkTaskUpdate,
    task_service: TaskService = Depends(get_task_service)
):
    """Bulk update multiple tasks"""
    updated_count, task_ids = task_service.bulk_update_tasks(bulk_update)
    
    return BulkOperationResponse(
        success=True,
        affected_count=updated_count,
        message=f"Successfully updated {updated_count} tasks",
        task_ids=task_ids
    )


@router.delete("/tasks/bulk", response_model=BulkOperationResponse)
async def bulk_delete_tasks(
    bulk_delete: BulkTaskDelete,
    task_service: TaskService = Depends(get_task_service)
):
    """Bulk delete multiple tasks"""
    deleted_count, task_ids = task_service.bulk_delete_tasks(bulk_delete)
    
    return BulkOperationResponse(
        success=True,
        affected_count=deleted_count,
        message=f"Successfully deleted {deleted_count} tasks",
        task_ids=task_ids
    )


@router.get("/tasks/status/{status}", response_model=TaskListResponse)
async def get_tasks_by_status(
    status: TaskStatus,
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Number of tasks to return"
    ),
    sort_by: Optional[SortField] = Query(None, description="Field to sort by"),
    sort_order: Optional[SortOrder] = Query(SortOrder.desc, description="Sort order (asc/desc)"),
    task_service: TaskService = Depends(get_task_service)
):
    """Get tasks by status"""
    tasks, total = task_service.get_tasks_by_status(
        status, skip, limit, sort_by, sort_order
    )
    
    return TaskListResponse(
        tasks=tasks,
        total=total,
        skip=skip,
        limit=limit,
        sort_by=sort_by.value if sort_by else None,
        sort_order=sort_order.value if sort_order else None
    )


@router.get("/tasks/priority/{priority}", response_model=TaskListResponse)
async def get_tasks_by_priority(
    priority: TaskPriority,
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Number of tasks to return"
    ),
    sort_by: Optional[SortField] = Query(None, description="Field to sort by"),
    sort_order: Optional[SortOrder] = Query(SortOrder.desc, description="Sort order (asc/desc)"),
    task_service: TaskService = Depends(get_task_service)
):
    """Get tasks by priority"""
    tasks, total = task_service.get_tasks_by_priority(
        priority, skip, limit, sort_by, sort_order
    )
    
    return TaskListResponse(
        tasks=tasks,
        total=total,
        skip=skip,
        limit=limit,
        sort_by=sort_by.value if sort_by else None,
        sort_order=sort_order.value if sort_order else None
    )


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    task_service: TaskService = Depends(get_task_service)
):
    """Create a new task"""
    return task_service.create_task(task)


@router.get("/tasks", response_model=TaskListResponse)
async def get_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Number of tasks to return"
    ),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    sort_by: Optional[SortField] = Query(None, description="Field to sort by"),
    sort_order: Optional[SortOrder] = Query(SortOrder.desc, description="Sort order (asc/desc)"),
    task_service: TaskService = Depends(get_task_service)
):
    """List all tasks with optional filtering, sorting and pagination"""
    tasks, total = task_service.get_tasks(
        skip=skip,
        limit=limit,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return TaskListResponse(
        tasks=tasks,
        total=total,
        skip=skip,
        limit=limit,
        sort_by=sort_by.value if sort_by else None,
        sort_order=sort_order.value if sort_order else None
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service)
):
    """Retrieve a specific task"""
    return task_service.get_task_by_id(task_id)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    task_service: TaskService = Depends(get_task_service)
):
    """Update an existing task"""
    return task_service.update_task(task_id, task_update)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service)
):
    """Delete a task"""
    task_service.delete_task(task_id)
    return {"message": "Task deleted successfully"} 