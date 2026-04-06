import pytest
from utils.robots_checker import RobotsChecker


class TestRobotsChecker:
    """Unit tests for robots.txt checker"""
    
    def setup_method(self):
        self.checker = RobotsChecker()
    
    def test_can_fetch_allowed_url(self):
        """Test that allowed URLs return True"""
        # Mock cache with simple rules
        self.checker.cache["example.com"] = {
            "allow": [],
            "disallow": ["/admin", "/private"],
            "crawl_delay": None
        }
        
        result = self.checker.can_fetch("https://example.com/public/page")
        assert result is True
    
    def test_can_fetch_disallowed_url(self):
        """Test that disallowed URLs return False"""
        self.checker.cache["example.com"] = {
            "allow": [],
            "disallow": ["/admin", "/private"],
            "crawl_delay": None
        }
        
        result = self.checker.can_fetch("https://example.com/admin/dashboard")
        assert result is False
    
    def test_crawl_delay_parsing(self):
        """Test crawl-delay parsing from robots.txt"""
        robots_content = """
        User-agent: *
        Disallow: /admin
        Crawl-delay: 10
        """
        
        rules = self.checker._parse_robots(robots_content)
        assert rules["crawl_delay"] == 10.0
        assert "/admin" in rules["disallow"]
    
    def test_get_crawl_delay_from_cache(self):
        """Test getting crawl delay from cached rules"""
        self.checker.cache["example.com"] = {
            "allow": [],
            "disallow": [],
            "crawl_delay": 5.0
        }
        
        delay = self.checker.get_crawl_delay("example.com")
        assert delay == 5.0
    
    def test_get_crawl_delay_default(self):
        """Test default crawl delay when not specified"""
        delay = self.checker.get_crawl_delay("nonexistent.com")
        assert delay > 0  # Should return settings.DELAY_BETWEEN_REQUESTS
    
    def test_wildcard_pattern_matching(self):
        """Test wildcard pattern matching in robots.txt"""
        self.checker.cache["example.com"] = {
            "allow": [],
            "disallow": ["/*.pdf$", "/private/*"],
            "crawl_delay": None
        }
        
        # Should match *.pdf pattern
        result = self.checker.can_fetch("https://example.com/document.pdf")
        assert result is False
        
        # Should match /private/* pattern
        result = self.checker.can_fetch("https://example.com/private/secret")
        assert result is False
    
    def test_empty_disallow_rule(self):
        """Test that empty disallow rule allows everything"""
        self.checker.cache["example.com"] = {
            "allow": [],
            "disallow": [""],
            "crawl_delay": None
        }
        
        result = self.checker.can_fetch("https://example.com/anything")
        assert result is True
    
    def test_robots_txt_parse_error_handling(self):
        """Test graceful handling of malformed robots.txt"""
        malformed_content = """
        User-agent: *
        Disallow:
        Invalid-Line
        Crawl-delay: not_a_number
        """
        
        rules = self.checker._parse_robots(malformed_content)
        assert isinstance(rules, dict)
        assert "disallow" in rules
        assert "crawl_delay" in rules
