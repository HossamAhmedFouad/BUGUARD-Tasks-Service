"""
Database migration system for Task Management API
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from app.core.config import settings


class Migration:
    """Base migration class"""
    
    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
        self.timestamp = datetime.utcnow()
    
    def up(self, connection: sqlite3.Connection):
        """Apply the migration"""
        raise NotImplementedError("Subclasses must implement up() method")
    
    def down(self, connection: sqlite3.Connection):
        """Rollback the migration"""
        raise NotImplementedError("Subclasses must implement down() method")


class CreateTasksTable(Migration):
    """Initial migration to create tasks table"""
    
    def __init__(self):
        super().__init__("001", "Create tasks table")
    
    def up(self, connection: sqlite3.Connection):
        """Create the tasks table"""
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                priority VARCHAR(10) NOT NULL DEFAULT 'medium',
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP,
                due_date TIMESTAMP,
                assigned_to VARCHAR(100)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to)")
        
        connection.commit()
    
    def down(self, connection: sqlite3.Connection):
        """Drop the tasks table"""
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS tasks")
        connection.commit()


class AddTaskIndexes(Migration):
    """Add additional indexes for performance"""
    
    def __init__(self):
        super().__init__("002", "Add performance indexes")
    
    def up(self, connection: sqlite3.Connection):
        """Add additional indexes"""
        cursor = connection.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_compound_status_priority ON tasks(status, priority)")
        connection.commit()
    
    def down(self, connection: sqlite3.Connection):
        """Remove the indexes"""
        cursor = connection.cursor()
        cursor.execute("DROP INDEX IF EXISTS idx_tasks_title")
        cursor.execute("DROP INDEX IF EXISTS idx_tasks_compound_status_priority")
        connection.commit()


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.database_url
        self.migrations = [
            CreateTasksTable(),
            AddTaskIndexes(),
        ]
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        db_path = self.database_url.replace("sqlite:///", "")
        return sqlite3.connect(db_path)
    
    def _create_migration_table(self, connection: sqlite3.Connection):
        """Create migration tracking table"""
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                version VARCHAR(10) PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TIMESTAMP NOT NULL
            )
        """)
        connection.commit()
    
    def _get_applied_migrations(self, connection: sqlite3.Connection) -> List[str]:
        """Get list of applied migration versions"""
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT version FROM migrations ORDER BY version")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Migration table doesn't exist yet
            return []
    
    def _record_migration(self, connection: sqlite3.Connection, migration: Migration):
        """Record a migration as applied"""
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO migrations (version, description, applied_at) VALUES (?, ?, ?)",
            (migration.version, migration.description, datetime.utcnow())
        )
        connection.commit()
    
    def migrate(self) -> Dict[str, any]:
        """Apply pending migrations"""
        with self._get_connection() as connection:
            self._create_migration_table(connection)
            applied_migrations = self._get_applied_migrations(connection)
            
            pending_migrations = [
                m for m in self.migrations 
                if m.version not in applied_migrations
            ]
            
            if not pending_migrations:
                return {
                    "status": "up_to_date",
                    "message": "No pending migrations",
                    "applied_count": 0
                }
            
            results = []
            for migration in pending_migrations:
                try:
                    print(f"Applying migration {migration.version}: {migration.description}")
                    migration.up(connection)
                    self._record_migration(connection, migration)
                    results.append({
                        "version": migration.version,
                        "description": migration.description,
                        "status": "success"
                    })
                    print(f"✅ Migration {migration.version} applied successfully")
                except Exception as e:
                    print(f"❌ Migration {migration.version} failed: {e}")
                    results.append({
                        "version": migration.version,
                        "description": migration.description,
                        "status": "failed",
                        "error": str(e)
                    })
                    break
            
            return {
                "status": "completed",
                "message": f"Applied {len([r for r in results if r['status'] == 'success'])} migrations",
                "applied_count": len([r for r in results if r['status'] == 'success']),
                "migrations": results
            }
    
    def rollback(self, target_version: str = None) -> Dict[str, any]:
        """Rollback migrations to target version"""
        with self._get_connection() as connection:
            self._create_migration_table(connection)
            applied_migrations = self._get_applied_migrations(connection)
            
            if not applied_migrations:
                return {
                    "status": "no_migrations",
                    "message": "No migrations to rollback"
                }
            
            # Determine which migrations to rollback
            if target_version:
                rollback_migrations = [
                    m for m in reversed(self.migrations)
                    if m.version in applied_migrations and m.version > target_version
                ]
            else:
                # Rollback the last migration only
                rollback_migrations = [
                    m for m in reversed(self.migrations)
                    if m.version == applied_migrations[-1]
                ]
            
            if not rollback_migrations:
                return {
                    "status": "nothing_to_rollback",
                    "message": f"No migrations to rollback to version {target_version or 'previous'}"
                }
            
            results = []
            cursor = connection.cursor()
            
            for migration in rollback_migrations:
                try:
                    print(f"Rolling back migration {migration.version}: {migration.description}")
                    migration.down(connection)
                    cursor.execute("DELETE FROM migrations WHERE version = ?", (migration.version,))
                    connection.commit()
                    results.append({
                        "version": migration.version,
                        "description": migration.description,
                        "status": "rolled_back"
                    })
                    print(f"✅ Migration {migration.version} rolled back successfully")
                except Exception as e:
                    print(f"❌ Rollback of migration {migration.version} failed: {e}")
                    results.append({
                        "version": migration.version,
                        "description": migration.description,
                        "status": "failed",
                        "error": str(e)
                    })
                    break
            
            return {
                "status": "completed",
                "message": f"Rolled back {len([r for r in results if r['status'] == 'rolled_back'])} migrations",
                "rollback_count": len([r for r in results if r['status'] == 'rolled_back']),
                "migrations": results
            }
    
    def status(self) -> Dict[str, any]:
        """Get migration status"""
        with self._get_connection() as connection:
            self._create_migration_table(connection)
            applied_migrations = self._get_applied_migrations(connection)
            
            all_migrations = []
            for migration in self.migrations:
                all_migrations.append({
                    "version": migration.version,
                    "description": migration.description,
                    "applied": migration.version in applied_migrations
                })
            
            pending_count = len([m for m in all_migrations if not m["applied"]])
            
            return {
                "total_migrations": len(self.migrations),
                "applied_migrations": len(applied_migrations),
                "pending_migrations": pending_count,
                "migrations": all_migrations
            }


# Global migration manager instance
migration_manager = MigrationManager() 