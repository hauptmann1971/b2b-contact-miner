from playwright.async_api import async_playwright, Page, Browser
from typing import List, Dict, Set, Tuple, Optional
from config.settings import settings
from loguru import logger
import asyncio
import time
from urllib.parse import urljoin, urlparse
import re
from collections import deque


class PrioritizedLink:
    """Link with priority for crawling"""
    def __init__(self, url: str, priority: int, depth: int):
        self.url = url
        self.priority = priority
        self.depth = depth
    
    def __lt__(self, other):
        return self.priority > other.priority


class DomainRateLimiter:
    """Rate limiter per domain using semaphore"""
    def __init__(self, max_concurrent_per_domain: int = 5):
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        self.max_concurrent = max_concurrent_per_domain
    
    def get_semaphore(self, domain: str) -> asyncio.Semaphore:
        """Get or create semaphore for domain"""
        if domain not in self.semaphores:
            self.semaphores[domain] = asyncio.Semaphore(self.max_concurrent)
        return self.semaphores[domain]


class CrawlerService:
    def __init__(self):
        self.max_pages = settings.MAX_PAGES_PER_DOMAIN
        self.timeout = settings.REQUEST_TIMEOUT * 1000
        self.processed_domains = set()
        self.rate_limiter = DomainRateLimiter(settings.MAX_CONCURRENT_DOMAINS_PER_SITE)
    
    async def crawl_domain(self, base_url: str) -> Dict:
        """Crawl a domain with prioritized link extraction and deduplication"""
        base_url = self._normalize_base_url(base_url)
        domain = urlparse(base_url).netloc
        
        # Note: Redis deduplication removed - using database-backed task queue instead
        # Domain deduplication is now handled by the task queue status tracking
        
        logger.info(f"Starting crawl for domain: {domain}")
        start_time = time.time()
        pages_crawled = 0
        all_content = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.HEADLESS_BROWSER,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            try:
                context = await browser.new_context(
                    user_agent=self._get_random_user_agent(),
                    viewport={'width': 1920, 'height': 1080},
                    ignore_https_errors=True
                )
                
                page = await context.new_page()
                
                try:
                    sitemap_urls = await self._parse_sitemap(page, base_url)
                    if sitemap_urls:
                        logger.info(f"Found {len(sitemap_urls)} URLs in sitemap for {domain}")
                    
                    pages_to_crawl = self._build_prioritized_queue(base_url, sitemap_urls if sitemap_urls else [])
                    
                    while pages_to_crawl and pages_crawled < self.max_pages:
                        # Check domain crawl timeout
                        elapsed_time = time.time() - start_time
                        if elapsed_time > settings.DOMAIN_CRAWL_TIMEOUT:
                            logger.warning(f"Domain crawl timeout for {domain} after {elapsed_time:.0f}s ({pages_crawled} pages)")
                            break
                        
                        prioritized_link = pages_to_crawl.pop(0)
                        
                        if pages_crawled >= self.max_pages:
                            break
                        
                        semaphore = self.rate_limiter.get_semaphore(domain)
                        async with semaphore:
                            try:
                                page_data = await self._crawl_page_with_rotation(page, prioritized_link.url)
                                if page_data:
                                    all_content.append({
                                        "url": prioritized_link.url,
                                        "content": page_data.get("text", ""),
                                        "html": page_data.get("html", ""),
                                        "type": "contact_page" if self._is_contact_page(prioritized_link.url) else "regular_page",
                                        "priority": prioritized_link.priority
                                    })
                                    pages_crawled += 1
                                    logger.info(f"Crawled [{prioritized_link.priority}] {prioritized_link.url}")
                                    
                                    if prioritized_link.priority >= 8 and self._has_quick_contacts(page_data.get("text", "")):
                                        logger.info(f"Found contacts on high-priority page, stopping early for {domain}")
                                        break
                                
                                if prioritized_link.priority >= 5:
                                    new_links = await self._extract_links_with_priority(page, prioritized_link.url, 
                                                                                       prioritized_link.depth + 1, domain)
                                    pages_to_crawl.extend(new_links)
                                    pages_to_crawl.sort(key=lambda x: x.priority, reverse=True)
                                
                                await asyncio.sleep(settings.DELAY_BETWEEN_REQUESTS)
                                
                            except Exception as e:
                                logger.warning(f"Failed to crawl {prioritized_link.url}: {e}")
                                continue
                finally:
                    await page.close()
                
            finally:
                await browser.close()
        
        duration = time.time() - start_time
        
        # Note: Redis caching removed - using database-backed task queue for tracking
        
        logger.info(f"Completed crawl for {domain}: {pages_crawled} pages in {duration:.2f}s")
        if pages_crawled == 0:
            logger.warning(f"No pages crawled for {domain}; likely timeout/blocked or invalid entry URL")
        
        return {
            "domain": domain,
            "pages_crawled": pages_crawled,
            "content": all_content,
            "duration": duration,
            "skipped": False
        }
    
    def _build_prioritized_queue(self, base_url: str, sitemap_urls: List[str] = None) -> List[PrioritizedLink]:
        """Build prioritized queue of pages to crawl"""
        queue = []
        
        for path in settings.CONTACT_PATHS:
            full_url = urljoin(base_url, path)
            queue.append(PrioritizedLink(full_url, priority=10, depth=0))
        
        if sitemap_urls:
            for url in sitemap_urls:
                if self._is_contact_page(url):
                    queue.append(PrioritizedLink(url, priority=9, depth=0))
        
        queue.append(PrioritizedLink(base_url, priority=7, depth=0))
        
        additional_paths = ["/team-members", "/our-story", "/company", "/leadership-team"]
        for path in additional_paths:
            full_url = urljoin(base_url, path)
            queue.append(PrioritizedLink(full_url, priority=5, depth=0))
        
        return queue
    
    async def _parse_sitemap(self, page: Page, base_url: str) -> Optional[List[str]]:
        """Parse sitemap.xml to find contact pages quickly"""
        sitemap_url = urljoin(base_url, "/sitemap.xml")
        
        try:
            response = await page.goto(sitemap_url, timeout=10000, wait_until="domcontentloaded")
            if response.status != 200:
                return None
            
            content = await page.content()
            urls = re.findall(r'<loc>(.*?)</loc>', content)
            
            filtered_urls = [
                url for url in urls 
                if not any(url.endswith(ext) for ext in ['.jpg', '.png', '.pdf', '.zip', '.mp4'])
            ]
            
            return filtered_urls[:100]
        except Exception as e:
            logger.debug(f"No sitemap found for {base_url}: {e}")
            return None
    
    async def _crawl_page_with_rotation(self, page: Page, url: str) -> Optional[Dict[str, str]]:
        """Crawl page with rotated User-Agent and return text+html."""
        try:
            new_ua = self._get_random_user_agent()
            await page.set_extra_http_headers({"User-Agent": new_ua})

            try:
                await page.goto(url, timeout=self.timeout, wait_until="networkidle")
            except Exception:
                # Some sites never reach "networkidle" due to trackers/streams; fallback to DOM ready.
                await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
            await asyncio.sleep(1)
            
            text_content = await page.inner_text("body")
            html_content = await page.content()
            return {
                "text": text_content,
                "html": html_content
            }
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return None

    def _normalize_base_url(self, url: str) -> str:
        """Normalize SERP URL to domain root for contact crawling."""
        parsed = urlparse(url)
        if not parsed.scheme:
            url = f"https://{url}"
            parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/"
    
    async def _extract_links_with_priority(self, page: Page, current_url: str, 
                                          depth: int, domain: str) -> List[PrioritizedLink]:
        """Extract links from page with smart prioritization and limits"""
        if depth > 2:
            return []
        
        try:
            elements = await page.query_selector_all("a")
            links = []
            for el in elements:
                href = await el.get_attribute("href")
                if href:
                    links.append(urljoin(current_url, href))
            
            prioritized_links = []
            seen_urls = set()
            
            for link in links[:50]:
                if link in seen_urls:
                    continue
                
                if not self._is_valid_internal_link(link, domain):
                    continue
                
                seen_urls.add(link)
                
                priority = self._calculate_link_priority(link)
                
                if priority >= 3:
                    prioritized_links.append(PrioritizedLink(link, priority, depth))
            
            return prioritized_links
            
        except Exception as e:
            logger.warning(f"Error extracting links from {current_url}: {e}")
            return []
    
    def _calculate_link_priority(self, url: str) -> int:
        """Calculate priority score for a link (1-10)"""
        url_lower = url.lower()
        
        if any(path in url_lower for path in ['/contact', '/contacts', '/contact-us']):
            return 10
        
        if any(path in url_lower for path in ['/about', '/about-us', '/company']):
            return 9
        
        if any(path in url_lower for path in ['/team', '/our-team', '/leadership']):
            return 8
        
        if any(path in url_lower for path in ['/impressum', '/legal', '/privacy']):
            return 6
        
        if any(path in url_lower for path in ['/services', '/products', '/solutions']):
            return 4
        
        if any(path in url_lower for path in ['/blog', '/news', '/articles']):
            return 2
        
        return 1
    
    def _is_contact_page(self, url: str) -> bool:
        """Check if URL looks like a contact page"""
        url_lower = url.lower()
        contact_indicators = [
            '/contact', '/contacts', '/about', '/team', '/leadership',
            '/impressum', '/legal', '/who-we-are', '/our-team'
        ]
        return any(indicator in url_lower for indicator in contact_indicators)
    
    def _has_quick_contacts(self, content: str) -> bool:
        """Quick check if content contains contact info"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        telegram_pattern = r'(?:t\.me|telegram\.me)[/\w]+'
        
        return bool(re.search(email_pattern, content) or re.search(telegram_pattern, content))
    
    def _get_random_user_agent(self) -> str:
        """Get random User-Agent from pool"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
        ]
        import random
        return random.choice(user_agents)
    
    def _is_valid_internal_link(self, url: str, domain: str) -> bool:
        """Check if URL is valid internal link"""
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc in ("", domain) and
                len(parsed.path) > 1 and
                not any(parsed.path.endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.zip', '.mp4', '.doc'])
            )
        except Exception:
            return False
    
    async def crawl_contact_pages(self, base_url: str, contact_page_paths: List[str]) -> Dict:
        """Crawl only specific contact pages (fast extraction mode)
        
        Args:
            base_url: Base domain URL
            contact_page_paths: List of relative paths to contact pages
            
        Returns:
            Dict with domain, content from contact pages, and metadata
        """
        domain = urlparse(base_url).netloc
        logger.info(f"Fast crawling contact pages for {domain}: {len(contact_page_paths)} pages")
        
        all_content = []
        pages_crawled = 0
        start_time = time.time()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.HEADLESS_BROWSER,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            try:
                context = await browser.new_context(
                    user_agent=self._get_random_user_agent(),
                    viewport={'width': 1920, 'height': 1080},
                    ignore_https_errors=True
                )
                
                page = await context.new_page()
                
                try:
                    for path in contact_page_paths:
                        full_url = urljoin(base_url, path)
                        
                        try:
                            page_data = await self._crawl_page_with_rotation(page, full_url)
                            if page_data:
                                all_content.append({
                                    "url": full_url,
                                    "content": page_data.get("text", ""),
                                    "html": page_data.get("html", ""),
                                    "type": "contact_page",
                                    "priority": 10
                                })
                                pages_crawled += 1
                                logger.debug(f"Crawled contact page: {full_url}")
                            
                            await asyncio.sleep(0.3)  # Short delay between pages
                            
                        except Exception as e:
                            logger.warning(f"Failed to crawl contact page {full_url}: {e}")
                            continue
                finally:
                    await page.close()
                
            finally:
                await browser.close()
        
        duration = time.time() - start_time
        logger.info(f"Completed fast crawl for {domain}: {pages_crawled} contact pages in {duration:.2f}s")
        
        return {
            "domain": domain,
            "pages_crawled": pages_crawled,
            "content": all_content,
            "duration": duration,
            "skipped": False
        }
