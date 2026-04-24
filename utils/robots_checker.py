from urllib.parse import urlparse
from loguru import logger
import urllib.robotparser as robotparser
from functools import lru_cache


class RobotsChecker:
    def __init__(self):
        self.cache = {}
    
    @lru_cache(maxsize=1000)
    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if URL is allowed by robots.txt"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            cached = self.cache.get(domain)
            if isinstance(cached, dict):
                path = parsed.path
                for pattern in cached.get("disallow", []):
                    if self._matches_pattern(path, pattern):
                        logger.debug(f"Blocked by robots.txt: {url}")
                        return False
                return True

            parser = self._get_parser(parsed.scheme, domain)
            allowed = parser.can_fetch(user_agent, url)
            if not allowed:
                logger.debug(f"Blocked by robots.txt: {url}")
            return allowed
        except Exception as e:
            logger.warning(f"Could not check robots.txt for {url}: {e}")
            return True

    def _get_parser(self, scheme: str, domain: str) -> robotparser.RobotFileParser:
        cache_key = f"{scheme}://{domain}"
        if cache_key not in self.cache:
            parser = robotparser.RobotFileParser()
            parser.set_url(f"{cache_key}/robots.txt")
            parser.read()
            self.cache[cache_key] = parser
        return self.cache[cache_key]

    def _parse_robots(self, content: str) -> dict:
        """Backward-compatible simple parser used in tests."""
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
                    rules["crawl_delay"] = float(line.split(':', 1)[1].strip())
                except ValueError:
                    pass
        return rules

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Backward-compatible wildcard matching for cached test rules."""
        import re
        if pattern == "":
            return False
        regex_pattern = pattern.replace('*', '.*').replace('$', '$')
        return bool(re.match(regex_pattern, path))
    
    def get_crawl_delay(self, domain: str) -> float:
        """Get crawl delay for domain from robots.txt"""
        from config.settings import settings
        
        try:
            cached = self.cache.get(domain)
            if isinstance(cached, dict):
                crawl_delay = cached.get("crawl_delay")
            else:
                parser = self.cache.get(f"https://{domain}") or self.cache.get(f"http://{domain}")
                crawl_delay = parser.crawl_delay("*") if parser else None
            
            if crawl_delay is not None:
                return max(crawl_delay, 0.1)  # Minimum 0.1s delay
            
            return settings.DELAY_BETWEEN_REQUESTS
        except Exception:
            return settings.DELAY_BETWEEN_REQUESTS
