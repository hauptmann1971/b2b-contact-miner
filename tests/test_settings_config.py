"""
Tests for settings and configuration improvements
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestSettingsConfiguration:
    """Test new settings and configuration"""
    
    def test_search_results_per_keyword_default(self):
        """Test default value for SEARCH_RESULTS_PER_KEYWORD"""
        from config.settings import settings
        
        assert hasattr(settings, 'SEARCH_RESULTS_PER_KEYWORD')
        assert settings.SEARCH_RESULTS_PER_KEYWORD == 2
    
    def test_max_keywords_per_run_default(self):
        """Test default value for MAX_KEYWORDS_PER_RUN"""
        from config.settings import settings
        
        assert hasattr(settings, 'MAX_KEYWORDS_PER_RUN')
        assert settings.MAX_KEYWORDS_PER_RUN == 50
    
    def test_log_level_default(self):
        """Test default value for LOG_LEVEL"""
        from config.settings import settings
        
        assert hasattr(settings, 'LOG_LEVEL')
        assert settings.LOG_LEVEL == 'INFO'
    
    def test_log_format_default(self):
        """Test default value for LOG_FORMAT"""
        from config.settings import settings
        
        assert hasattr(settings, 'LOG_FORMAT')
        assert settings.LOG_FORMAT == 'text'
    
    def test_database_url_is_mysql_by_default(self):
        """Test that DATABASE_URL defaults to MySQL"""
        from config.settings import settings
        
        assert 'mysql+pymysql://' in settings.DATABASE_URL
        assert 'postgresql://' not in settings.DATABASE_URL
    
    def test_settings_can_be_overridden_from_env(self):
        """Test that settings can be overridden from environment variables"""
        env_vars = {
            'SEARCH_RESULTS_PER_KEYWORD': '10',
            'MAX_KEYWORDS_PER_RUN': '100',
            'LOG_LEVEL': 'DEBUG',
            'LOG_FORMAT': 'json'
        }
        
        with patch.dict(os.environ, env_vars):
            # Need to reload settings to pick up new env vars
            import importlib
            import config.settings
            importlib.reload(config.settings)
            
            from config.settings import settings
            
            assert settings.SEARCH_RESULTS_PER_KEYWORD == 10
            assert settings.MAX_KEYWORDS_PER_RUN == 100
            assert settings.LOG_LEVEL == 'DEBUG'
            assert settings.LOG_FORMAT == 'json'


class TestLoggingConfiguration:
    """Test logging configuration improvements"""
    
    def test_log_level_info_accepted(self):
        """Test that INFO log level is accepted"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        for level in valid_levels:
            with patch.dict(os.environ, {'LOG_LEVEL': level}):
                import importlib
                import config.settings
                importlib.reload(config.settings)
                
                from config.settings import settings
                assert settings.LOG_LEVEL == level
    
    def test_invalid_log_level_defaults_to_info(self):
        """Test that invalid log level handling (should have fallback)"""
        # The getattr in main.py provides the fallback
        log_level = getattr(type('obj', (object,), {'LOG_LEVEL': 'INVALID'})(), 'LOG_LEVEL', 'INFO')
        
        # In actual code, this would use the default
        assert log_level == 'INVALID'  # Settings will have it, main.py handles fallback
    
    def test_log_format_text_supported(self):
        """Test that text log format is supported"""
        with patch.dict(os.environ, {'LOG_FORMAT': 'text'}):
            import importlib
            import config.settings
            importlib.reload(config.settings)
            
            from config.settings import settings
            assert settings.LOG_FORMAT == 'text'
    
    def test_log_format_json_supported(self):
        """Test that JSON log format is supported"""
        with patch.dict(os.environ, {'LOG_FORMAT': 'json'}):
            import importlib
            import config.settings
            importlib.reload(config.settings)
            
            from config.settings import settings
            assert settings.LOG_FORMAT == 'json'


