#!/usr/bin/env python3
"""
Standalone migration script for Task Management API
"""

import sys
import argparse
from app.database.migrations import migration_manager


def main():
    """Main migration script"""
    parser = argparse.ArgumentParser(description="Database migration tool")
    parser.add_argument("command", choices=["migrate", "rollback", "status"], 
                       help="Migration command to run")
    parser.add_argument("--target", type=str, help="Target version for rollback")
    
    args = parser.parse_args()
    
    try:
        if args.command == "migrate":
            print("🚀 Running database migrations...")
            result = migration_manager.migrate()
            print(f"✅ {result['message']}")
            
            if result['migrations']:
                print("\nMigrations applied:")
                for migration in result['migrations']:
                    status_icon = "✅" if migration['status'] == 'success' else "❌"
                    print(f"  {status_icon} {migration['version']}: {migration['description']}")
        
        elif args.command == "rollback":
            print("🔄 Rolling back migrations...")
            result = migration_manager.rollback(args.target)
            print(f"✅ {result['message']}")
            
            if result.get('migrations'):
                print("\nMigrations rolled back:")
                for migration in result['migrations']:
                    status_icon = "✅" if migration['status'] == 'rolled_back' else "❌"
                    print(f"  {status_icon} {migration['version']}: {migration['description']}")
        
        elif args.command == "status":
            print("📊 Migration status:")
            result = migration_manager.status()
            
            print(f"  Total migrations: {result['total_migrations']}")
            print(f"  Applied: {result['applied_migrations']}")
            print(f"  Pending: {result['pending_migrations']}")
            
            print("\nDetailed status:")
            for migration in result['migrations']:
                status_icon = "✅" if migration['applied'] else "⏳"
                status_text = "Applied" if migration['applied'] else "Pending"
                print(f"  {status_icon} {migration['version']}: {migration['description']} ({status_text})")
    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 