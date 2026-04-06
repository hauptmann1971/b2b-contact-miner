import requests
from urllib.parse import urlparse, urljoin
from loguru import logger
import re
from functools import lru_cache


class RobotsChecker:
    def __init__(self):
        self.cache = {}
    
    @lru_cache(maxsize=1000)
    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if URL is allowed by robots.txt"""
        try:
            domain = urlparse(url).netloc
            robots_url = f"{urlparse(url).scheme}://{domain}/robots.txt"
            
            if domain not in self.cache:
                response = requests.get(robots_url, timeout=5)
                if response.status_code == 200:
                    self.cache[domain] = self._parse_robots(response.text)
                else:
                    self.cache[domain] = {"allow": [], "disallow": []}
            
            rules = self.cache[domain]
            path = urlparse(url).path
            
            for pattern in rules["disallow"]:
                if self._matches_pattern(path, pattern):
                    logger.debug(f"Blocked by robots.txt: {url} (pattern: {pattern})")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Could not check robots.txt for {url}: {e}")
            return True
    
    def _parse_robots(self, content: str) -> dict:
        """Parse robots.txt content"""
        rules = {"allow": [], "disallow": [], "crawl_delay": None}
        
        for line in content.split('\n'):
            line = line.strip().lower()
            if line.startswith('disallow:'):
                path = line.split(':', 1)[1].strip()
                if path:
                    rules["disallow"].append(path)
            elif line.startswith('allow:'):
                path = line.split(':', 1)[1].strip()
                if path:
                    rules["allow"].append(path)
            elif line.startswith('crawl-delay:'):
                try:
                    delay = float(line.split(':', 1)[1].strip())
                    rules["crawl_delay"] = delay
                except ValueError:
                    pass
        
        return rules
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches robots.txt pattern"""
        if pattern == "":
            return False
        
        regex_pattern = pattern.replace('*', '.*').replace('$', '')
        return bool(re.match(regex_pattern, path))
    
    def get_crawl_delay(self, domain: str) -> float:
        """Get crawl delay for domain from robots.txt"""
        from config.settings import settings
        
        try:
            rules = self.cache.get(domain, {})
            crawl_delay = rules.get("crawl_delay")
            
            if crawl_delay is not None:
                return max(crawl_delay, 0.1)  # Minimum 0.1s delay
            
            return settings.DELAY_BETWEEN_REQUESTS
        except Exception:
            return settings.DELAY_BETWEEN_REQUESTS
