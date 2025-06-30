from typing import Optional, List, Tuple
from datetime import datetime
from sqlmodel import Session, select, func, or_, case
from fastapi import HTTPException

from app.models.database import Task
from app.models.schemas import TaskCreate, TaskUpdate, BulkTaskUpdate, BulkTaskDelete, SortField, SortOrder
from app.models.enums import TaskStatus, TaskPriority
from app.validation.validators import TaskValidator


class TaskService:
    """Service layer for task business logic"""
    
    def __init__(self, session: Session):
        self.session = session
        self.validator = TaskValidator()
    
    def create_task(self, task_data: TaskCreate) -> Task:
        """Create a new task with validation"""
        # Validate and sanitize input data
        validated_data = {
            'title': self.validator.validate_title(task_data.title),
            'description': self.validator.validate_description(task_data.description),
            'status': task_data.status,
            'priority': self.validator.validate_priority(task_data.priority),
            'due_date': self.validator.validate_due_date(task_data.due_date),
            'assigned_to': self.validator.validate_assigned_to(task_data.assigned_to)
        }
        
        # Create new task
        db_task = Task(**validated_data)
        self.session.add(db_task)
        self.session.commit()
        self.session.refresh(db_task)
        
        return db_task
    
    def get_task_by_id(self, task_id: int) -> Task:
        """Get a task by ID"""
        task = self.session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    
    def get_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[SortField] = None,
        sort_order: Optional[SortOrder] = None
    ) -> Tuple[List[Task], int]:
        """Get tasks with filtering, pagination, and sorting"""
        query = select(Task)
        count_query = select(func.count(Task.id))
        
        # Apply filters
        if status:
            query = query.where(Task.status == status)
            count_query = count_query.where(Task.status == status)
        
        if priority:
            query = query.where(Task.priority == priority)
            count_query = count_query.where(Task.priority == priority)
        
        if assigned_to:
            query = query.where(Task.assigned_to == assigned_to)
            count_query = count_query.where(Task.assigned_to == assigned_to)
        
        if search:
            # Case-insensitive search using lower() for SQLite compatibility
            search_lower = search.lower()
            search_filter = or_(
                func.lower(Task.title).contains(search_lower),
                func.lower(Task.description).contains(search_lower)
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Apply sorting
        if sort_by:
            if sort_by == SortField.priority:
                # Special handling for priority sorting using numeric values
                priority_case = case(
                    (Task.priority == TaskPriority.low, 1),
                    (Task.priority == TaskPriority.medium, 2),
                    (Task.priority == TaskPriority.high, 3),
                    (Task.priority == TaskPriority.urgent, 4),
                    else_=0
                )
                if sort_order == SortOrder.desc:
                    query = query.order_by(priority_case.desc())
                else:
                    query = query.order_by(priority_case.asc())
            else:
                # Regular column sorting
                sort_column = getattr(Task, sort_by.value)
                if sort_order == SortOrder.desc:
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
        else:
            # Default sorting by created_at descending
            query = query.order_by(Task.created_at.desc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute queries
        tasks = self.session.exec(query).all()
        total = self.session.exec(count_query).one()
        
        return tasks, total
    
    def update_task(self, task_id: int, task_update: TaskUpdate) -> Task:
        """Update an existing task with validation"""
        # Get existing task
        db_task = self.get_task_by_id(task_id)
        
        # Get update data excluding unset fields
        update_data = task_update.model_dump(exclude_unset=True)
        
        # Validate each field that's being updated
        if 'title' in update_data:
            update_data['title'] = self.validator.validate_title(update_data['title'])
        
        if 'description' in update_data:
            update_data['description'] = self.validator.validate_description(update_data['description'])
        
        if 'due_date' in update_data:
            update_data['due_date'] = self.validator.validate_due_date(update_data['due_date'])
        
        if 'assigned_to' in update_data:
            update_data['assigned_to'] = self.validator.validate_assigned_to(update_data['assigned_to'])
        
        if 'priority' in update_data:
            update_data['priority'] = self.validator.validate_priority(update_data['priority'])
        
        # Validate status transition if status is being updated
        if 'status' in update_data:
            new_status = update_data['status']
            if not self.validator.validate_status_transition(db_task.status, new_status):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status transition from {db_task.status} to {new_status}"
                )
        
        # Apply updates
        for field, value in update_data.items():
            setattr(db_task, field, value)
        
        # Set updated timestamp
        db_task.updated_at = datetime.utcnow()
        
        self.session.add(db_task)
        self.session.commit()
        self.session.refresh(db_task)
        
        return db_task
    
    def delete_task(self, task_id: int) -> None:
        """Delete a task"""
        task = self.get_task_by_id(task_id)
        self.session.delete(task)
        self.session.commit()
    
    def bulk_update_tasks(self, bulk_update: BulkTaskUpdate) -> Tuple[int, List[int]]:
        """Update multiple tasks at once"""
        # Validate that all task IDs exist
        existing_tasks = self.session.exec(
            select(Task).where(Task.id.in_(bulk_update.task_ids))
        ).all()
        
        existing_ids = [task.id for task in existing_tasks]
        missing_ids = [task_id for task_id in bulk_update.task_ids if task_id not in existing_ids]
        
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Tasks not found: {missing_ids}"
            )
        
        # Get update data
        update_data = bulk_update.update_data.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No update data provided"
            )
        
        # Validate update data
        if 'title' in update_data:
            update_data['title'] = self.validator.validate_title(update_data['title'])
        
        if 'description' in update_data:
            update_data['description'] = self.validator.validate_description(update_data['description'])
        
        if 'due_date' in update_data:
            update_data['due_date'] = self.validator.validate_due_date(update_data['due_date'])
        
        if 'assigned_to' in update_data:
            update_data['assigned_to'] = self.validator.validate_assigned_to(update_data['assigned_to'])
        
        if 'priority' in update_data:
            update_data['priority'] = self.validator.validate_priority(update_data['priority'])
        
        # Validate status transitions if status is being updated
        if 'status' in update_data:
            new_status = update_data['status']
            for task in existing_tasks:
                if not self.validator.validate_status_transition(task.status, new_status):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid status transition from {task.status} to {new_status} for task {task.id}"
                    )
        
        # Apply updates to all tasks
        update_data['updated_at'] = datetime.utcnow()
        updated_count = 0
        
        for task in existing_tasks:
            for field, value in update_data.items():
                setattr(task, field, value)
            self.session.add(task)
            updated_count += 1
        
        self.session.commit()
        
        return updated_count, existing_ids
    
    def bulk_delete_tasks(self, bulk_delete: BulkTaskDelete) -> Tuple[int, List[int]]:
        """Delete multiple tasks at once"""
        # Get existing tasks
        existing_tasks = self.session.exec(
            select(Task).where(Task.id.in_(bulk_delete.task_ids))
        ).all()
        
        existing_ids = [task.id for task in existing_tasks]
        
        if not existing_ids:
            raise HTTPException(
                status_code=404,
                detail="No tasks found to delete"
            )
        
        # Delete all tasks
        for task in existing_tasks:
            self.session.delete(task)
        
        self.session.commit()
        
        return len(existing_ids), existing_ids
    
    def get_tasks_by_status(
        self,
        status: TaskStatus,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[SortField] = None,
        sort_order: Optional[SortOrder] = None
    ) -> Tuple[List[Task], int]:
        """Get tasks filtered by status"""
        return self.get_tasks(
            skip=skip, 
            limit=limit, 
            status=status,
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    def get_tasks_by_priority(
        self,
        priority: TaskPriority,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[SortField] = None,
        sort_order: Optional[SortOrder] = None
    ) -> Tuple[List[Task], int]:
        """Get tasks filtered by priority"""
        return self.get_tasks(
            skip=skip, 
            limit=limit, 
            priority=priority,
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    def get_task_statistics(self) -> dict:
        """Get task statistics"""
        total_tasks = self.session.exec(select(func.count(Task.id))).one()
        
        status_counts = {}
        for status in TaskStatus:
            count = self.session.exec(
                select(func.count(Task.id)).where(Task.status == status)
            ).one()
            status_counts[status.value] = count
        
        priority_counts = {}
        for priority in TaskPriority:
            count = self.session.exec(
                select(func.count(Task.id)).where(Task.priority == priority)
            ).one()
            priority_counts[priority.value] = count
        
        return {
            'total_tasks': total_tasks,
            'status_breakdown': status_counts,
            'priority_breakdown': priority_counts
        } 