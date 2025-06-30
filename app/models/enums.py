from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration"""
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enumeration with numeric values for sorting"""
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"
    
    @property
    def sort_value(self) -> int:
        """Return numeric value for sorting priorities logically"""
        priority_values = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "urgent": 4
        }
        return priority_values.get(self.value, 0)
    
    @classmethod
    def get_sort_mapping(cls):
        """Get mapping for SQL ordering"""
        return {
            cls.low: 1,
            cls.medium: 2,
            cls.high: 3,
            cls.urgent: 4
        } 