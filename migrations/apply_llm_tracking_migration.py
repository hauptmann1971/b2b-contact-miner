"""Apply LLM tracking fields migration"""
import sys
import os
# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from models.database import SessionLocal, engine
from loguru import logger

def apply_migration():
    """Add LLM tracking fields to database"""
    logger.info("Starting LLM tracking fields migration...")
    
    db = SessionLocal()
    try:
        # Check if columns already exist
        search_results_columns = db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'search_results' 
            AND COLUMN_NAME = 'raw_search_query'
        """)).fetchone()
        
        crawl_logs_columns = db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'crawl_logs' 
            AND COLUMN_NAME = 'llm_request'
        """)).fetchone()
        
        if search_results_columns and crawl_logs_columns:
            logger.info("✓ LLM tracking fields already exist - skipping migration")
            return
        
        logger.info("Adding raw_search_query to search_results...")
        db.execute(text("""
            ALTER TABLE search_results 
            ADD COLUMN raw_search_query TEXT AFTER is_processed
        """))
        logger.info("✓ Added raw_search_query column")
        
        logger.info("Adding LLM fields to crawl_logs...")
        db.execute(text("""
            ALTER TABLE crawl_logs 
            ADD COLUMN llm_request TEXT AFTER duration_seconds,
            ADD COLUMN llm_response TEXT AFTER llm_request,
            ADD COLUMN llm_model VARCHAR(100) AFTER llm_response
        """))
        logger.info("✓ Added llm_request, llm_response, llm_model columns")
        
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
