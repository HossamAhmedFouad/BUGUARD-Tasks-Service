import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel, select
from app.main import app
from app.database.connection import get_session
from app.models.database import Task  # Import to register the model
import os
import tempfile


# Use a temporary file for test database
TEST_DATABASE_URL = f"sqlite:///{tempfile.gettempdir()}/test_tasks_{os.getpid()}.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    # Use temporary file-based database for better consistency
    engine = create_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    yield engine
    
    # Clean up - remove test database file
    try:
        db_path = TEST_DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_path):
            os.remove(db_path)
    except (FileNotFoundError, PermissionError):
        # File might already be deleted or in use, that's okay
        pass


@pytest.fixture(scope="session")
def test_client(test_engine):
    """Create a test client with proper database setup"""
    
    def get_test_session():
        """Override database session for testing"""
        with Session(test_engine) as session:
            yield session
    
    # Override the database dependency
    app.dependency_overrides[get_session] = get_test_session
    
    # Create test client
    with TestClient(app) as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def setup_and_cleanup_database(test_engine):
    """Set up and clean up database for each test"""
    # Clean up any existing data before each test
    with Session(test_engine) as session:
        # Delete all tasks using SQLModel's exec() method
        statement = select(Task)
        tasks = session.exec(statement).all()
        for task in tasks:
            session.delete(task)
        session.commit()
    
    yield
    
    # Clean up after each test
    with Session(test_engine) as session:
        statement = select(Task)
        tasks = session.exec(statement).all()
        for task in tasks:
            session.delete(task)
        session.commit() 