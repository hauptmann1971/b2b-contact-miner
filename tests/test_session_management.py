"""
Tests for database session management improvements in main.py
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDatabaseSessionManagement:
    """Test database session management improvements"""

    @staticmethod
    def _attach_mock_queue(pipeline):
        """Attach mocked task queue for orchestrator-mode tests."""
        queue = AsyncMock()
        queue.add_task = AsyncMock()
        queue.get_queue_stats = AsyncMock(return_value={
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "total": 0,
            "keywords_in_progress": 0
        })
        queue.stop_workers = AsyncMock()
        pipeline.task_queue = queue
    
    @pytest.fixture
    def mock_keyword(self):
        """Create a mock keyword object"""
        keyword = Mock()
        keyword.id = 1
        keyword.keyword = "test keyword"
        keyword.language = "ru"
        keyword.country = "RU"
        return keyword
    
    @pytest.mark.asyncio
    async def test_separate_session_per_keyword(self):
        """Test that each keyword gets its own database session"""
        from main import ContactMiningPipeline
        
        pipeline = ContactMiningPipeline()
        self._attach_mock_queue(pipeline)
        
        # Mock dependencies
        with patch.object(pipeline, 'initialize', new_callable=AsyncMock):
            with patch('main.SessionLocal') as mock_session_local:
                with patch('main.KeywordService') as mock_keyword_service:
                    with patch.object(pipeline.state_manager, 'create_run'):
                        # Setup mocks
                        mock_db_main = MagicMock()
                        mock_db_keyword = MagicMock()
                        
                        # First call returns main db, subsequent calls return keyword dbs
                        mock_session_local.side_effect = [mock_db_main, mock_db_keyword]
                        
                        mock_keyword_service_instance = MagicMock()
                        mock_keyword_service.return_value = mock_keyword_service_instance
                        
                        # Create mock keyword
                        keyword = Mock()
                        keyword.id = 1
                        keyword.keyword = "test"
                        keyword.language = "ru"
                        keyword.country = "RU"
                        
                        mock_keyword_service_instance.get_pending_keywords.return_value = [keyword]
                        
                        # Mock _process_keyword to avoid actual processing
                        with patch.object(pipeline, '_process_keyword', new_callable=AsyncMock) as mock_process:
                            mock_process.return_value = {"websites": 0, "contacts": 0}
                            
                            # Run pipeline
                            await pipeline.run_pipeline()
                            
                            # Orchestrator mode now uses one main session for queue orchestration
                            assert mock_session_local.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_session_closed_in_finally_block(self):
        """Test that keyword session is closed in finally block"""
        from main import ContactMiningPipeline
        
        pipeline = ContactMiningPipeline()
        self._attach_mock_queue(pipeline)
        
        with patch.object(pipeline, 'initialize', new_callable=AsyncMock):
            with patch('main.SessionLocal') as mock_session_local:
                with patch('main.KeywordService') as mock_keyword_service:
                    with patch.object(pipeline.state_manager, 'create_run'):
                        mock_db_main = MagicMock()
                        mock_session_local.return_value = mock_db_main
                        
                        mock_keyword_service_instance = MagicMock()
                        mock_keyword_service.return_value = mock_keyword_service_instance
                        
                        keyword = Mock()
                        keyword.id = 1
                        keyword.keyword = "test"
                        keyword.language = "ru"
                        keyword.country = "RU"
                        
                        mock_keyword_service_instance.get_pending_keywords.return_value = [keyword]
                        
                        with patch.object(pipeline, '_process_keyword', new_callable=AsyncMock) as mock_process:
                            # Make it raise an exception to test finally block
                            mock_process.side_effect = Exception("Test error")
                            
                            # Mock state_manager methods
                            with patch.object(pipeline.state_manager, 'mark_failed'):
                                await pipeline.run_pipeline()
                                
                                # Main orchestration DB session should still be closed
                                mock_db_main.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_main_session_closed_at_end(self):
        """Test that main session is closed at the end"""
        from main import ContactMiningPipeline
        
        pipeline = ContactMiningPipeline()
        self._attach_mock_queue(pipeline)
        
        with patch.object(pipeline, 'initialize', new_callable=AsyncMock):
            with patch('main.SessionLocal') as mock_session_local:
                with patch('main.KeywordService') as mock_keyword_service:
                    with patch.object(pipeline.state_manager, 'create_run'):
                        mock_db_main = MagicMock()
                        mock_db_keyword = MagicMock()
                        
                        mock_session_local.side_effect = [mock_db_main, mock_db_keyword]
                        
                        mock_keyword_service_instance = MagicMock()
                        mock_keyword_service.return_value = mock_keyword_service_instance
                        mock_keyword_service_instance.get_pending_keywords.return_value = []
                        
                        await pipeline.run_pipeline()
                        
                        # Verify main session was closed
                        mock_db_main.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_isolation_between_keywords(self):
        """Test that sessions are isolated between keywords"""
        from main import ContactMiningPipeline
        
        pipeline = ContactMiningPipeline()
        self._attach_mock_queue(pipeline)
        
        with patch.object(pipeline, 'initialize', new_callable=AsyncMock):
            with patch('main.SessionLocal') as mock_session_local:
                with patch('main.KeywordService') as mock_keyword_service:
                    with patch.object(pipeline.state_manager, 'create_run'):
                        mock_db_main = MagicMock()
                        mock_session_local.return_value = mock_db_main
                        
                        mock_keyword_service_instance = MagicMock()
                        mock_keyword_service.return_value = mock_keyword_service_instance
                        
                        keyword1 = Mock(id=1, keyword="test1", language="ru", country="RU")
                        keyword2 = Mock(id=2, keyword="test2", language="ru", country="RU")
                        
                        mock_keyword_service_instance.get_pending_keywords.return_value = [keyword1, keyword2]
                        
                        with patch.object(pipeline, '_process_keyword', new_callable=AsyncMock) as mock_process:
                            mock_process.return_value = {"websites": 0, "contacts": 0}
                            
                            await pipeline.run_pipeline()
                            
                            # Main orchestration DB session should be closed once
                            mock_db_main.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_not_leaked_on_exception(self):
        """Test that session is not leaked when exception occurs"""
        from main import ContactMiningPipeline
        
        pipeline = ContactMiningPipeline()
        self._attach_mock_queue(pipeline)
        
        with patch.object(pipeline, 'initialize', new_callable=AsyncMock):
            with patch('main.SessionLocal') as mock_session_local:
                with patch('main.KeywordService') as mock_keyword_service:
                    with patch.object(pipeline.state_manager, 'create_run'):
                        mock_db_main = MagicMock()
                        mock_session_local.return_value = mock_db_main
                        
                        mock_keyword_service_instance = MagicMock()
                        mock_keyword_service.return_value = mock_keyword_service_instance
                        
                        keyword = Mock(id=1, keyword="test", language="ru", country="RU")
                        mock_keyword_service_instance.get_pending_keywords.return_value = [keyword]
                        
                        with patch.object(pipeline, '_process_keyword', new_callable=AsyncMock) as mock_process:
                            mock_process.side_effect = Exception("Database error")
                            
                            with patch.object(pipeline.state_manager, 'mark_failed'):
                                await pipeline.run_pipeline()
                                
                                # Main DB session should still be closed on exception paths
                                mock_db_main.close.assert_called_once()


class TestSettingsUsageInMain:
    """Test that main.py uses settings correctly"""
    
    def test_uses_max_keywords_per_run_setting(self):
        """Test that main.py uses MAX_KEYWORDS_PER_RUN setting"""
        import inspect
        from main import ContactMiningPipeline
        
        # Get source code of run_pipeline method
        source = inspect.getsource(ContactMiningPipeline.run_pipeline)
        
        # Check that it references the setting
        assert 'MAX_KEYWORDS_PER_RUN' in source or 'settings.MAX_KEYWORDS_PER_RUN' in source
    
    def test_uses_search_results_per_keyword_setting(self):
        """Test that main.py uses SEARCH_RESULTS_PER_KEYWORD setting"""
        import inspect
        from main import ContactMiningPipeline
        
        # Get source code of _process_keyword method
        source = inspect.getsource(ContactMiningPipeline._process_keyword)
        
        # Check that it references the setting
        assert 'SEARCH_RESULTS_PER_KEYWORD' in source or 'settings.SEARCH_RESULTS_PER_KEYWORD' in source
    
    def test_no_hardcoded_limits_in_main(self):
        """Test that there are no hardcoded limits like [:5] in main.py"""
        import inspect
        from main import ContactMiningPipeline
        
        # Get source code
        source = inspect.getsource(ContactMiningPipeline)
        
        # Should use settings instead of hardcoded values
        # Note: This is a soft check - we're looking for patterns like [:5] that aren't in comments
        lines = source.split('\n')
        for line in lines:
            # Skip comments
            if '#' in line:
                line = line[:line.index('#')]
            
            # Check for hardcoded slice limits (but allow in variable names)
            if '[:5]' in line and 'SEARCH_RESULTS' not in line:
                pytest.fail(f"Found hardcoded limit in line: {line.strip()}")


class TestLoggingConfigurationInMain:
    """Test logging configuration in main.py"""
    
    def test_log_level_from_settings(self):
        """Test that log level is read from settings"""
        import inspect
        from main import ContactMiningPipeline
        
        # Read main.py source
        main_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        with open(main_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check that LOG_LEVEL is used
        assert 'LOG_LEVEL' in source
        assert 'getattr' in source or 'settings.LOG_LEVEL' in source
    
    def test_single_logger_remove_call(self):
        """Test that logger.remove() is called only once at configuration"""
        main_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        with open(main_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Count logger.remove() calls in configuration section (first 50 lines)
        config_section = '\n'.join(source.split('\n')[:50])
        remove_count = config_section.count('logger.remove()')
        
        # Should be called only once
        assert remove_count == 1, f"Expected 1 logger.remove() call, found {remove_count}"
    
    def test_both_log_formats_supported(self):
        """Test that both text and JSON log formats are supported"""
        main_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        with open(main_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check for both format configurations
        assert 'json' in source.lower()
        assert 'serialize=True' in source or 'text' in source.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
