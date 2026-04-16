"""Apply contacts_json migration for hybrid approach"""
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from models.database import SessionLocal
from loguru import logger

def apply_migration():
    """Add contacts_json column to domain_contacts"""
    logger.info("Starting contacts_json migration...")
    
    db = SessionLocal()
    try:
        # Check if column already exists
        existing = db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'domain_contacts' 
            AND COLUMN_NAME = 'contacts_json'
        """)).fetchone()
        
        if existing:
            logger.info("✓ contacts_json column already exists - skipping migration")
            return
        
        logger.info("Adding contacts_json column to domain_contacts...")
        db.execute(text("""
            ALTER TABLE domain_contacts 
            ADD COLUMN contacts_json JSON
        """))
        
        db.commit()
        logger.info("✅ Migration completed successfully!")
        logger.info("Hybrid approach: JSON for fast read + normalized table for search")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    apply_migration()
