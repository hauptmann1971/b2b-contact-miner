import asyncio
import redis.asyncio as redis
from sqlalchemy.orm import Session
from models.database import SessionLocal, init_db, CrawlLog, Contact, DomainContact, ContactType, SearchResult
from services.keyword_service import KeywordService
from services.serp_service import SerpService
from services.crawler_service import CrawlerService
from services.extraction_service import ExtractionService
from utils.state_manager import StateManager
from utils.robots_checker import RobotsChecker
from workers.task_worker import AsyncTaskQueue
from config.settings import settings
from loguru import logger
from datetime import datetime
import time
from urllib.parse import urlparse
import sys
import traceback
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging format
if settings.LOG_FORMAT == "json":
    logger.remove()
    logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}", serialize=True)
    logger.info("JSON logging enabled")


class ContactMiningPipeline:
    def __init__(self):
        init_db()
        self.serp = SerpService()
        self.crawler = CrawlerService()
        self.extractor = ExtractionService()
        self.state_manager = StateManager()
        self.robots_checker = RobotsChecker()
        self.redis_client = None
        self.task_queue = None
    
    async def initialize(self):
        """Initialize async components"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Redis not available, falling back to in-memory deduplication: {e}")
            self.redis_client = None
        
        self.task_queue = AsyncTaskQueue(max_concurrent=settings.MAX_CONCURRENT_DOMAINS)
        await self.task_queue.start_workers()
        
        try:
            from monitoring.healthcheck import redis_client as health_redis, task_queue as health_queue
            import monitoring.healthcheck as health_module
            health_module.redis_client = self.redis_client
            health_module.task_queue = self.task_queue
            logger.info("Healthcheck API initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize healthcheck API: {e}")
    
    async def shutdown(self):
        """Cleanup resources"""
        if self.task_queue:
            await self.task_queue.stop_workers()
        if self.redis_client:
            await self.redis_client.close()
    
    async def run_pipeline(self):
        """Main pipeline execution"""
        logger.info("="*60)
        logger.info("Starting contact mining pipeline")
        logger.info("="*60)
        
        await self.initialize()
        
        db = SessionLocal()
        try:
            keyword_service = KeywordService(db)
            self.state_manager.create_run()
            
            pending_keywords = keyword_service.get_pending_keywords(limit=50)
            logger.info(f"Found {len(pending_keywords)} pending keywords")
            
            if not pending_keywords:
                logger.info("No pending keywords to process")
                return
            
            total_websites = len(pending_keywords) * 5
            websites_processed = 0
            contacts_found = 0
            
            for idx, keyword in enumerate(pending_keywords, 1):
                try:
                    logger.info(f"\n{'='*80}")
                    logger.info(f"Processing keyword [{idx}/{len(pending_keywords)}]: {keyword.keyword}")
                    logger.info(f"{'='*80}")
                    
                    result = await self._process_keyword(db, keyword_service, keyword)
                    websites_processed += result.get("websites", 0)
                    contacts_found += result.get("contacts", 0)
                    
                    logger.info(f"\n📊 Progress: {idx}/{len(pending_keywords)} keywords")
                    logger.info(f"   Total websites: {websites_processed}")
                    logger.info(f"   Total contacts: {contacts_found}")
                    
                    # Update progress with retry
                    try:
                        self.state_manager.update_progress(
                            keyword.id, 
                            websites_processed, 
                            contacts_found,
                            total_websites
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update progress: {e}")
                    
                except KeyboardInterrupt:
                    logger.warning("\n⚠️  Pipeline interrupted by user")
                    break
                except Exception as e:
                    logger.error(f"\n❌ Unexpected error processing keyword {keyword.id}: {e}")
                    logger.debug(traceback.format_exc())
                    
                    # Mark as failed but continue with next keyword
                    try:
                        self.state_manager.mark_failed(keyword.id, str(e))
                    except:
                        pass
                    
                    # Continue with next keyword instead of crashing
                    logger.info("Continuing with next keyword...")
                    continue
            
            logger.info(f"Pipeline completed: {websites_processed} websites, {contacts_found} contacts")
        
        finally:
            db.close()
            await self.shutdown()
    
    async def _process_keyword(self, db: Session, keyword_service: KeywordService, keyword) -> dict:
        """Process a single keyword with error handling and retry"""
        logger.info(f"Processing keyword: {keyword.keyword} ({keyword.language})")
        
        websites_processed = 0
        contacts_found = 0
        
        try:
            # Retry search if it fails
            search_results = await self._retry_search(keyword)
            
            if not search_results:
                logger.warning(f"No search results for keyword: {keyword.keyword}")
                keyword_service.mark_as_processed(keyword.id)
                return {"websites": 0, "contacts": 0}
            
            # Save search results with retry
            await self._retry_save_results(db, keyword.id, search_results)
            
            # Process each search result
            for idx, result in enumerate(search_results[:5], 1):
                try:
                    logger.info(f"[{idx}/5] Processing: {result['url'][:70]}")
                    
                    if not self.robots_checker.can_fetch(result["url"]):
                        logger.info(f"Skipping (robots.txt): {result['url'][:70]}")
                        continue
                    
                    contacts = await self._process_search_result(db, result)
                    if contacts:
                        contacts_found += len(contacts.emails) + len(contacts.telegram_links)
                    
                    websites_processed += 1
                    logger.info(f"✓ Completed [{idx}/5]: {result['url'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"✗ Error processing URL {result['url']}: {e}")
                    logger.debug(traceback.format_exc())
                    # Continue with next URL instead of failing entire keyword
                    continue
            
            # Mark as processed even if some URLs failed
            try:
                keyword_service.mark_as_processed(keyword.id)
                self.state_manager.mark_keyword_completed(keyword.id, contacts_found)
                logger.info(f"✅ Keyword completed: {websites_processed} websites, {contacts_found} contacts")
            except Exception as e:
                logger.error(f"Failed to mark keyword as processed: {e}")
                # Don't raise - keyword was still processed
            
        except Exception as e:
            logger.error(f"❌ Keyword processing failed: {keyword.keyword}")
            logger.error(f"Error: {e}")
            logger.debug(traceback.format_exc())
            
            # Mark as failed but don't crash the pipeline
            try:
                self.state_manager.mark_failed(keyword.id, str(e))
            except:
                pass
            
            # Return partial results
            return {"websites": websites_processed, "contacts": contacts_found}
        
        return {"websites": websites_processed, "contacts": contacts_found}
    
    async def _retry_search(self, keyword, max_retries=3):
        """Search with retry logic"""
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Searching (attempt {attempt}/{max_retries})...")
                search_results = self.serp.search(
                    query=keyword.keyword,
                    country=keyword.country,
                    language=keyword.language,
                    num_results=10
                )
                logger.info(f"✓ Search successful: {len(search_results)} results")
                return search_results
            except Exception as e:
                logger.warning(f"Search attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ Search failed after {max_retries} attempts")
                    return []
    
    async def _retry_save_results(self, db, keyword_id, search_results, max_retries=3):
        """Save search results with retry logic"""
        for attempt in range(1, max_retries + 1):
            try:
                self.serp.save_results(db, keyword_id, search_results)
                logger.info(f"✓ Saved {len(search_results)} search results")
                return
            except Exception as e:
                logger.warning(f"Save attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    # Try to recreate DB session
                    try:
                        db.close()
                    except:
                        pass
                    db = SessionLocal()
                    
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ Failed to save results after {max_retries} attempts")
                    # Don't raise - continue with crawling even if save failed
    
    async def _process_search_result(self, db: Session, search_result: dict):
        """Crawl and extract contacts"""
        url = search_result["url"]
        logger.info(f"Crawling: {url}")
        
        start_time = time.time()
        
        try:
            crawl_data = await self.crawler.crawl_domain(url, self.redis_client)
            
            if crawl_data.get("skipped"):
                return None
            
            contacts = self.extractor.extract_contacts(crawl_data["content"])
            
            if contacts.emails:
                mx_results = await self.extractor.batch_verify_emails(contacts.emails)
                verified_emails = [email for email, valid in mx_results.items() if valid]
                logger.info(f"MX verification: {len(verified_emails)}/{len(contacts.emails)} emails valid")
            
            if contacts.emails or contacts.telegram_links or contacts.linkedin_links:
                domain = urlparse(url).netloc
                
                sr = db.query(SearchResult).filter(SearchResult.url == url).first()
                
                if sr:
                    domain_contact = DomainContact(
                        search_result_id=sr.id,
                        domain=domain,
                        tags=[],
                        confidence_score=self.extractor.calculate_confidence(contacts),
                        extraction_method="llm" if settings.USE_LLM_EXTRACTION else "regex"
                    )
                    db.add(domain_contact)
                    db.flush()
                    
                    for email in contacts.emails:
                        contact = Contact(
                            domain_contact_id=domain_contact.id,
                            contact_type=ContactType.EMAIL,
                            value=email
                        )
                        db.add(contact)
                    
                    for tg in contacts.telegram_links:
                        contact = Contact(
                            domain_contact_id=domain_contact.id,
                            contact_type=ContactType.TELEGRAM,
                            value=tg
                        )
                        db.add(contact)
                    
                    for li in contacts.linkedin_links:
                        contact = Contact(
                            domain_contact_id=domain_contact.id,
                            contact_type=ContactType.LINKEDIN,
                            value=li
                        )
                        db.add(contact)
                    
                    db.commit()
                    
                    logger.info(f"Saved contacts for {domain}: {len(contacts.emails)} emails, "
                              f"{len(contacts.telegram_links)} Telegram, {len(contacts.linkedin_links)} LinkedIn")
                    
                    return contacts
            
            duration = int(time.time() - start_time)
            crawl_log = CrawlLog(
                domain=crawl_data["domain"],
                url=url,
                status_code=200,
                pages_crawled=crawl_data["pages_crawled"],
                duration_seconds=duration
            )
            db.add(crawl_log)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to process {url}: {e}")
            crawl_log = CrawlLog(
                domain=urlparse(url).netloc,
                url=url,
                status_code=0,
                error_message=str(e),
                duration_seconds=int(time.time() - start_time)
            )
            db.add(crawl_log)
            db.commit()
        
        return None


async def main():
    pipeline = ContactMiningPipeline()
    await pipeline.run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
