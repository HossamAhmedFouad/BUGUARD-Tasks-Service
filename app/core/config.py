from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # API Configuration
    app_name: str = "Task Management API"
    app_version: str = "1.0.0"
    app_description: str = "A comprehensive task management system built with FastAPI"
    debug: bool = True
    
    # Database Configuration
    database_url: str = "sqlite:///./tasks.db"
    echo_sql: bool = True
    
    # Server Configuration
    host: str = "localhost"
    port: int = 8000
    reload: bool = True
    
    # Pagination
    default_page_size: int = 100
    max_page_size: int = 1000

    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings() 