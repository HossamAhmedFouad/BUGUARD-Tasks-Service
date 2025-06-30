from fastapi import APIRouter, HTTPException
from app.database.migrations import migration_manager

router = APIRouter(prefix="/admin", tags=["Admin - Migrations"])


@router.get("/migrations/status")
async def get_migration_status():
    """Get current migration status"""
    try:
        return migration_manager.status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get migration status: {str(e)}")


@router.post("/migrations/migrate")
async def run_migrations():
    """Apply pending migrations"""
    try:
        result = migration_manager.migrate()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.post("/migrations/rollback")
async def rollback_migration(target_version: str = None):
    """Rollback migrations to target version"""
    try:
        result = migration_manager.rollback(target_version)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}") 