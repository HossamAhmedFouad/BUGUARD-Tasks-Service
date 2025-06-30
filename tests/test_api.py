import pytest
from datetime import datetime, timedelta
import json


class TestAPIEndpoints:
    """Integration tests for API endpoints"""
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Task Management API"
        assert "endpoints" in data
    
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
    
    def test_create_task_success(self, test_client):
        """Test successful task creation"""
        future_date = datetime.utcnow() + timedelta(days=1)
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "priority": "high",
            "due_date": future_date.isoformat(),
            "assigned_to": "John Doe"
        }
        
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["priority"] == "high"
        assert data["status"] == "pending"  # default
        assert "id" in data
        assert "created_at" in data
    
    def test_create_task_validation_error(self, test_client):
        """Test task creation with validation errors"""
        # Empty title
        task_data = {
            "title": "",
            "description": "Test Description"
        }
        
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 422
        
        # Past due date
        past_date = datetime.utcnow() - timedelta(days=1)
        task_data = {
            "title": "Valid Title",
            "due_date": past_date.isoformat()
        }
        
        response = test_client.post("/tasks", json=task_data)
        assert response.status_code == 422
    
    def test_get_tasks(self, test_client):
        """Test getting all tasks"""
        # Create a test task first
        future_date = datetime.utcnow() + timedelta(days=1)
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "priority": "high",
            "due_date": future_date.isoformat(),
            "assigned_to": "John Doe"
        }
        
        create_response = test_client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        response = test_client.get("/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert len(data["tasks"]) >= 1
    
    def test_get_task_by_id(self, test_client):
        """Test getting specific task by ID"""
        # Create a test task first
        future_date = datetime.utcnow() + timedelta(days=1)
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "priority": "high",
            "due_date": future_date.isoformat(),
            "assigned_to": "John Doe"
        }
        
        create_response = test_client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        response = test_client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Test Task"
        
        # Test non-existent task
        response = test_client.get("/tasks/99999")
        assert response.status_code == 404
    
    def test_update_task(self, test_client):
        """Test task update"""
        # Create a test task first
        future_date = datetime.utcnow() + timedelta(days=1)
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "priority": "high",
            "due_date": future_date.isoformat(),
            "assigned_to": "John Doe"
        }
        
        create_response = test_client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Update the task
        update_data = {
            "title": "Updated Title",
            "status": "in_progress",
            "priority": "urgent"
        }
        
        response = test_client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "in_progress"
        assert data["priority"] == "urgent"
        assert data["updated_at"] is not None
        
        # Test non-existent task update
        response = test_client.put("/tasks/99999", json=update_data)
        assert response.status_code == 404
    
    def test_delete_task(self, test_client):
        """Test task deletion"""
        # Create a test task first
        future_date = datetime.utcnow() + timedelta(days=1)
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "priority": "high",
            "due_date": future_date.isoformat(),
            "assigned_to": "John Doe"
        }
        
        create_response = test_client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Delete the task
        response = test_client.delete(f"/tasks/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "deleted successfully" in data["message"]
        
        # Verify task is deleted
        response = test_client.get(f"/tasks/{task_id}")
        assert response.status_code == 404
        
        # Test deleting non-existent task
        response = test_client.delete("/tasks/99999")
        assert response.status_code == 404
    
    def test_filter_tasks_by_status(self, test_client):
        """Test filtering tasks by status"""
        # Create test tasks with different statuses
        task1_data = {"title": "Pending Task", "status": "pending"}
        task2_data = {"title": "In Progress Task", "status": "in_progress"}
        
        response1 = test_client.post("/tasks", json=task1_data)
        response2 = test_client.post("/tasks", json=task2_data)
        
        task1_id = response1.json()["id"]
        task2_id = response2.json()["id"]
        
        # Filter by pending status
        response = test_client.get("/tasks/status/pending")
        assert response.status_code == 200
        
        data = response.json()
        pending_tasks = [t for t in data["tasks"] if t["status"] == "pending"]
        assert len(pending_tasks) >= 1
        
        # Filter by in_progress status
        response = test_client.get("/tasks/status/in_progress")
        assert response.status_code == 200
        
        data = response.json()
        in_progress_tasks = [t for t in data["tasks"] if t["status"] == "in_progress"]
        assert len(in_progress_tasks) >= 1
        
        # Cleanup
        test_client.delete(f"/tasks/{task1_id}")
        test_client.delete(f"/tasks/{task2_id}")
    
    def test_filter_tasks_by_priority(self, test_client):
        """Test filtering tasks by priority"""
        # Create test tasks with different priorities
        task1_data = {"title": "Low Priority Task", "priority": "low"}
        task2_data = {"title": "High Priority Task", "priority": "high"}
        
        response1 = test_client.post("/tasks", json=task1_data)
        response2 = test_client.post("/tasks", json=task2_data)
        
        task1_id = response1.json()["id"]
        task2_id = response2.json()["id"]
        
        # Filter by high priority
        response = test_client.get("/tasks/priority/high")
        assert response.status_code == 200
        
        data = response.json()
        high_priority_tasks = [t for t in data["tasks"] if t["priority"] == "high"]
        assert len(high_priority_tasks) >= 1
        
        # Cleanup
        test_client.delete(f"/tasks/{task1_id}")
        test_client.delete(f"/tasks/{task2_id}")
    
    def test_search_tasks(self, test_client):
        """Test task search functionality"""
        # Create test tasks
        task1_data = {"title": "API Documentation", "description": "Write API docs"}
        task2_data = {"title": "User Interface", "description": "Design UI components"}
        
        response1 = test_client.post("/tasks", json=task1_data)
        response2 = test_client.post("/tasks", json=task2_data)
        
        task1_id = response1.json()["id"]
        task2_id = response2.json()["id"]
        
        # Search for 'API'
        response = test_client.get("/tasks?search=API")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["tasks"]) >= 1
        found_api_task = any(t["title"] == "API Documentation" for t in data["tasks"])
        assert found_api_task
        
        # Search for 'UI'
        response = test_client.get("/tasks?search=UI")
        assert response.status_code == 200
        
        data = response.json()
        found_ui_task = any("UI" in t["description"] for t in data["tasks"])
        assert found_ui_task
        
        # Cleanup
        test_client.delete(f"/tasks/{task1_id}")
        test_client.delete(f"/tasks/{task2_id}")
    
    def test_sort_tasks(self, test_client):
        """Test task sorting"""
        # Create test tasks
        task1_data = {"title": "Alpha Task", "priority": "low"}
        task2_data = {"title": "Beta Task", "priority": "high"}
        task3_data = {"title": "Gamma Task", "priority": "medium"}
        
        responses = [
            test_client.post("/tasks", json=task1_data),
            test_client.post("/tasks", json=task2_data),
            test_client.post("/tasks", json=task3_data)
        ]
        
        task_ids = [r.json()["id"] for r in responses]
        
        # Sort by title ascending
        response = test_client.get("/tasks?sort_by=title&sort_order=asc")
        assert response.status_code == 200
        
        data = response.json()
        titles = [t["title"] for t in data["tasks"]]
        
        # Check if Alpha comes before Beta and Gamma
        alpha_index = next(i for i, title in enumerate(titles) if title == "Alpha Task")
        beta_index = next(i for i, title in enumerate(titles) if title == "Beta Task")
        assert alpha_index < beta_index
        
        # Sort by priority ascending (low -> high)
        response = test_client.get("/tasks?sort_by=priority&sort_order=asc")
        assert response.status_code == 200
        
        data = response.json()
        priorities = [t["priority"] for t in data["tasks"]]
        
        # Check logical order: low should come before medium and high
        if "low" in priorities and "high" in priorities:
            low_index = priorities.index("low")
            high_index = priorities.index("high")
            assert low_index < high_index
        
        # Cleanup
        for task_id in task_ids:
            test_client.delete(f"/tasks/{task_id}")
    
    def test_pagination(self, test_client):
        """Test pagination"""
        # Create multiple test tasks
        task_ids = []
        for i in range(5):
            task_data = {"title": f"Task {i+1}"}
            response = test_client.post("/tasks", json=task_data)
            task_ids.append(response.json()["id"])
        
        # Test pagination
        response = test_client.get("/tasks?skip=0&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["skip"] == 0
        assert data["limit"] == 2
        assert data["total"] >= 5
        
        # Test second page
        response = test_client.get("/tasks?skip=2&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["tasks"]) <= 2
        assert data["skip"] == 2
        
        # Cleanup
        for task_id in task_ids:
            test_client.delete(f"/tasks/{task_id}")
    
    def test_bulk_operations(self, test_client):
        """Test bulk update and delete operations"""
        # Create test tasks
        task_ids = []
        for i in range(3):
            task_data = {"title": f"Bulk Task {i+1}", "priority": "low"}
            response = test_client.post("/tasks", json=task_data)
            task_ids.append(response.json()["id"])
        
        # Test bulk update
        bulk_update_data = {
            "task_ids": task_ids,
            "update_data": {
                "priority": "high",
                "assigned_to": "Team Lead"
            }
        }
        
        response = test_client.put("/tasks/bulk", json=bulk_update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["affected_count"] == 3
        
        # Verify updates
        for task_id in task_ids:
            response = test_client.get(f"/tasks/{task_id}")
            task = response.json()
            assert task["priority"] == "high"
            assert task["assigned_to"] == "Team Lead"
        
        # Test bulk delete
        bulk_delete_data = {"task_ids": task_ids}
        
        response = test_client.request("DELETE", "/tasks/bulk", json=bulk_delete_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["affected_count"] == 3
        
        # Verify deletion
        for task_id in task_ids:
            response = test_client.get(f"/tasks/{task_id}")
            assert response.status_code == 404
    
    def test_task_statistics(self, test_client):
        """Test task statistics endpoint"""
        response = test_client.get("/tasks/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_tasks" in data
        assert "status_breakdown" in data
        assert "priority_breakdown" in data
        
        # Verify structure
        assert isinstance(data["total_tasks"], int)
        assert isinstance(data["status_breakdown"], dict)
        assert isinstance(data["priority_breakdown"], dict) 