"""
Example script to add keywords for contact mining
Run this before starting the main pipeline
"""
from models.database import SessionLocal, init_db
from models.schemas import KeywordInput
from services.keyword_service import KeywordService


def add_sample_keywords():
    """Add sample keywords for testing"""
    
    # Initialize database
    init_db()
    db = SessionLocal()
    keyword_service = KeywordService(db)
    
    print("="*60)
    print("Adding Keywords for Contact Mining")
    print("="*60)
    
    # Sample keywords - customize these for your needs
    keywords = [
        # Russian keywords
        ("финтех стартап", "ru", "RU"),
        ("AI компания Москва", "ru", "RU"),
        ("blockchain разработка", "ru", "RU"),
        ("IT аутсорсинг", "ru", "RU"),
        
        # English keywords
        ("fintech startup", "en", "US"),
        ("AI company Berlin", "en", "DE"),
        ("blockchain development", "en", "GB"),
        ("software outsourcing", "en", "US"),
        
        # German keywords
        ("fintech unternehmen", "de", "DE"),
        ("KI startup München", "de", "DE"),
    ]
    
    print(f"\nAdding {len(keywords)} keywords...\n")
    
    added_count = 0
    skipped_count = 0
    
    for keyword_text, language, country in keywords:
        try:
            keyword_data = KeywordInput(
                keyword=keyword_text,
                language=language,
                country=country
            )
            
            keyword = keyword_service.add_keyword(keyword_data)
            added_count += 1
            
            print(f"✅ Added: '{keyword_text}' ({language}, {country}) - ID: {keyword.id}")
            
        except Exception as e:
            skipped_count += 1
            print(f"⚠️  Skipped: '{keyword_text}' - {e}")
    
    print("\n" + "="*60)
    print(f"Summary:")
    print(f"  ✅ Added: {added_count}")
    print(f"  ⚠️  Skipped: {skipped_count}")
    print(f"  📊 Total in DB: {len(keyword_service.get_existing_keywords())}")
    print("="*60)
    
    # Show pending keywords
    pending = keyword_service.get_pending_keywords(limit=100)
    print(f"\n⏳ Pending keywords ready for processing: {len(pending)}")
    
    if pending:
        print("\nNext step:")
        print("  Run: python main.py")
        print("\nThis will:")
        print("  1. Search for each keyword using DuckDuckGo")
        print("  2. Crawl top 5 websites per keyword")
        print("  3. Extract emails, Telegram, LinkedIn")
        print("  4. Verify emails via MX records")
        print("  5. Save results to database")
    
    db.close()


def show_existing_keywords():
    """Show all keywords in database"""
    init_db()
    db = SessionLocal()
    keyword_service = KeywordService(db)
    
    print("="*60)
    print("Existing Keywords in Database")
    print("="*60)
    
    keywords = keyword_service.get_existing_keywords()
    
    if not keywords:
        print("\nNo keywords found. Add some first!")
        return
    
    for kw in keywords:
        status = "✅" if kw["is_processed"] else "⏳"
        last_crawl = kw["last_crawled_at"].strftime("%Y-%m-%d %H:%M") if kw["last_crawled_at"] else "Never"
        
        print(f"\n{status} ID: {kw['id']}")
        print(f"   Keyword: {kw['keyword']}")
        print(f"   Language: {kw['language']}")
        print(f"   Country: {kw['country']}")
        print(f"   Last crawled: {last_crawl}")
    
    # Language summary
    lang_summary = keyword_service.get_languages_summary()
    print("\n" + "="*60)
    print("Keywords per language:")
    for lang, count in lang_summary.items():
        print(f"  {lang}: {count}")
    print("="*60)
    
    db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        # Show existing keywords
        show_existing_keywords()
    else:
        # Add sample keywords
        add_sample_keywords()
        
        print("\n\nTo view keywords:")
        print("  python add_keywords.py show")
