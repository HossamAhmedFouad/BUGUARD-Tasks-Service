from sqlmodel import create_engine, Session, SQLModel
from app.core.config import settings
from contextlib import contextmanager
from typing import Generator


# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.echo_sql,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)


def create_db_and_tables():
    """Create database and tables"""
    # Import models to ensure they are registered with SQLModel
    from app.models.database import Task
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session dependency for FastAPI"""
    with Session(engine) as session:
        yield session


@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close() 