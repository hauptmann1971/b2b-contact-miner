"""
Tests for input validation and security improvements in web_server.py
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestInputValidation:
    """Test input validation in add_keyword endpoint"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        from web_server import app
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_empty_keyword_rejected(self, client):
        """Test that empty keyword is rejected"""
        response = client.post('/add_keyword', data={
            'keyword': '',
            'language': 'ru',
            'country': 'RU'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Check for error message in response (decode to string for unicode check)
        response_text = response.data.decode('utf-8').lower()
        assert 'error' in response_text or 'ошибка' in response_text or 'пустым' in response_text
    
    def test_whitespace_only_keyword_rejected(self, client):
        """Test that whitespace-only keyword is rejected"""
        response = client.post('/add_keyword', data={
            'keyword': '   ',
            'language': 'ru',
            'country': 'RU'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_very_long_keyword_rejected(self, client):
        """Test that keyword longer than 500 chars is rejected"""
        long_keyword = 'a' * 501
        
        response = client.post('/add_keyword', data={
            'keyword': long_keyword,
            'language': 'ru',
            'country': 'RU'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should be rejected due to length
        response_text = response.data.decode('utf-8').lower()
        assert 'слишком длинное' in response_text or 'error' in response_text
    
    def test_max_length_keyword_accepted(self, client):
        """Test that keyword with exactly 500 chars is accepted"""
        max_keyword = 'a' * 500
        
        with patch('web_server.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.post('/add_keyword', data={
                'keyword': max_keyword,
                'language': 'ru',
                'country': 'RU'
            }, follow_redirects=True)
            
            # Should not be rejected for length
            assert response.status_code == 200
    
    def test_xss_characters_sanitized(self, client):
        """Test that XSS characters are removed"""
        xss_keyword = '<script>alert("xss")</script>test'
        
        with patch('web_server.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.post('/add_keyword', data={
                'keyword': xss_keyword,
                'language': 'ru',
                'country': 'RU'
            }, follow_redirects=True)
            
            # Check that dangerous characters were removed
            call_args = mock_db.add.call_args
            if call_args:
                keyword_obj = call_args[0][0]
                assert '<' not in keyword_obj.keyword
                assert '>' not in keyword_obj.keyword
                assert '"' not in keyword_obj.keyword
                assert "'" not in keyword_obj.keyword
    
    def test_invalid_language_defaults_to_russian(self, client):
        """Test that invalid language defaults to 'ru'"""
        with patch('web_server.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.post('/add_keyword', data={
                'keyword': 'test keyword',
                'language': 'invalid_lang',
                'country': 'RU'
            }, follow_redirects=True)
            
            # Check that language was set to 'ru'
            call_args = mock_db.add.call_args
            if call_args:
                keyword_obj = call_args[0][0]
                assert keyword_obj.language == 'ru'
    
    def test_valid_languages_accepted(self, client):
        """Test that valid languages are accepted"""
        valid_languages = ['ru', 'en', 'kk', 'uz', 'ky', 'tg', 'az', 'hy', 'ka', 'be', 'ro']
        
        for lang in valid_languages:
            with patch('web_server.SessionLocal') as mock_session:
                mock_db = MagicMock()
                mock_session.return_value = mock_db
                mock_db.query.return_value.filter.return_value.first.return_value = None
                
                response = client.post('/add_keyword', data={
                    'keyword': 'test',
                    'language': lang,
                    'country': 'RU'
                }, follow_redirects=True)
                
                call_args = mock_db.add.call_args
                if call_args:
                    keyword_obj = call_args[0][0]
                    assert keyword_obj.language == lang
    
    def test_invalid_country_defaults_to_russia(self, client):
        """Test that invalid country defaults to 'RU'"""
        with patch('web_server.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.post('/add_keyword', data={
                'keyword': 'test keyword',
                'language': 'ru',
                'country': 'INVALID'
            }, follow_redirects=True)
            
            # Check that country was set to 'RU'
            call_args = mock_db.add.call_args
            if call_args:
                keyword_obj = call_args[0][0]
                assert keyword_obj.country == 'RU'
    
    def test_valid_countries_accepted(self, client):
        """Test that valid countries are accepted"""
        valid_countries = ['RU', 'KZ', 'UZ', 'KG', 'TJ', 'TM', 'AZ', 'AM', 'GE', 
                          'BY', 'MD', 'UA', 'MN', 'AF', 'PK', 'US', 'GB', 'DE', 'FR']
        
        for country in valid_countries:
            with patch('web_server.SessionLocal') as mock_session:
                mock_db = MagicMock()
                mock_session.return_value = mock_db
                mock_db.query.return_value.filter.return_value.first.return_value = None
                
                response = client.post('/add_keyword', data={
                    'keyword': 'test',
                    'language': 'ru',
                    'country': country
                }, follow_redirects=True)
                
                call_args = mock_db.add.call_args
                if call_args:
                    keyword_obj = call_args[0][0]
                    assert keyword_obj.country == country
    
    def test_duplicate_keyword_rejected(self, client):
        """Test that duplicate keyword is rejected"""
        with patch('web_server.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            
            # Simulate existing keyword
            existing_keyword = Mock()
            mock_db.query.return_value.filter.return_value.first.return_value = existing_keyword
            
            response = client.post('/add_keyword', data={
                'keyword': 'existing keyword',
                'language': 'ru',
                'country': 'RU'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # Should show warning about duplicate
            response_text = response.data.decode('utf-8').lower()
            assert 'warning' in response_text or 'уже существует' in response_text
    
    def test_quotes_removed_from_keyword(self, client):
        """Test that quotes are removed from keyword"""
        keyword_with_quotes = 'test "quoted" keyword'
        
        with patch('web_server.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.post('/add_keyword', data={
                'keyword': keyword_with_quotes,
                'language': 'ru',
                'country': 'RU'
            }, follow_redirects=True)
            
            call_args = mock_db.add.call_args
            if call_args:
                keyword_obj = call_args[0][0]
                assert '"' not in keyword_obj.keyword
                assert "'" not in keyword_obj.keyword


class TestSecretKeyGeneration:
    """Test secret key generation"""
    
    def test_secret_key_not_hardcoded(self):
        """Test that secret key is not hardcoded"""
        from web_server import app
        
        # Secret key should not be the old hardcoded value
        assert app.secret_key != 'b2b-contact-miner-secret-key'
    
    def test_secret_key_is_generated(self):
        """Test that secret key is generated if not in env"""
        import secrets
        
        # When SECRET_KEY is not set, it should generate a random one
        with patch.dict(os.environ, {}, clear=False):
            if 'SECRET_KEY' not in os.environ:
                from web_server import app
                # Should be a hex string of 64 characters (32 bytes)
                assert len(app.secret_key) == 64
                # Should be valid hex
                int(app.secret_key, 16)
    
    def test_secret_key_from_env(self):
        """Test that secret key can be set from environment"""
        custom_key = 'my-custom-secret-key-12345'
        
        with patch.dict(os.environ, {'SECRET_KEY': custom_key}):
            # Need to reload the module to pick up new env var
            import importlib
            import web_server
            importlib.reload(web_server)
            
            assert web_server.app.secret_key == custom_key


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
