"""Apply raw_search_response migration"""
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from models.database import SessionLocal
from loguru import logger

def apply_migration():
    """Add raw_search_response column to search_results"""
    logger.info("Starting raw_search_response migration...")
    
    db = SessionLocal()
    try:
        # Check if column already exists
        existing = db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'search_results' 
            AND COLUMN_NAME = 'raw_search_response'
        """)).fetchone()
        
        if existing:
            logger.info("✓ raw_search_response column already exists - skipping migration")
            return
        
        logger.info("Adding raw_search_response column to search_results...")
        db.execute(text("""
            ALTER TABLE search_results 
            ADD COLUMN raw_search_response JSON AFTER raw_search_query
        """))
        
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
