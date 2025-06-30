import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.services.task_service import TaskService
from app.models.database import Task
from app.models.schemas import TaskCreate, TaskUpdate, BulkTaskUpdate, BulkTaskDelete
from app.models.enums import TaskStatus, TaskPriority


class TestTaskService:
    """Test TaskService business logic"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_session = Mock()
        self.service = TaskService(self.mock_session)
    
    def test_create_task_success(self):
        """Test successful task creation"""
        # Setup
        task_data = TaskCreate(
            title="Test Task",
            description="Test Description",
            priority=TaskPriority.high
        )
        
        mock_task = Task(
            id=1,
            title="Test Task",
            description="Test Description",
            priority=TaskPriority.high,
            status=TaskStatus.pending,
            created_at=datetime.utcnow()
        )
        
        self.mock_session.add = Mock()
        self.mock_session.commit = Mock()
        self.mock_session.refresh = Mock()
        
        # Mock the Task constructor
        with pytest.MonkeyPatch().context() as m:
            m.setattr('app.services.task_service.Task', lambda **kwargs: mock_task)
            
            # Execute
            result = self.service.create_task(task_data)
            
            # Verify
            assert result == mock_task
            self.mock_session.add.assert_called_once()
            self.mock_session.commit.assert_called_once()
            self.mock_session.refresh.assert_called_once_with(mock_task)
    
    def test_get_task_by_id_found(self):
        """Test getting existing task by ID"""
        # Setup
        mock_task = Task(id=1, title="Test Task", status=TaskStatus.pending)
        self.mock_session.get.return_value = mock_task
        
        # Execute
        result = self.service.get_task_by_id(1)
        
        # Verify
        assert result == mock_task
        self.mock_session.get.assert_called_once_with(Task, 1)
    
    def test_get_task_by_id_not_found(self):
        """Test getting non-existent task by ID"""
        # Setup
        self.mock_session.get.return_value = None
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            self.service.get_task_by_id(999)
        
        assert exc_info.value.status_code == 404
        assert "Task not found" in str(exc_info.value.detail)
    
    def test_update_task_success(self):
        """Test successful task update"""
        # Setup
        existing_task = Task(
            id=1,
            title="Old Title",
            status=TaskStatus.pending,
            priority=TaskPriority.low
        )
        
        update_data = TaskUpdate(
            title="New Title",
            priority=TaskPriority.high
        )
        
        self.mock_session.get.return_value = existing_task
        self.mock_session.add = Mock()
        self.mock_session.commit = Mock()
        self.mock_session.refresh = Mock()
        
        # Execute
        result = self.service.update_task(1, update_data)
        
        # Verify
        assert result.title == "New Title"
        assert result.priority == TaskPriority.high
        assert result.updated_at is not None
        self.mock_session.commit.assert_called_once()
    
    def test_update_task_not_found(self):
        """Test updating non-existent task"""
        # Setup
        self.mock_session.get.return_value = None
        update_data = TaskUpdate(title="New Title")
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            self.service.update_task(999, update_data)
        
        assert exc_info.value.status_code == 404
    
    def test_delete_task_success(self):
        """Test successful task deletion"""
        # Setup
        mock_task = Task(id=1, title="Test Task")
        self.mock_session.get.return_value = mock_task
        self.mock_session.delete = Mock()
        self.mock_session.commit = Mock()
        
        # Execute
        self.service.delete_task(1)
        
        # Verify
        self.mock_session.delete.assert_called_once_with(mock_task)
        self.mock_session.commit.assert_called_once()
    
    def test_delete_task_not_found(self):
        """Test deleting non-existent task"""
        # Setup
        self.mock_session.get.return_value = None
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            self.service.delete_task(999)
        
        assert exc_info.value.status_code == 404
    
    def test_bulk_update_tasks_success(self):
        """Test successful bulk update"""
        # Setup
        task1 = Task(id=1, title="Task 1", status=TaskStatus.pending)
        task2 = Task(id=2, title="Task 2", status=TaskStatus.pending)
        existing_tasks = [task1, task2]
        
        bulk_update = BulkTaskUpdate(
            task_ids=[1, 2],
            update_data=TaskUpdate(status=TaskStatus.in_progress, assigned_to="John")
        )
        
        mock_exec_result = Mock()
        mock_exec_result.all.return_value = existing_tasks
        self.mock_session.exec.return_value = mock_exec_result
        self.mock_session.add = Mock()
        self.mock_session.commit = Mock()
        
        # Execute
        updated_count, task_ids = self.service.bulk_update_tasks(bulk_update)
        
        # Verify
        assert updated_count == 2
        assert task_ids == [1, 2]
        assert task1.status == TaskStatus.in_progress
        assert task2.assigned_to == "John"
        assert self.mock_session.commit.called
    
    def test_bulk_update_tasks_not_found(self):
        """Test bulk update with non-existent tasks"""
        # Setup
        bulk_update = BulkTaskUpdate(
            task_ids=[999, 1000],
            update_data=TaskUpdate(status=TaskStatus.completed)
        )
        
        mock_exec_result = Mock()
        mock_exec_result.all.return_value = []  # No tasks found
        self.mock_session.exec.return_value = mock_exec_result
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            self.service.bulk_update_tasks(bulk_update)
        
        assert exc_info.value.status_code == 404
        assert "Tasks not found" in str(exc_info.value.detail)
    
    def test_bulk_delete_tasks_success(self):
        """Test successful bulk deletion"""
        # Setup
        task1 = Task(id=1, title="Task 1")
        task2 = Task(id=2, title="Task 2")
        existing_tasks = [task1, task2]
        
        bulk_delete = BulkTaskDelete(task_ids=[1, 2])
        
        mock_exec_result = Mock()
        mock_exec_result.all.return_value = existing_tasks
        self.mock_session.exec.return_value = mock_exec_result
        self.mock_session.delete = Mock()
        self.mock_session.commit = Mock()
        
        # Execute
        deleted_count, task_ids = self.service.bulk_delete_tasks(bulk_delete)
        
        # Verify
        assert deleted_count == 2
        assert task_ids == [1, 2]
        assert self.mock_session.delete.call_count == 2
        assert self.mock_session.commit.called
    
    def test_get_task_statistics(self):
        """Test task statistics calculation"""
        # Setup
        mock_exec_results = [
            Mock(one=lambda: 10),  # Total tasks
            Mock(one=lambda: 3),   # Pending tasks
            Mock(one=lambda: 2),   # In progress tasks
            Mock(one=lambda: 4),   # Completed tasks
            Mock(one=lambda: 1),   # Cancelled tasks
            Mock(one=lambda: 2),   # Low priority
            Mock(one=lambda: 5),   # Medium priority
            Mock(one=lambda: 2),   # High priority
            Mock(one=lambda: 1),   # Urgent priority
        ]
        
        self.mock_session.exec.side_effect = mock_exec_results
        
        # Execute
        stats = self.service.get_task_statistics()
        
        # Verify
        assert stats['total_tasks'] == 10
        assert stats['status_breakdown']['pending'] == 3
        assert stats['status_breakdown']['in_progress'] == 2
        assert stats['status_breakdown']['completed'] == 4
        assert stats['status_breakdown']['cancelled'] == 1
        assert stats['priority_breakdown']['low'] == 2
        assert stats['priority_breakdown']['medium'] == 5
        assert stats['priority_breakdown']['high'] == 2
        assert stats['priority_breakdown']['urgent'] == 1 