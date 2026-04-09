"""
Test pipeline with a single keyword
Quick test to verify the full pipeline works
"""
import asyncio
from sqlalchemy.orm import Session
from models.database import SessionLocal, init_db, Keyword
from services.keyword_service import KeywordService
from services.serp_service import SerpService
from services.crawler_service import CrawlerService
from services.extraction_service import ExtractionService
from utils.robots_checker import RobotsChecker
from config.settings import settings
from loguru import logger


async def test_single_keyword(keyword_id: int = None):
    """Test pipeline with one keyword"""
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    try:
        # Get keyword or use first pending
        if keyword_id:
            keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
            if not keyword:
                print(f"❌ Keyword ID {keyword_id} not found!")
                return
        else:
            keyword_service = KeywordService(db)
            pending = keyword_service.get_pending_keywords(limit=1)
            if not pending:
                print("❌ No pending keywords found!")
                print("\nAdd keywords first:")
                print("  python add_keywords.py")
                return
            keyword = pending[0]
        
        print("="*70)
        print(f"Testing Pipeline with Single Keyword")
        print("="*70)
        print(f"\nKeyword: '{keyword.keyword}'")
        print(f"Language: {keyword.language}")
        print(f"Country: {keyword.country}")
        print(f"ID: {keyword.id}")
        print("="*70)
        
        # Initialize services
        print("\n1. Initializing services...")
        serp = SerpService()
        crawler = CrawlerService()
        extractor = ExtractionService()
        robots_checker = RobotsChecker()
        print("   ✅ Services initialized")
        
        # Step 1: Search
        print(f"\n2. Searching for '{keyword.keyword}'...")
        search_results = serp.search(
            query=keyword.keyword,
            country=keyword.country,
            language=keyword.language,
            num_results=3  # Just 3 for quick test
        )
        
        print(f"   ✅ Found {len(search_results)} results")
        
        if not search_results:
            print("\n⚠️  No search results found!")
            return
        
        # Show results
        print("\n   Search Results:")
        for i, result in enumerate(search_results, 1):
            print(f"   {i}. {result['title'][:60]}")
            print(f"      {result['url'][:70]}")
        
        # Save results
        serp.save_results(db, keyword.id, search_results)
        print(f"\n   ✅ Saved {len(search_results)} results to database")
        
        # Refresh keyword object to avoid stale connection issues
        db.refresh(keyword)
        
        # Step 2: Crawl and extract
        print(f"\n3. Crawling websites...")
        contacts_found = 0
        
        for idx, result in enumerate(search_results[:2], 1):  # Just first 2 for quick test
            url = result["url"]
            print(f"\n   [{idx}/{min(2, len(search_results))}] Processing: {url[:70]}")
            
            # Check robots.txt
            if not robots_checker.can_fetch(url):
                print(f"       ⚠️  Skipped (robots.txt)")
                continue
            
            try:
                # Crawl
                print(f"       🕷️  Crawling...")
                crawl_data = await crawler.crawl_domain(url, redis_client=None)
                
                if crawl_data.get("skipped"):
                    print(f"       ⚠️  Skipped (already crawled)")
                    continue
                
                pages_crawled = crawl_data.get("pages_crawled", 0)
                print(f"       ✅ Crawled {pages_crawled} pages")
                
                # Extract contacts
                print(f"       📧 Extracting contacts...")
                contacts = extractor.extract_contacts(crawl_data["content"])
                
                email_count = len(contacts.emails)
                telegram_count = len(contacts.telegram_links)
                linkedin_count = len(contacts.linkedin_links)
                
                if email_count > 0 or telegram_count > 0 or linkedin_count > 0:
                    print(f"       ✅ Found: {email_count} emails, {telegram_count} Telegram, {linkedin_count} LinkedIn")
                    
                    # Verify emails
                    if contacts.emails:
                        print(f"       ✓ Verifying emails...")
                        mx_results = await extractor.batch_verify_emails(contacts.emails)
                        verified = [e for e, v in mx_results.items() if v]
                        print(f"       ✓ Verified: {len(verified)}/{len(contacts.emails)} emails")
                    
                    contacts_found += email_count + telegram_count + linkedin_count
                    
                    # Print details
                    if contacts.emails:
                        print(f"       📧 Emails: {', '.join(contacts.emails[:3])}")
                    if contacts.telegram_links:
                        print(f"       ✈️  Telegram: {', '.join(contacts.telegram_links[:2])}")
                    if contacts.linkedin_links:
                        print(f"       💼 LinkedIn: {', '.join(contacts.linkedin_links[:2])}")
                else:
                    print(f"       ⚠️  No contacts found")
                
            except Exception as e:
                print(f"       ❌ Error: {e}")
                continue
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Keyword: '{keyword.keyword}'")
        print(f"Websites processed: {min(2, len(search_results))}")
        print(f"Total contacts found: {contacts_found}")
        print("="*70)
        
        if contacts_found > 0:
            print("\n✅ TEST SUCCESSFUL! Pipeline is working correctly.")
        else:
            print("\n⚠️  Test completed but no contacts found.")
            print("   This might be normal - depends on the websites.")
        
        print("\nTo run full pipeline:")
        print("  python main.py")
        
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    # Get keyword ID from command line or use first pending
    keyword_id = None
    if len(sys.argv) > 1:
        try:
            keyword_id = int(sys.argv[1])
        except ValueError:
            print(f"Invalid keyword ID: {sys.argv[1]}")
            sys.exit(1)
    
    asyncio.run(test_single_keyword(keyword_id))
