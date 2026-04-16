"""Apply database migrations"""
import sys
import os
# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from models.database import SessionLocal, engine
from loguru import logger


def apply_migration(sql_file: str):
    """Apply SQL migration file"""
    migration_path = os.path.join(os.path.dirname(__file__), sql_file)
    
    if not os.path.exists(migration_path):
        logger.error(f"Migration file not found: {migration_path}")
        return False
    
    try:
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        db = SessionLocal()
        
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for statement in statements:
            if statement:
                db.execute(text(statement))
        
        db.commit()
        logger.info(f"Successfully applied migration: {sql_file}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to apply migration: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Applying task_queue table migration...")
    success = apply_migration("add_task_queue_table.sql")
    
    if success:
        logger.info("✅ Migration completed successfully!")
    else:
        logger.error("❌ Migration failed!")
        sys.exit(1)
