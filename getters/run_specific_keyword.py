"""
Add specific keyword and run pipeline for it
"""
from models.database import SessionLocal, init_db, Keyword
from models.schemas import KeywordInput
from services.keyword_service import KeywordService
import asyncio
from main import ContactMiningPipeline


def add_keyword(keyword_text: str, language: str = "ru", country: str = "RU"):
    """Add a single keyword to database"""
    init_db()
    db = SessionLocal()
    
    try:
        keyword_service = KeywordService(db)
        
        # Check if keyword already exists
        existing = db.query(Keyword).filter(Keyword.keyword == keyword_text).first()
        if existing:
            print(f"⚠️  Keyword '{keyword_text}' already exists (ID: {existing.id})")
            return existing.id
        
        # Add new keyword
        keyword_data = KeywordInput(
            keyword=keyword_text,
            language=language,
            country=country
        )
        
        keyword = keyword_service.add_keyword(keyword_data)
        print(f"✅ Added keyword: '{keyword_text}' (ID: {keyword.id})")
        
        return keyword.id
        
    finally:
        db.close()


async def run_pipeline_for_keyword(keyword_id: int):
    """Run pipeline for specific keyword"""
    pipeline = ContactMiningPipeline()
    
    try:
        await pipeline.initialize()
        
        db = SessionLocal()
        try:
            keyword_service = KeywordService(db)
            keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
            
            if not keyword:
                print(f"❌ Keyword ID {keyword_id} not found!")
                return
            
            print(f"\n{'='*80}")
            print(f"Running pipeline for keyword: '{keyword.keyword}'")
            print(f"{'='*80}\n")
            
            # Process only this keyword
            result = await pipeline._process_keyword(db, keyword_service, keyword)
            
            print(f"\n{'='*80}")
            print(f"Pipeline completed!")
            print(f"Websites processed: {result.get('websites', 0)}")
            print(f"Contacts found: {result.get('contacts', 0)}")
            print(f"{'='*80}")
            
        finally:
            db.close()
            
    finally:
        await pipeline.shutdown()


if __name__ == "__main__":
    import sys
    
    keyword_text = "искусственный интеллект"
    
    print("="*80)
    print(f"Adding keyword: '{keyword_text}'")
    print("="*80)
    
    # Add keyword
    keyword_id = add_keyword(keyword_text, language="ru", country="RU")
    
    if keyword_id:
        print(f"\nStarting pipeline for keyword ID: {keyword_id}")
        print("="*80)
        
        # Run pipeline
        asyncio.run(run_pipeline_for_keyword(keyword_id))
