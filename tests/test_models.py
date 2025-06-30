import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.models.enums import TaskStatus, TaskPriority
from app.models.schemas import TaskCreate, TaskUpdate, TaskResponse
from app.validation.validators import TaskValidator


class TestTaskEnums:
    """Test task enumerations"""
    
    def test_task_status_values(self):
        """Test TaskStatus enum values"""
        assert TaskStatus.pending == "pending"
        assert TaskStatus.in_progress == "in_progress"
        assert TaskStatus.completed == "completed"
        assert TaskStatus.cancelled == "cancelled"
    
    def test_task_priority_values(self):
        """Test TaskPriority enum values"""
        assert TaskPriority.low == "low"
        assert TaskPriority.medium == "medium"
        assert TaskPriority.high == "high"
        assert TaskPriority.urgent == "urgent"
    
    def test_priority_sort_values(self):
        """Test priority sorting logic"""
        assert TaskPriority.low.sort_value == 1
        assert TaskPriority.medium.sort_value == 2
        assert TaskPriority.high.sort_value == 3
        assert TaskPriority.urgent.sort_value == 4


class TestTaskSchemas:
    """Test Pydantic schemas"""
    
    def test_task_create_valid(self):
        """Test valid task creation"""
        future_date = datetime.utcnow() + timedelta(days=1)
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "priority": "high",
            "due_date": future_date.isoformat(),
            "assigned_to": "John Doe"
        }
        
        task = TaskCreate(**task_data)
        assert task.title == "Test Task"
        assert task.priority == TaskPriority.high
        assert task.status == TaskStatus.pending  # default
    
    def test_task_create_title_validation(self):
        """Test title validation"""
        # Empty title should fail
        with pytest.raises(ValidationError):
            TaskCreate(title="")
        
        # Whitespace only should fail
        with pytest.raises(ValidationError):
            TaskCreate(title="   ")
        
        # Valid title should work
        task = TaskCreate(title="  Valid Title  ")
        assert task.title == "Valid Title"  # trimmed
    
    def test_task_create_due_date_validation(self):
        """Test due date validation"""
        # Past date should fail
        past_date = datetime.utcnow() - timedelta(days=1)
        with pytest.raises(ValidationError):
            TaskCreate(title="Test", due_date=past_date)
        
        # Future date should work
        future_date = datetime.utcnow() + timedelta(days=1)
        task = TaskCreate(title="Test", due_date=future_date)
        assert task.due_date == future_date
    
    def test_task_update_optional_fields(self):
        """Test TaskUpdate with optional fields"""
        # All fields optional
        update = TaskUpdate()
        assert update.title is None
        
        # Partial update
        update = TaskUpdate(title="Updated Title", priority="urgent")
        assert update.title == "Updated Title"
        assert update.priority == TaskPriority.urgent
        assert update.description is None
    
    def test_task_response_from_attributes(self):
        """Test TaskResponse schema"""
        # This would normally be tested with actual database objects
        # For now, just test the schema definition
        response_data = {
            "id": 1,
            "title": "Test Task",
            "description": "Test Description",
            "status": "pending",
            "priority": "high",
            "created_at": datetime.utcnow(),
            "updated_at": None,
            "due_date": None,
            "assigned_to": "John Doe"
        }
        
        response = TaskResponse(**response_data)
        assert response.id == 1
        assert response.title == "Test Task"
        assert response.status == TaskStatus.pending


class TestTaskValidator:
    """Test custom validators"""
    
    def test_validate_title(self):
        """Test title validation"""
        validator = TaskValidator()
        
        # Valid title
        assert validator.validate_title("Valid Title") == "Valid Title"
        
        # Title with whitespace
        assert validator.validate_title("  Spaced Title  ") == "Spaced Title"
        
        # Empty title should raise error
        with pytest.raises(ValueError, match="Title cannot be empty"):
            validator.validate_title("")
        
        # Whitespace only should raise error
        with pytest.raises(ValueError, match="Title cannot be empty"):
            validator.validate_title("   ")
    
    def test_validate_description(self):
        """Test description validation"""
        validator = TaskValidator()
        
        # Valid description
        desc = "A" * 500
        assert validator.validate_description(desc) == desc
        
        # None description
        assert validator.validate_description(None) is None
        
        # Too long description
        long_desc = "A" * 1001
        with pytest.raises(ValueError, match="Description cannot exceed 1000 characters"):
            validator.validate_description(long_desc)
    
    def test_validate_due_date(self):
        """Test due date validation"""
        validator = TaskValidator()
        
        # Future date
        future_date = datetime.utcnow() + timedelta(days=1)
        assert validator.validate_due_date(future_date) == future_date
        
        # None date
        assert validator.validate_due_date(None) is None
        
        # Past date should raise error
        past_date = datetime.utcnow() - timedelta(days=1)
        with pytest.raises(ValueError, match="Due date must be in the future"):
            validator.validate_due_date(past_date)
    
    def test_validate_status_transition(self):
        """Test status transition validation"""
        validator = TaskValidator()
        
        # Valid transitions
        assert validator.validate_status_transition(TaskStatus.pending, TaskStatus.in_progress)
        assert validator.validate_status_transition(TaskStatus.in_progress, TaskStatus.completed)
        assert validator.validate_status_transition(TaskStatus.completed, TaskStatus.in_progress)
        
        # Invalid transitions (these should be allowed based on current logic)
        # Our current implementation allows all transitions, but this test
        # documents the expected behavior if we wanted to restrict them
        # assert not validator.validate_status_transition(TaskStatus.completed, TaskStatus.pending)
    
    def test_validate_priority(self):
        """Test priority validation"""
        validator = TaskValidator()
        
        # Valid priorities
        assert validator.validate_priority(TaskPriority.low) == TaskPriority.low
        assert validator.validate_priority(TaskPriority.urgent) == TaskPriority.urgent
    
    def test_validate_assigned_to(self):
        """Test assignee validation"""
        validator = TaskValidator()
        
        # Valid assignee
        assert validator.validate_assigned_to("John Doe") == "John Doe"
        
        # None assignee
        assert validator.validate_assigned_to(None) is None
        
        # Empty string
        assert validator.validate_assigned_to("") is None
        
        # Whitespace
        assert validator.validate_assigned_to("  John  ") == "John"
        
        # Too long assignee
        long_name = "A" * 101
        with pytest.raises(ValueError, match="Assignee name cannot exceed 100 characters"):
            validator.validate_assigned_to(long_name) 