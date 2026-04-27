import asyncio
from sqlalchemy.orm import Session
from models.database import SessionLocal, init_db, CrawlLog, Contact, DomainContact, ContactType, SearchResult, Keyword
from services.keyword_service import KeywordService
from services.serp_service import SerpService
from services.crawler_service import CrawlerService
from services.extraction_service import ExtractionService
from utils.state_manager import StateManager
from utils.robots_checker import RobotsChecker
from workers.db_task_queue import DatabaseTaskQueue
from config.settings import settings
from loguru import logger
from datetime import datetime
import time
from urllib.parse import urlparse
import sys
import traceback
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logger.remove()  # Удаляем handler по умолчанию

log_level = getattr(settings, 'LOG_LEVEL', 'INFO').upper()

if settings.LOG_FORMAT == "json":
    log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"
    logger.add(sys.stdout, format=log_format, serialize=True, level=log_level)
    logger.info("JSON logging enabled")
else:
    log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    logger.add(sys.stdout, format=log_format, level=log_level)

logger.info(f"Log level set to {log_level}")


class ContactMiningPipeline:
    def __init__(self):
        init_db()
        self.serp = SerpService()
        self.crawler = CrawlerService()
        self.extractor = ExtractionService()
        self.state_manager = StateManager()
        self.robots_checker = RobotsChecker()
        self.task_queue = None
    
    async def initialize(self):
        """Initialize async components"""
        self._run_preflight_checks()

        # Initialize database-backed task queue
        self.task_queue = DatabaseTaskQueue(max_concurrent=settings.MAX_CONCURRENT_DOMAINS)
        await self.task_queue.start_workers()
        
        try:
            from monitoring.healthcheck import task_queue as health_queue
            import monitoring.healthcheck as health_module
            health_module.task_queue = self.task_queue
            logger.info("Healthcheck API initialized with database task queue")
        except Exception as e:
            logger.warning(f"Failed to initialize healthcheck API: {e}")

    def _run_preflight_checks(self):
        """Validate critical external dependencies before queue startup."""
        try:
            # SERP configuration sanity
            provider = settings.SERP_API_PROVIDER
            if provider == "serpapi" and not settings.SERPAPI_KEY:
                logger.warning("Preflight: SERP provider is serpapi but SERPAPI_KEY is empty")
            elif provider == "duckduckgo":
                logger.info("Preflight: using DuckDuckGo provider (no API key required)")

            # LLM fallback readiness
            if settings.USE_LLM_EXTRACTION:
                llm_ready = False
                if settings.USE_YANDEXGPT:
                    llm_ready = bool(settings.YANDEX_IAM_TOKEN and settings.YANDEX_FOLDER_ID)
                    if not llm_ready:
                        logger.warning("Preflight: USE_YANDEXGPT=true but IAM/FOLDER config is incomplete")
                    elif settings.YANDEX_IAM_TOKEN.startswith("t1."):
                        logger.info("Preflight: YandexGPT token format looks valid")

                if settings.USE_DEEPSEEK and settings.DEEPSEEK_API_KEY:
                    llm_ready = True
                if settings.USE_OPENAI and settings.OPENAI_API_KEY:
                    llm_ready = True

                if not llm_ready:
                    logger.warning("Preflight: no ready LLM provider configured; fallback extraction may be disabled")
        except Exception as e:
            logger.warning(f"Preflight checks failed with non-fatal error: {e}")
    
    async def shutdown(self):
        """Cleanup resources"""
        if self.task_queue:
            await self.task_queue.stop_workers()
            logger.info("Task queue workers stopped")
    
    async def run_pipeline(self):
        """Main pipeline execution - Orchestrator mode (async parallel)"""
        logger.info("="*60)
        logger.info("Starting contact mining pipeline (ASYNC PARALLEL MODE)")
        logger.info("="*60)
        
        await self.initialize()
        
        # Создаем сессию для получения списка ключевых слов
        db = SessionLocal()
        try:
            keyword_service = KeywordService(db)
            self.state_manager.create_run()
            
            pending_keywords = keyword_service.get_pending_keywords(limit=settings.MAX_KEYWORDS_PER_RUN)
            logger.info(f"Found {len(pending_keywords)} pending keywords")
            
            if not pending_keywords:
                logger.info("No pending keywords to process")
                return
            
            # Add search tasks for all keywords to the queue
            logger.info(f"\n📤 Adding {len(pending_keywords)} search tasks to queue...")
            for idx, keyword in enumerate(pending_keywords, 1):
                await self.task_queue.add_task(
                    task_name=f"search_{keyword.id}",
                    task_type='search_keyword',
                    payload={
                        'keyword_id': keyword.id,
                        'keyword': keyword.keyword,
                        'language': keyword.language,
                        'country': keyword.country
                    },
                    priority=10,  # High priority for search tasks
                    keyword_id=keyword.id
                )
                logger.info(f"   [{idx}/{len(pending_keywords)}] Added search task for: {keyword.keyword}")
            
            logger.info(f"\n✅ All search tasks added to queue. Workers will process them automatically.")
            logger.info(f"   Queue stats: {await self.task_queue.get_queue_stats()}")
            
            # Wait for all tasks to complete
            await self._wait_for_completion(pending_keywords)
            
            logger.info(f"\n🎉 Pipeline completed successfully!")
        
        finally:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"Non-critical error closing DB session: {e}")
            await self.shutdown()
    
    async def _wait_for_completion(self, keywords: list, timeout_hours: int = 2):
        """Wait for all tasks to complete with progress monitoring"""
        import time
        start_time = time.time()
        timeout_seconds = timeout_hours * 3600
        
        logger.info(f"\n⏳ Waiting for tasks to complete (timeout: {timeout_hours}h)...")
        
        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logger.error(f"❌ Pipeline timeout after {elapsed/3600:.1f} hours")
                break
            
            # Get queue stats
            stats = await self.task_queue.get_queue_stats()
            
            # Check if stats is valid (handle DB errors)
            if not stats:
                logger.warning("Failed to get queue stats, retrying in 5s...")
                await asyncio.sleep(5)
                continue
            
            # Check if all tasks completed
            if stats.get('pending', 0) == 0 and stats.get('running', 0) == 0:
                logger.info(f"\n✅ All tasks completed!")
                logger.info(f"   Total: {stats['total']} tasks")
                logger.info(f"   Completed: {stats['completed']}")
                logger.info(f"   Failed: {stats['failed']}")
                break

            zero_page_crawls = stats.get('zero_page_crawls_24h', 0)
            if zero_page_crawls >= settings.ZERO_PAGE_CRAWLS_ALERT_THRESHOLD:
                logger.warning(
                    f"⚠️ High zero-page crawl rate: {zero_page_crawls} domains in last 24h with pages_crawled=0"
                )
            timeout_rate = stats.get('timeout_rate_24h', 0.0)
            if timeout_rate >= settings.TIMEOUT_RATE_ALERT_THRESHOLD_PCT:
                logger.warning(
                    f"⚠️ High timeout rate: {timeout_rate}% in last 24h "
                    f"(threshold={settings.TIMEOUT_RATE_ALERT_THRESHOLD_PCT}%)"
                )
            contacts_rate = stats.get('domains_with_contacts_rate_24h', 0.0)
            if contacts_rate <= settings.CONTACTS_RATE_ALERT_THRESHOLD_PCT:
                logger.warning(
                    f"⚠️ Low contacts yield: {contacts_rate}% domains with contacts in last 24h "
                    f"(threshold={settings.CONTACTS_RATE_ALERT_THRESHOLD_PCT}%)"
                )
            avg_contacts_per_domain = stats.get('avg_contacts_per_domain_24h', 0.0)
            if avg_contacts_per_domain <= settings.AVG_CONTACTS_PER_DOMAIN_ALERT_THRESHOLD:
                logger.warning(
                    f"⚠️ Low contact density: avg={avg_contacts_per_domain} contacts/domain in last 24h "
                    f"(threshold={settings.AVG_CONTACTS_PER_DOMAIN_ALERT_THRESHOLD})"
                )
            
            # Log progress every 30 seconds
            logger.info(
                f"📊 Queue Status: {stats.get('pending', 0)} pending | "
                f"{stats.get('running', 0)} running | "
                f"{stats.get('completed', 0)} completed | "
                f"{stats.get('failed', 0)} failed | "
                f"{stats.get('keywords_in_progress', 0)} keywords in progress | "
                f"{stats.get('zero_page_crawls_24h', 0)} zero-page crawls/24h | "
                f"{stats.get('timeout_rate_24h', 0.0)}% timeout rate/24h | "
                f"{stats.get('domains_with_contacts_rate_24h', 0.0)}% domains with contacts/24h"
            )
            
            await asyncio.sleep(30)
    
    async def _process_keyword(self, db: Session, keyword_service: KeywordService, keyword) -> dict:
        """Process a single keyword with error handling and retry"""
        logger.info(f"Processing keyword: {keyword.keyword} ({keyword.language})")
        
        websites_processed = 0
        contacts_found = 0
        
        try:
            # Retry search if it fails
            search_results, raw_response = await self._retry_search(keyword)
            
            if not search_results:
                logger.warning(f"No search results for keyword: {keyword.keyword}")
                keyword_service.mark_as_processed(keyword.id)
                return {"websites": 0, "contacts": 0}
            
            # Save search results with retry
            raw_query = f"{keyword.keyword} site:{keyword.country}" if keyword.country else keyword.keyword
            await self._retry_save_results(db, keyword.id, search_results, raw_query, raw_response)
            
            # Process each search result
            for idx, result in enumerate(search_results[:settings.SEARCH_RESULTS_PER_KEYWORD], 1):
                try:
                    logger.info(f"[{idx}/{settings.SEARCH_RESULTS_PER_KEYWORD}] Processing: {result['url'][:70]}")
                    
                    if not self.robots_checker.can_fetch(result["url"]):
                        logger.info(f"Skipping (robots.txt): {result['url'][:70]}")
                        continue
                    
                    contacts = await self._process_search_result(db, result)
                    if contacts:
                        contacts_found += len(contacts.emails) + len(contacts.telegram_links)
                    
                    websites_processed += 1
                    logger.info(f"✓ Completed [{idx}/{settings.SEARCH_RESULTS_PER_KEYWORD}]: {result['url'][:50]}...")
                    
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
            except Exception:
                pass
            
            # Return partial results
            return {"websites": websites_processed, "contacts": contacts_found}
        
        return {"websites": websites_processed, "contacts": contacts_found}
    
    async def _retry_search(self, keyword, max_retries=3):
        """Search with retry logic
        Returns: (search_results, raw_response)
        """
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Searching (attempt {attempt}/{max_retries})...")
                search_results, raw_response = self.serp.search(
                    query=keyword.keyword,
                    country=keyword.country,
                    language=keyword.language,
                    num_results=settings.SEARCH_RESULTS_PER_KEYWORD
                )
                logger.info(f"✓ Search successful: {len(search_results)} results")
                return search_results, raw_response
            except Exception as e:
                logger.warning(f"Search attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ Search failed after {max_retries} attempts")
                    return [], None
    
    async def _retry_save_results(self, db, keyword_id, search_results, raw_query=None, raw_response=None, max_retries=3):
        """Save search results with retry logic"""
        for attempt in range(1, max_retries + 1):
            try:
                self.serp.save_results(db, keyword_id, search_results, raw_query, raw_response)
                logger.info(f"✓ Saved {len(search_results)} search results")
                return
            except Exception as e:
                logger.warning(f"Save attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    # Try to recreate DB session
                    try:
                        db.close()
                    except Exception:
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
            crawl_data = await self.crawler.crawl_domain(url)
            
            if crawl_data.get("skipped"):
                return None
            
            contacts, llm_data = self.extractor.extract_contacts(crawl_data["content"])
            
            if contacts.emails:
                mx_results = await self.extractor.batch_verify_emails(contacts.emails)
                verified_emails = [email for email, valid in mx_results.items() if valid]
                logger.info(f"MX verification: {len(verified_emails)}/{len(contacts.emails)} emails valid")
            
            if contacts.emails or contacts.telegram_links or contacts.linkedin_links:
                domain = urlparse(url).netloc
                
                sr = db.query(SearchResult).filter(SearchResult.url == url).first()
                
                if sr:
                    # Determine tags (hybrid approach: keyword + LLM classification)
                    tags = []
                    try:
                        # 1. Get keyword text as base tag
                        keyword_obj = db.query(Keyword).filter(Keyword.id == sr.keyword_id).first()
                        if keyword_obj:
                            tags.append(keyword_obj.keyword)
                            logger.info(f"Added keyword as tag: {keyword_obj.keyword}")
                        
                        # 2. Use LLM to classify domain category (if enabled)
                        if settings.USE_LLM_EXTRACTION and crawl_data.get("content"):
                            combined_content = "\n\n".join([
                                item.get("content", "")[:1000] 
                                for item in crawl_data["content"][:3]
                            ])
                            
                            llm_categories = self.extractor.classify_domain_category(
                                combined_content, 
                                keyword=keyword_obj.keyword if keyword_obj else ""
                            )
                            
                            for category in llm_categories:
                                if category.lower() not in [t.lower() for t in tags]:
                                    tags.append(category)
                            
                            logger.info(f"Final tags for {domain}: {tags}")
                    except Exception as e:
                        logger.warning(f"Failed to determine tags for {domain}: {e}")
                        if keyword_obj:
                            tags = [keyword_obj.keyword]
                    
                    # Prepare contacts_json for hybrid approach
                    contacts_data = {
                        "emails": contacts.emails,
                        "telegram": contacts.telegram_links,
                        "linkedin": contacts.linkedin_links,
                        "phones": contacts.phone_numbers if hasattr(contacts, 'phone_numbers') else [],
                        "social": contacts.social_links if hasattr(contacts, 'social_links') else {}
                    }
                    
                    domain_contact = DomainContact(
                        search_result_id=sr.id,
                        domain=domain,
                        tags=tags,  # ← Hybrid tags: keyword + LLM categories
                        contacts_json=contacts_data,  # Hybrid: JSON for fast read
                        confidence_score=self.extractor.calculate_confidence(contacts),
                        extraction_method="llm" if settings.USE_LLM_EXTRACTION else "regex"
                    )
                    db.add(domain_contact)
                    db.flush()
                    
                    # Also save to normalized table for search
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

                    for platform, links in (contacts.social_links or {}).items():
                        contact_type_map = {
                            "x": ContactType.X,
                            "facebook": ContactType.FACEBOOK,
                            "instagram": ContactType.INSTAGRAM,
                            "youtube": ContactType.YOUTUBE,
                        }
                        mapped_type = contact_type_map.get(platform)
                        if not mapped_type:
                            continue
                        for link in links:
                            contact = Contact(
                                domain_contact_id=domain_contact.id,
                                contact_type=mapped_type,
                                value=link
                            )
                            db.add(contact)
                    
                    db.commit()
                    
                    total_social = sum(len(v) for v in (contacts.social_links or {}).values())
                    logger.info(f"Saved contacts for {domain}: {len(contacts.emails)} emails, "
                              f"{len(contacts.telegram_links)} Telegram, {len(contacts.linkedin_links)} LinkedIn, "
                              f"{total_social} social")
                    
                    return contacts
            
            duration = int(time.time() - start_time)
            crawl_log = CrawlLog(
                domain=crawl_data["domain"],
                url=url,
                status_code=200,
                pages_crawled=crawl_data["pages_crawled"],
                duration_seconds=duration,
                llm_request=llm_data.get("request") if llm_data else None,
                llm_response=llm_data.get("response") if llm_data else None,
                llm_model=llm_data.get("model") if llm_data else None
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
                # llm_data not available on error
            )
            db.add(crawl_log)
            db.commit()
        
        return None


async def main():
    pipeline = ContactMiningPipeline()
    await pipeline.run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
