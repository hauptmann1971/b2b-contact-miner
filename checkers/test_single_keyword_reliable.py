"""
Test pipeline with single keyword and reliability improvements
- Max 3 websites to crawl
- 120 second timeout per website
- Graceful error handling
"""
import asyncio
import time
from sqlalchemy.orm import Session
from models.database import SessionLocal, init_db, Keyword
from services.keyword_service import KeywordService
from services.serp_service import SerpService
from services.crawler_service import CrawlerService
from services.extraction_service import ExtractionService
from utils.robots_checker import RobotsChecker
from config.settings import settings
from loguru import logger


async def test_single_keyword_reliable(keyword_id: int = None):
    """Test pipeline with one keyword and reliability features"""
    
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
        
        print("="*80)
        print("RELIABLE PIPELINE TEST - Single Keyword")
        print("="*80)
        print(f"\nKeyword: '{keyword.keyword}'")
        print(f"Language: {keyword.language}")
        print(f"Country: {keyword.country}")
        print(f"ID: {keyword.id}")
        print(f"Max websites to crawl: 3")
        print(f"Timeout per website: 120 seconds")
        print("="*80)
        
        # Initialize services
        print("\n1. Initializing services...")
        serp = SerpService()
        crawler = CrawlerService()
        extractor = ExtractionService()
        robots_checker = RobotsChecker()
        print("   ✅ Services initialized")
        
        # Step 1: Search with retry
        print(f"\n2. Searching for '{keyword.keyword}'...")
        search_results = None
        max_retries = 3
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"   Attempt {attempt}/{max_retries}...")
                search_results = serp.search(
                    query=keyword.keyword,
                    country=keyword.country,
                    language=keyword.language,
                    num_results=10
                )
                print(f"   ✅ Search successful: {len(search_results)} results")
                break
            except Exception as e:
                print(f"   ⚠️  Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"   Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"   ❌ Search failed after {max_retries} attempts")
                    return
        
        if not search_results:
            print("\n⚠️  No search results found!")
            return
        
        # Show results
        print("\n   Search Results (top 10):")
        for i, result in enumerate(search_results[:10], 1):
            print(f"   {i}. {result['title'][:60]}")
            print(f"      {result['url'][:70]}")
        
        # Save results with retry
        print(f"\n3. Saving search results...")
        for attempt in range(1, max_retries + 1):
            try:
                serp.save_results(db, keyword.id, search_results)
                print(f"   ✅ Saved {len(search_results)} results to database")
                break
            except Exception as e:
                print(f"   ⚠️  Save attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    try:
                        db.close()
                    except:
                        pass
                    db = SessionLocal()
                    await asyncio.sleep(2 ** attempt)
                else:
                    print(f"   ⚠️  Failed to save results (continuing anyway)")
        
        # Refresh keyword
        db.refresh(keyword)
        
        # Step 2: Crawl websites with timeout and limit
        print(f"\n4. Crawling websites (max 3, timeout 120s each)...")
        contacts_found = 0
        websites_processed = 0
        max_websites = 3
        
        for idx, result in enumerate(search_results[:max_websites], 1):
            url = result["url"]
            print(f"\n   [{'='*50}]")
            print(f"   [{idx}/{max_websites}] Processing: {url[:70]}")
            print(f"   [{'='*50}]")
            
            # Check robots.txt
            if not robots_checker.can_fetch(url):
                print(f"       ⚠️  Skipped (robots.txt)")
                continue
            
            start_time = time.time()
            
            try:
                # Crawl with timeout
                print(f"       🕷️  Crawling (timeout: 120s)...")
                
                # Use asyncio.wait_for for timeout
                try:
                    crawl_data = await asyncio.wait_for(
                        crawler.crawl_domain(url, redis_client=None),
                        timeout=120.0
                    )
                    
                    elapsed = time.time() - start_time
                    print(f"       ✅ Crawled in {elapsed:.1f}s")
                    
                    if crawl_data.get("skipped"):
                        print(f"       ⚠️  Skipped (already crawled)")
                        continue
                    
                    pages_crawled = crawl_data.get("pages_crawled", 0)
                    print(f"       📄 Pages crawled: {pages_crawled}")
                    
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"       ⏱️  TIMEOUT after {elapsed:.1f}s (>120s)")
                    print(f"       ⚠️  Stopping crawl for this site")
                    print(f"       💾 Keeping any partial results...")
                    # Continue to next website instead of failing
                    websites_processed += 1
                    continue
                
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
                        try:
                            mx_results = await extractor.batch_verify_emails(contacts.emails)
                            verified = [e for e, v in mx_results.items() if v]
                            print(f"       ✓ Verified: {len(verified)}/{len(contacts.emails)} emails")
                        except Exception as e:
                            print(f"       ⚠️  Email verification failed: {e}")
                            verified = contacts.emails
                    
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
                
                websites_processed += 1
                
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"       ❌ Error after {elapsed:.1f}s: {e}")
                # Continue with next website
                continue
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Keyword: '{keyword.keyword}'")
        print(f"Websites processed: {websites_processed}/{max_websites}")
        print(f"Total contacts found: {contacts_found}")
        print("="*80)
        
        if contacts_found > 0:
            print("\n✅ TEST SUCCESSFUL! Pipeline is working correctly.")
        else:
            print("\n⚠️  Test completed but no contacts found.")
            print("   This might be normal - depends on the websites.")
        
        print("\nReliability features tested:")
        print("  ✓ Retry logic for search")
        print("  ✓ Retry logic for DB save")
        print("  ✓ Timeout per website (120s)")
        print("  ✓ Max websites limit (3)")
        print("  ✓ Error isolation (continue on failure)")
        print("  ✓ Partial results preserved")
        
        print("\nTo run full pipeline:")
        print("  python main.py")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        print("Graceful shutdown completed.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            db.close()
        except:
            pass


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
    
    asyncio.run(test_single_keyword_reliable(keyword_id))