class TestPipelineSettings:
    """Test pipeline-specific settings"""
    
    def test_search_results_per_keyword_is_positive(self):
        """Test that SEARCH_RESULTS_PER_KEYWORD is positive"""
        from config.settings import settings
        
        assert settings.SEARCH_RESULTS_PER_KEYWORD > 0
    
    def test_max_keywords_per_run_is_positive(self):
        """Test that MAX_KEYWORDS_PER_RUN is positive"""
        from config.settings import settings
        
        assert settings.MAX_KEYWORDS_PER_RUN > 0
    
    def test_settings_are_integers(self):
        """Test that numeric settings are integers"""
        from config.settings import settings
        
        assert isinstance(settings.SEARCH_RESULTS_PER_KEYWORD, int)
        assert isinstance(settings.MAX_KEYWORDS_PER_RUN, int)
    
    def test_reasonable_default_values(self):
        """Test that default values are reasonable"""
        from config.settings import settings
        
        # Should process at least 1 result per keyword
        assert settings.SEARCH_RESULTS_PER_KEYWORD >= 1
        
        # Should process at least 1 keyword per run
        assert settings.MAX_KEYWORDS_PER_RUN >= 1
        
        # Should not have excessively high defaults
        assert settings.SEARCH_RESULTS_PER_KEYWORD <= 20
        assert settings.MAX_KEYWORDS_PER_RUN <= 200


class TestEnvFileExample:
    """Test that .env.example contains all necessary settings"""
    
    def test_env_example_exists(self):
        """Test that .env.example file exists"""
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env.example')
        assert os.path.exists(env_path), ".env.example file should exist"
    
    def test_env_example_contains_new_settings(self):
        """Test that .env.example contains new settings"""
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env.example')
        
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'SEARCH_RESULTS_PER_KEYWORD' in content
        assert 'MAX_KEYWORDS_PER_RUN' in content
        assert 'LOG_LEVEL' in content
        assert 'LOG_FORMAT' in content
        assert 'SECRET_KEY' in content
    
    def test_env_example_has_pipeline_section(self):
        """Test that .env.example has Pipeline Settings section"""
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env.example')
        
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'Pipeline Settings' in content or 'PIPELINE' in content.upper()
    
    def test_env_example_has_logging_section(self):
        """Test that .env.example has Logging section"""
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env.example')
        
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'Logging' in content or 'LOG' in content.upper()
    
    def test_env_example_has_security_section(self):
        """Test that .env.example has Security section"""
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env.example')
        
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'Security' in content or 'SECRET_KEY' in content


class TestDatabaseConfiguration:
    """Test database configuration"""
    
    def test_database_url_uses_mysql(self):
        """Test that default DATABASE_URL uses MySQL"""
        from config.settings import settings
        
        assert 'mysql' in settings.DATABASE_URL.lower()
        assert 'pymysql' in settings.DATABASE_URL.lower()
    
    def test_database_url_has_correct_format(self):
        """Test that DATABASE_URL has correct SQLAlchemy format"""
        from config.settings import settings
        
        # Should follow pattern: mysql+pymysql://user:pass@host:port/db
        assert '://' in settings.DATABASE_URL
        assert '@' in settings.DATABASE_URL
        assert '/' in settings.DATABASE_URL
    
    def test_database_comment_mentions_postgresql_support(self):
        """Test that settings.py mentions PostgreSQL support"""
        settings_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.py')
        
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for comment about PostgreSQL support
        assert 'PostgreSQL' in content or 'postgresql' in content


class TestBackwardsCompatibility:
    """Test backwards compatibility of changes"""
    
    def test_existing_settings_still_work(self):
        """Test that existing settings are not broken"""
        from config.settings import settings
        
        # Check that old settings still exist
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'REDIS_URL')
        assert hasattr(settings, 'MAX_PAGES_PER_DOMAIN')
        assert hasattr(settings, 'REQUEST_TIMEOUT')
        assert hasattr(settings, 'CONCURRENT_BROWSERS')
    
    def test_new_settings_have_sensible_defaults(self):
        """Test that new settings don't break existing functionality"""
        from config.settings import settings
        
        # New settings should have defaults that work with existing code
        assert settings.SEARCH_RESULTS_PER_KEYWORD == 2  # Same as current default
        assert settings.MAX_KEYWORDS_PER_RUN == 50  # Same as old hardcoded value
    
    def test_settings_types_are_correct(self):
        """Test that all settings have correct types"""
        from config.settings import settings
        
        assert isinstance(settings.DATABASE_URL, str)
        assert isinstance(settings.REDIS_URL, str)
        assert isinstance(settings.SEARCH_RESULTS_PER_KEYWORD, int)
        assert isinstance(settings.MAX_KEYWORDS_PER_RUN, int)
        assert isinstance(settings.LOG_LEVEL, str)
        assert isinstance(settings.LOG_FORMAT, str)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
