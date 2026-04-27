"""Database-backed task queue service with async parallel processing"""
import json
import asyncio
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from loguru import logger
from models.database import SessionLocal, SearchResult, DomainContact, Contact, ContactType, CrawlLog, Keyword
from models.task_queue import TaskQueue
from config.settings import settings
from services.serp_service import SerpService
from services.crawler_service import CrawlerService
from services.extraction_service import ExtractionService
from urllib.parse import urlparse


class DatabaseTaskQueue:
    """Persistent task queue using MySQL database instead of Redis"""
    
    def __init__(self, max_concurrent: int = 20, lock_timeout: int = None):
        self.max_concurrent = max_concurrent
        self.lock_timeout = lock_timeout or settings.TASK_LOCK_TIMEOUT  # seconds before lock expires
        self.running = False
        self.workers = []
        self.current_tasks = 0
        self.tasks_semaphore = asyncio.Semaphore(max_concurrent)
        
        # Initialize services (lazy loading to avoid circular imports)
        self._serp_service = None
        self._crawler_service = None
        self._extraction_service = None
    
    @staticmethod
    def _safe_close_db(db: Session):
        """Safely close database session without raising errors"""
        try:
            db.close()
        except Exception as e:
            logger.debug(f"Non-critical error closing DB session: {e}")
    
    def _get_serp_service(self):
        """Lazy load SerpService"""
        if self._serp_service is None:
            self._serp_service = SerpService()
        return self._serp_service
    
    def _get_crawler_service(self):
        """Lazy load CrawlerService"""
        if self._crawler_service is None:
            self._crawler_service = CrawlerService()
        return self._crawler_service
    
    def _get_extraction_service(self):
        """Lazy load ExtractionService"""
        if self._extraction_service is None:
            self._extraction_service = ExtractionService()
        return self._extraction_service

    @staticmethod
    def _root_url(url: str) -> str:
        """Convert a SERP result URL to domain root."""
        parsed = urlparse(url)
        if not parsed.scheme:
            return f"https://{parsed.netloc}/" if parsed.netloc else f"https://{url.strip('/')}/"
        return f"{parsed.scheme}://{parsed.netloc}/"

    @staticmethod
    def _needs_domain_fallback(url: str) -> bool:
        """Heuristic: article/news-like URLs benefit from root-domain crawl."""
        parsed = urlparse(url)
        path = (parsed.path or "").lower()
        article_markers = ["/news/", "/article", "/press", "/blog/", "/post/", ".html", ".htm"]
        return len(path) > 1 and any(marker in path for marker in article_markers)
    
    async def start_workers(self):
        """Start worker tasks and recover stale tasks"""
        # Recover any stale tasks from previous crashes
        recovered = await self.recover_stale_tasks()
        if recovered > 0:
            logger.info(f"Recovered {recovered} stale tasks before starting workers")
        
        self.running = True
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        logger.info(f"Started {self.max_concurrent} database-backed workers")
    
    async def stop_workers(self):
        """Stop all workers gracefully"""
        self.running = False
        
        for worker in self.workers:
            worker.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("All database workers stopped")
    
    async def add_task(self, task_name: str, task_type: str, payload: Dict, 
                      priority: int = 0, max_retries: int = None,
                      keyword_id: int = None, depends_on_task_id: int = None,
                      scheduled_for: Optional[datetime] = None):
        """Add task to database queue
        
        Args:
            task_name: Human-readable task name
            task_type: Type of task (search_keyword, crawl_domain, extract_contacts, save_results)
            payload: Task data as dict (will be JSON serialized)
            priority: Priority level (higher = more important)
            max_retries: Max retry attempts (uses settings default if None)
            keyword_id: Associated keyword ID for tracking
            depends_on_task_id: Parent task ID (task won't run until parent completes)
            scheduled_for: Delayed execution time
        """
        # Set default max_retries based on task type
        if max_retries is None:
            retry_map = {
                'search_keyword': settings.SEARCH_MAX_RETRIES,
                'crawl_domain': settings.CRAWL_MAX_RETRIES,
                'extract_contacts': settings.EXTRACT_MAX_RETRIES,
                'save_results': settings.SAVE_MAX_RETRIES,
            }
            max_retries = retry_map.get(task_type, 3)
        
        try:
            db = SessionLocal()
            task = TaskQueue(
                task_name=task_name,
                task_type=task_type,
                payload=json.dumps(payload),
                priority=priority,
                max_retries=max_retries,
                keyword_id=keyword_id,
                depends_on_task_id=depends_on_task_id,
                scheduled_for=scheduled_for,
                status='pending'
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            logger.debug(f"Task added to DB queue: {task.id} ({task_type}) [priority={priority}, keyword={keyword_id}]")
            return task.id
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add task to DB: {e}")
            raise
        finally:
            self._safe_close_db(db)
    
    async def _worker(self, worker_id: int):
        """Worker that processes tasks from database"""
        worker_name = f"db-worker-{worker_id}"
        
        while self.running:
            try:
                # Try to acquire semaphore (limits concurrent tasks)
                await asyncio.wait_for(self.tasks_semaphore.acquire(), timeout=2.0)
                
                # Fetch next pending task
                task = await self._fetch_next_task(worker_name)
                
                if task:
                    self.current_tasks += 1
                    try:
                        # Execute the task
                        await self._execute_task(task, worker_name)
                    except Exception as e:
                        logger.error(f"Worker {worker_id} task {task.id} failed: {e}")
                        await self._handle_task_failure(task.id, str(e))
                    finally:
                        self.current_tasks -= 1
                        self.tasks_semaphore.release()
                else:
                    # No tasks available, release semaphore and wait
                    self.tasks_semaphore.release()
                    await asyncio.sleep(1)
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
    
    async def _fetch_next_task(self, worker_name: str) -> Optional[TaskQueue]:
        """Fetch next pending task and lock it (respects dependencies)"""
        db = None
        try:
            db = SessionLocal()
            
            # Find next pending task (ordered by priority DESC, created_at ASC)
            now = datetime.now(timezone.utc)
            tasks = db.query(TaskQueue).filter(
                TaskQueue.status == 'pending',
                (TaskQueue.scheduled_for == None) | (TaskQueue.scheduled_for <= now)
            ).order_by(
                TaskQueue.priority.desc(),
                TaskQueue.created_at.asc()
            ).all()
            
            # Check dependencies and find first executable task
            for task in tasks:
                # Check if task has unmet dependencies
                if task.depends_on_task_id:
                    parent = db.query(TaskQueue).filter(
                        TaskQueue.id == task.depends_on_task_id
                    ).first()
                    
                    if not parent or parent.status != 'completed':
                        # Parent not completed yet, skip this task
                        continue
                
                # Atomically claim the task to avoid multiple workers taking the same row.
                claimed_rows = db.query(TaskQueue).filter(
                    TaskQueue.id == task.id,
                    TaskQueue.status == 'pending'
                ).update({
                    TaskQueue.status: 'running',
                    TaskQueue.locked_by: worker_name,
                    TaskQueue.locked_at: now,
                    TaskQueue.started_at: now
                }, synchronize_session=False)

                if claimed_rows != 1:
                    db.rollback()
                    continue

                db.commit()
                locked_task = db.query(TaskQueue).filter(TaskQueue.id == task.id).first()
                logger.debug(f"Worker {worker_name} locked task {task.id} ({task.task_type})")
                return locked_task
            
            return None
        except Exception as e:
            logger.error(f"Failed to fetch task: {e}")
            return None
        finally:
            self._safe_close_db(db)
    
    async def _execute_task(self, task: TaskQueue, worker_name: str):
        """Execute a task based on its type"""
        try:
            payload = json.loads(task.payload)
            
            # Route to appropriate handler based on task_type
            if task.task_type == 'search_keyword':
                await self._handle_search_task(task.id, payload)
            elif task.task_type == 'crawl_domain':
                await self._handle_crawl_task(task.id, payload)
            elif task.task_type == 'extract_contacts':
                await self._handle_extract_task(task.id, payload)
            else:
                logger.warning(f"Unknown task type: {task.task_type}")
                await self._handle_task_failure(task.id, f"Unknown task type: {task.task_type}")
                return
            
            # Mark as completed (handlers already created child tasks)
            await self._handle_task_completion(task.id, {"status": "success"})
            logger.info(f"✅ Task {task.id} ({task.task_type}) completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Task {task.id} execution failed: {e}")
            raise
    
    async def _handle_search_task(self, task_id: int, payload: Dict):
        """Handle keyword search task - creates crawl tasks for each result"""
        keyword_id = payload.get('keyword_id')
        keyword_text = payload.get('keyword')
        language = payload.get('language', 'ru')
        country = payload.get('country', 'RU')
        
        if not keyword_id or not keyword_text:
            raise ValueError("Missing keyword_id or keyword in payload")
        
        logger.info(f"🔍 Searching for keyword {keyword_id}: '{keyword_text}' ({language}/{country})")
        
        # Perform search
        serp = self._get_serp_service()
        search_results, raw_response = serp.search(
            query=keyword_text,
            country=country,
            language=language,
            num_results=settings.SEARCH_RESULTS_PER_KEYWORD
        )
        
        if not search_results:
            logger.warning(f"No search results for keyword {keyword_id}")
            return
        
        # Save search results to DB
        db = SessionLocal()
        try:
            raw_query = f"{keyword_text} site:{country}" if country else keyword_text
            serp.save_results(db, keyword_id, search_results, raw_query, raw_response)
            logger.info(f"✓ Saved {len(search_results)} search results for keyword {keyword_id}")
            
            # Create crawl tasks for each URL (+ optional domain-root fallback)
            queued_urls = set()
            for idx, result in enumerate(search_results):
                url = result['url']
                candidate_urls = [url]
                if self._needs_domain_fallback(url):
                    candidate_urls.append(self._root_url(url))

                for candidate_url in candidate_urls:
                    if candidate_url in queued_urls:
                        continue

                    # Ensure SearchResult exists for this candidate URL
                    sr = db.query(SearchResult).filter(
                        SearchResult.keyword_id == keyword_id,
                        SearchResult.url == candidate_url
                    ).first()

                    if not sr:
                        sr = SearchResult(
                            keyword_id=keyword_id,
                            url=candidate_url,
                            title=result.get('title'),
                            snippet=result.get('snippet'),
                            position=result.get('position'),
                            raw_search_query=raw_query,
                            raw_search_response=raw_response
                        )
                        db.add(sr)
                        db.flush()

                    queued_urls.add(candidate_url)
                    await self.add_task(
                        task_name=f"crawl_{sr.id}",
                        task_type='crawl_domain',
                        payload={
                            'search_result_id': sr.id,
                            'url': candidate_url,
                            'keyword_id': keyword_id
                        },
                        priority=5,
                        keyword_id=keyword_id,
                        depends_on_task_id=task_id  # Depends on search completion
                    )
            
            db.commit()
            logger.info(f"✓ Created {len(queued_urls)} crawl tasks for keyword {keyword_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save search results: {e}")
            raise
        finally:
            self._safe_close_db(db)
    
    async def _handle_crawl_task(self, task_id: int, payload: Dict):
        """Handle domain crawling task - creates extract task"""
        search_result_id = payload.get('search_result_id')
        url = payload.get('url')
        keyword_id = payload.get('keyword_id')
        
        if not search_result_id or not url:
            raise ValueError("Missing search_result_id or url in payload")
        
        logger.info(f"🕷️  Crawling domain: {url}")
        
        # Crawl the domain
        crawler = self._get_crawler_service()
        crawl_data = await crawler.crawl_domain(url)
        
        if crawl_data.get("skipped"):
            logger.info(f"⊘ Skipped crawling {url}")
            return
        
        # Save crawl log
        db = SessionLocal()
        try:
            from models.database import CrawlLog
            import time
            
            crawl_log = CrawlLog(
                domain=crawl_data["domain"],
                url=url,
                status_code=200,
                pages_crawled=crawl_data["pages_crawled"],
                duration_seconds=int(crawl_data["duration"])
            )
            db.add(crawl_log)
            db.commit()
            logger.debug(f"✓ Saved crawl log for {url}")
            
            # Extract contact page URLs from crawled content
            contact_page_urls = []
            for item in crawl_data.get("content", []):
                if item.get("type") == "contact_page":
                    # Get relative path
                    from urllib.parse import urlparse
                    parsed = urlparse(item['url'])
                    contact_page_urls.append(parsed.path)
            
            # Create extract task
            if contact_page_urls or crawl_data.get("content"):
                await self.add_task(
                    task_name=f"extract_{search_result_id}",
                    task_type='extract_contacts',
                    payload={
                        'search_result_id': search_result_id,
                        'url': url,
                        'domain': crawl_data['domain'],
                        'keyword_id': keyword_id,
                        'contact_page_urls': contact_page_urls[:5]  # Limit to top 5
                    },
                    priority=7,
                    keyword_id=keyword_id,
                    depends_on_task_id=task_id
                )
                logger.info(f"✓ Created extract task for {url}")
            else:
                logger.warning(f"No contact pages found for {url}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save crawl data: {e}")
            raise
        finally:
            self._safe_close_db(db)
    
    async def _handle_extract_task(self, task_id: int, payload: Dict):
        """Handle contact extraction - saves final results to DB"""
        search_result_id = payload.get('search_result_id')
        url = payload.get('url')
        domain = payload.get('domain')
        keyword_id = payload.get('keyword_id')
        contact_page_urls = payload.get('contact_page_urls', [])
        
        if not search_result_id or not domain:
            raise ValueError("Missing search_result_id or domain in payload")
        
        logger.info(f"🔎 Extracting contacts from {domain}")
        
        # Phase 1: crawl contact pages (fast mode)
        crawler = self._get_crawler_service()
        if contact_page_urls:
            crawl_data = await crawler.crawl_contact_pages(url, contact_page_urls)
        else:
            # No pre-identified contact pages: use full crawl directly
            crawl_data = await crawler.crawl_domain(url)
        
        if not crawl_data.get("content"):
            logger.warning(f"No content to extract from {domain}")
            return
        
        # Extract contacts
        extractor = self._get_extraction_service()
        contacts, llm_data = extractor.extract_contacts(crawl_data["content"])

        # Phase 2 fallback: run full crawl only if fast phase found no contacts.
        if contact_page_urls and not (contacts.emails or contacts.telegram_links or contacts.linkedin_links):
            logger.info(f"No contacts in fast mode for {domain}; running full domain fallback crawl")
            full_crawl_data = await crawler.crawl_domain(url)
            if full_crawl_data.get("content"):
                contacts, llm_data = extractor.extract_contacts(full_crawl_data["content"])
                crawl_data = full_crawl_data
        
        # Verify emails via MX records
        if contacts.emails:
            verified_emails = await extractor.batch_verify_emails(contacts.emails)
            logger.info(f"✓ Email verification: {sum(verified_emails.values())}/{len(verified_emails)} valid")
        
        # Save to database
        db = SessionLocal()
        try:
            # Determine tags (hybrid approach: keyword + LLM classification)
            tags = []
            try:
                # 1. Get keyword text as base tag
                keyword_obj = db.query(Keyword).filter(Keyword.id == keyword_id).first()
                if keyword_obj:
                    tags.append(keyword_obj.keyword)
                    logger.info(f"Added keyword as tag: {keyword_obj.keyword}")
                
                # 2. Use LLM to classify domain category (if enabled)
                if settings.USE_LLM_EXTRACTION and crawl_data.get("content"):
                    # Combine all page content for classification
                    combined_content = "\n\n".join([
                        item.get("content", "")[:1000] 
                        for item in crawl_data["content"][:3]  # First 3 pages
                    ])
                    
                    llm_categories = extractor.classify_domain_category(
                        combined_content, 
                        keyword=keyword_obj.keyword if keyword_obj else ""
                    )
                    
                    # Add LLM categories (avoid duplicates)
                    for category in llm_categories:
                        if category.lower() not in [t.lower() for t in tags]:
                            tags.append(category)
                    
                    logger.info(f"Final tags for {domain}: {tags}")
            except Exception as e:
                logger.warning(f"Failed to determine tags for {domain}: {e}")
                # Fallback to keyword only
                if keyword_id:
                    try:
                        keyword_obj = db.query(Keyword).filter(Keyword.id == keyword_id).first()
                        if keyword_obj:
                            tags = [keyword_obj.keyword]
                    except Exception:
                        pass
            
            # Create DomainContact with JSON
            contacts_data = {
                "emails": contacts.emails,
                "telegram": contacts.telegram_links,
                "linkedin": contacts.linkedin_links,
                "phones": contacts.phone_numbers if hasattr(contacts, 'phone_numbers') else [],
                "social": contacts.social_links if hasattr(contacts, 'social_links') else {}
            }
            
            domain_contact = DomainContact(
                search_result_id=search_result_id,
                domain=domain,
                tags=tags,  # ← Hybrid tags: keyword + LLM categories
                contacts_json=contacts_data,
                confidence_score=extractor.calculate_confidence(contacts),
                extraction_method="llm" if settings.USE_LLM_EXTRACTION else "regex"
            )
            db.add(domain_contact)
            db.flush()  # Get the ID
            
            # Create normalized Contact records
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
            
            # Update crawl log with LLM data if available
            if llm_data:
                crawl_log = db.query(CrawlLog).filter(
                    CrawlLog.domain == domain,
                    CrawlLog.url == url
                ).order_by(CrawlLog.crawled_at.desc()).first()
                
                if crawl_log:
                    crawl_log.llm_request = llm_data.get("request")
                    crawl_log.llm_response = llm_data.get("response")
                    crawl_log.llm_model = llm_data.get("model")
            
            db.commit()
            
            total_social = sum(len(v) for v in (contacts.social_links or {}).values())
            total_contacts = len(contacts.emails) + len(contacts.telegram_links) + len(contacts.linkedin_links) + total_social
            logger.info(f"✅ Saved {total_contacts} contacts for {domain}: "
                       f"{len(contacts.emails)} emails, {len(contacts.telegram_links)} Telegram, "
                       f"{len(contacts.linkedin_links)} LinkedIn, {total_social} social")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save contacts for {domain}: {e}")
            raise
        finally:
            self._safe_close_db(db)
    
    async def _handle_task_completion(self, task_id: int, result: Dict):
        """Mark task as completed"""
        try:
            db = SessionLocal()
            task = db.query(TaskQueue).filter(TaskQueue.id == task_id).first()
            if task:
                task.status = 'completed'
                task.result = json.dumps(result)
                task.completed_at = datetime.now(timezone.utc)
                task.locked_by = None
                task.locked_at = None
                db.commit()
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {e}")
        finally:
            self._safe_close_db(db)
    
    async def _handle_task_failure(self, task_id: int, error_message: str):
        """Handle task failure with retry logic"""
        try:
            db = SessionLocal()
            task = db.query(TaskQueue).filter(TaskQueue.id == task_id).first()
            if task:
                task.retry_count += 1
                task.error_message = error_message
                
                if task.retry_count < task.max_retries:
                    # Retry the task
                    task.status = 'pending'
                    task.locked_by = None
                    task.locked_at = None
                    logger.info(f"Task {task_id} will retry ({task.retry_count}/{task.max_retries})")
                else:
                    # Max retries reached
                    task.status = 'failed'
                    task.completed_at = datetime.now(timezone.utc)
                    task.locked_by = None
                    task.locked_at = None
                    logger.error(f"Task {task_id} failed after {task.retry_count} retries")
                
                db.commit()
        except Exception as e:
            logger.error(f"Failed to handle task failure {task_id}: {e}")
        finally:
            self._safe_close_db(db)
    
    async def get_queue_stats(self) -> Dict:
        """Get queue statistics with keyword breakdown"""
        try:
            db = SessionLocal()
            now = datetime.now(timezone.utc)
            day_ago = now - timedelta(hours=24)
            stats = {
                'pending': db.query(TaskQueue).filter(TaskQueue.status == 'pending').count(),
                'running': db.query(TaskQueue).filter(TaskQueue.status == 'running').count(),
                'completed': db.query(TaskQueue).filter(TaskQueue.status == 'completed').count(),
                'failed': db.query(TaskQueue).filter(TaskQueue.status == 'failed').count(),
                'total': db.query(TaskQueue).count(),
                'current_workers': self.current_tasks
            }
            
            # Add keyword-level stats
            keywords_in_progress = db.query(TaskQueue.keyword_id).filter(
                TaskQueue.keyword_id.isnot(None),
                TaskQueue.status.in_(['pending', 'running'])
            ).distinct().count()
            
            stats['keywords_in_progress'] = keywords_in_progress
            crawl_logs_24h = db.query(CrawlLog).filter(
                CrawlLog.crawled_at >= day_ago
            )
            total_crawls_24h = crawl_logs_24h.count()
            zero_page_crawls_24h = crawl_logs_24h.filter(CrawlLog.pages_crawled == 0).count()

            contacts_24h = db.query(DomainContact).filter(
                DomainContact.created_at >= day_ago
            )
            total_domains_24h = contacts_24h.count()
            domains_with_any_social_24h = 0
            for row in contacts_24h.with_entities(DomainContact.contacts_json).all():
                payload = row[0] or {}
                social = payload.get("social") if isinstance(payload, dict) else None
                if isinstance(social, dict) and any(bool(v) for v in social.values()):
                    domains_with_any_social_24h += 1

            stats['crawls_24h'] = total_crawls_24h
            stats['zero_page_crawls_24h'] = zero_page_crawls_24h
            stats['crawl_success_rate_24h'] = round(
                ((total_crawls_24h - zero_page_crawls_24h) / total_crawls_24h) * 100, 2
            ) if total_crawls_24h else 100.0
            stats['domains_with_social_24h'] = domains_with_any_social_24h
            stats['social_coverage_rate_24h'] = round(
                (domains_with_any_social_24h / total_domains_24h) * 100, 2
            ) if total_domains_24h else 0.0
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}
        finally:
            self._safe_close_db(db)
    
    async def clear_completed_tasks(self, older_than_days: int = 7):
        """Clear old completed/failed tasks"""
        try:
            db = SessionLocal()
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
            
            deleted = db.query(TaskQueue).filter(
                TaskQueue.status.in_(['completed', 'failed']),
                TaskQueue.completed_at < cutoff_date
            ).delete()
            
            db.commit()
            logger.info(f"Cleared {deleted} old tasks from queue")
            return deleted
        except Exception as e:
            logger.error(f"Failed to clear old tasks: {e}")
            return 0
        finally:
            self._safe_close_db(db)
    
    async def recover_stale_tasks(self):
        """Recover tasks that are stuck in 'running' state (worker crashed)"""
        try:
            db = SessionLocal()
            timeout_threshold = datetime.now(timezone.utc) - timedelta(seconds=self.lock_timeout)
            
            stale_tasks = db.query(TaskQueue).filter(
                TaskQueue.status == 'running',
                TaskQueue.locked_at < timeout_threshold
            ).all()
            
            if stale_tasks:
                logger.warning(f"Found {len(stale_tasks)} stale running tasks, recovering...")
                
                for task in stale_tasks:
                    task.status = 'pending'
                    task.locked_by = None
                    task.locked_at = None
                    task.error_message = f"Task recovered from stale state (locked at {task.locked_at})"
                
                db.commit()
                logger.info(f"✓ Recovered {len(stale_tasks)} stale tasks")
                return len(stale_tasks)
            
            return 0
        except Exception as e:
            logger.error(f"Failed to recover stale tasks: {e}")
            return 0
        finally:
            self._safe_close_db(db)
