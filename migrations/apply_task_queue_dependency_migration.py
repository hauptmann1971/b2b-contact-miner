"""Apply task queue dependency fields migration"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models.database import engine, SessionLocal
from loguru import logger

def apply_migration():
    """Add keyword_id and depends_on_task_id columns to task_queue table"""
    
    logger.info("Starting task_queue dependency fields migration...")
    
    db = SessionLocal()
    try:
        # Check if columns already exist
        result = db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'task_queue'
            AND COLUMN_NAME IN ('keyword_id', 'depends_on_task_id')
        """)).fetchall()
        
        existing_columns = [row[0] for row in result]
        
        if 'keyword_id' in existing_columns and 'depends_on_task_id' in existing_columns:
            logger.info("Migration already applied - columns exist")
            return
        
        logger.info("Adding new columns to task_queue table...")
        
        # Add keyword_id column if not exists
        if 'keyword_id' not in existing_columns:
            db.execute(text("""
                ALTER TABLE task_queue 
                ADD COLUMN keyword_id INT NULL
            """))
            logger.info("✓ Added keyword_id column")
        
        # Add depends_on_task_id column if not exists
        if 'depends_on_task_id' not in existing_columns:
            db.execute(text("""
                ALTER TABLE task_queue 
                ADD COLUMN depends_on_task_id INT NULL
            """))
            logger.info("✓ Added depends_on_task_id column")
        
        # Add indexes (without IF NOT EXISTS for MySQL compatibility)
        try:
            db.execute(text("""
                CREATE INDEX idx_task_queue_keyword_id 
                ON task_queue(keyword_id)
            """))
            logger.info("✓ Created index on keyword_id")
        except Exception as e:
            if "Duplicate key name" in str(e):
                logger.info("✓ Index on keyword_id already exists")
            else:
                raise
        
        try:
            db.execute(text("""
                CREATE INDEX idx_task_queue_depends_on 
                ON task_queue(depends_on_task_id)
            """))
            logger.info("✓ Created index on depends_on_task_id")
        except Exception as e:
            if "Duplicate key name" in str(e):
                logger.info("✓ Index on depends_on_task_id already exists")
            else:
                raise
        
        db.commit()
        logger.info("✅ Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    apply_migration()
