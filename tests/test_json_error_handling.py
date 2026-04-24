"""
Tests for JSON error handling in extraction_service.py
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.extraction_service import ExtractionService
from models.schemas import ContactInfo
from pydantic import ValidationError


class TestJSONErrorHandling:
    """Test JSON parsing error handling in LLM extraction"""
    
    @pytest.fixture
    def extractor(self):
        """Create ExtractionService instance"""
        return ExtractionService()
    
    def test_invalid_json_returns_empty_contact_info(self, extractor):
        """Test that invalid JSON returns empty ContactInfo"""
        # Mock settings to enable YandexGPT
        with patch('services.extraction_service.settings') as mock_settings:
            mock_settings.USE_YANDEXGPT = True
            mock_settings.YANDEX_IAM_TOKEN = 'test_token'
            mock_settings.YANDEX_FOLDER_ID = 'test_folder'
            mock_settings.USE_DEEPSEEK = False
            mock_settings.USE_OPENAI = False
            
            # Mock requests.post to return invalid JSON
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = {
                    "result": {
                        "alternatives": [{
                            "message": {
                                "text": "This is not valid JSON {{{"
                            }
                        }]
                    }
                }
                mock_post.return_value = mock_response
                
                contacts, llm_data = extractor._extract_with_llm_selective(["test content"])
                
                assert isinstance(contacts, ContactInfo)
                assert llm_data is None
                assert len(contacts.emails) == 0
                assert len(contacts.telegram_links) == 0
                assert len(contacts.linkedin_links) == 0
    
    def test_malformed_json_returns_empty_contact_info(self, extractor):
        """Test that malformed JSON returns empty ContactInfo"""
        with patch('services.extraction_service.settings') as mock_settings:
            mock_settings.USE_YANDEXGPT = True
            mock_settings.YANDEX_IAM_TOKEN = 'test_token'
            mock_settings.YANDEX_FOLDER_ID = 'test_folder'
            mock_settings.USE_DEEPSEEK = False
            mock_settings.USE_OPENAI = False
            
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = {
                    "result": {
                        "alternatives": [{
                            "message": {
                                "text": '{"emails": ["test@test.com"'  # Missing closing bracket
                            }
                        }]
                    }
                }
                mock_post.return_value = mock_response
                
                contacts, llm_data = extractor._extract_with_llm_selective(["test content"])
                
                assert isinstance(contacts, ContactInfo)
                assert llm_data is None
                assert len(contacts.emails) == 0
    
    def test_non_dict_json_returns_empty_contact_info(self, extractor):
        """Test that non-dict JSON response returns empty ContactInfo"""
        with patch('services.extraction_service.settings') as mock_settings:
            mock_settings.USE_YANDEXGPT = True
            mock_settings.YANDEX_IAM_TOKEN = 'test_token'
            mock_settings.YANDEX_FOLDER_ID = 'test_folder'
            mock_settings.USE_DEEPSEEK = False
            mock_settings.USE_OPENAI = False
            
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = {
                    "result": {
                        "alternatives": [{
                            "message": {
                                "text": '["email1@test.com", "email2@test.com"]'  # List instead of dict
                            }
                        }]
                    }
                }
                mock_post.return_value = mock_response
                
                contacts, llm_data = extractor._extract_with_llm_selective(["test content"])
                
                assert isinstance(contacts, ContactInfo)
                assert llm_data is None
                assert len(contacts.emails) == 0
    
    def test_valid_json_parsed_correctly(self, extractor):
        """Test that valid JSON is parsed correctly"""
        with patch('services.extraction_service.settings') as mock_settings:
            mock_settings.USE_YANDEXGPT = True
            mock_settings.YANDEX_IAM_TOKEN = 'test_token'
            mock_settings.YANDEX_FOLDER_ID = 'test_folder'
            mock_settings.USE_DEEPSEEK = False
            mock_settings.USE_OPENAI = False
            
            expected_emails = ["ceo@company.com", "info@company.com"]
            expected_telegram = ["https://t.me/company"]
            expected_linkedin = ["https://linkedin.com/in/john-doe"]
            
            valid_json = json.dumps({
                "emails": expected_emails,
                "telegram": expected_telegram,
                "linkedin": expected_linkedin
            })
            
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = {
                    "result": {
                        "alternatives": [{
                            "message": {
                                "text": valid_json
                            }
                        }]
                    }
                }
                mock_post.return_value = mock_response
                
                contacts, llm_data = extractor._extract_with_llm_selective(["test content"])
                
                assert isinstance(contacts, ContactInfo)
                assert llm_data is not None
                assert contacts.emails == expected_emails
                assert contacts.telegram_links == expected_telegram
                assert contacts.linkedin_links == expected_linkedin
    
    def test_empty_json_object_returns_empty_lists(self, extractor):
        """Test that empty JSON object returns empty lists"""
        with patch('services.extraction_service.settings') as mock_settings:
            mock_settings.USE_YANDEXGPT = True
            mock_settings.YANDEX_IAM_TOKEN = 'test_token'
            mock_settings.YANDEX_FOLDER_ID = 'test_folder'
            mock_settings.USE_DEEPSEEK = False
            mock_settings.USE_OPENAI = False
            
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = {
                    "result": {
                        "alternatives": [{
                            "message": {
                                "text": '{}'
                            }
                        }]
                    }
                }
                mock_post.return_value = mock_response
                
                contacts, llm_data = extractor._extract_with_llm_selective(["test content"])
                
                assert isinstance(contacts, ContactInfo)
                assert llm_data is not None
                assert len(contacts.emails) == 0
                assert len(contacts.telegram_links) == 0
                assert len(contacts.linkedin_links) == 0
    
    def test_json_with_missing_keys_uses_defaults(self, extractor):
        """Test that JSON with missing keys uses default empty lists"""
        with patch('services.extraction_service.settings') as mock_settings:
            mock_settings.USE_YANDEXGPT = True
            mock_settings.YANDEX_IAM_TOKEN = 'test_token'
            mock_settings.YANDEX_FOLDER_ID = 'test_folder'
            mock_settings.USE_DEEPSEEK = False
            mock_settings.USE_OPENAI = False
            
            partial_json = json.dumps({
                "emails": ["test@company.com"]
                # telegram and linkedin keys are missing
            })
            
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = {
                    "result": {
                        "alternatives": [{
                            "message": {
                                "text": partial_json
                            }
                        }]
                    }
                }
                mock_post.return_value = mock_response
                
                contacts, llm_data = extractor._extract_with_llm_selective(["test content"])
                
                assert isinstance(contacts, ContactInfo)
                assert llm_data is not None
                assert contacts.emails == ["test@company.com"]
                assert contacts.telegram_links == []
                assert contacts.linkedin_links == []
    
    def test_llm_exception_returns_empty_contact_info(self, extractor):
        """Test that LLM API exception returns empty ContactInfo"""
        with patch('services.extraction_service.settings') as mock_settings:
            mock_settings.USE_YANDEXGPT = True
            mock_settings.YANDEX_IAM_TOKEN = 'test_token'
            mock_settings.YANDEX_FOLDER_ID = 'test_folder'
            mock_settings.USE_DEEPSEEK = False
            mock_settings.USE_OPENAI = False
            
            with patch('requests.post') as mock_post:
                mock_post.side_effect = Exception("API Error")
                
                contacts, llm_data = extractor._extract_with_llm_selective(["test content"])
                
                assert isinstance(contacts, ContactInfo)
                assert llm_data is None
                assert len(contacts.emails) == 0
                assert len(contacts.telegram_links) == 0
                assert len(contacts.linkedin_links) == 0
    
    def test_no_llm_configured_returns_empty_contact_info(self, extractor):
        """Test that when no LLM is configured, returns empty ContactInfo"""
        with patch('services.extraction_service.settings') as mock_settings:
            mock_settings.USE_YANDEXGPT = False
            mock_settings.USE_DEEPSEEK = False
            mock_settings.USE_OPENAI = False
            
            contacts, llm_data = extractor._extract_with_llm_selective(["test content"])
            
            assert isinstance(contacts, ContactInfo)
            assert llm_data is None
            assert len(contacts.emails) == 0
            assert len(contacts.telegram_links) == 0
            assert len(contacts.linkedin_links) == 0


class TestContactInfoValidation:
    """Test ContactInfo schema validation"""
    
    def test_contact_info_creation_with_valid_data(self):
        """Test creating ContactInfo with valid data"""
        contact = ContactInfo(
            emails=["test@company.com"],
            telegram_links=["https://t.me/test"],
            linkedin_links=["https://linkedin.com/in/test"],
            phone_numbers=["+1234567890"]
        )
        
        assert contact.emails == ["test@company.com"]
        assert contact.telegram_links == ["https://t.me/test"]
        assert contact.linkedin_links == ["https://linkedin.com/in/test"]
        assert contact.phone_numbers == ["+1234567890"]
    
    def test_contact_info_creation_with_empty_lists(self):
        """Test creating ContactInfo with empty lists"""
        contact = ContactInfo()
        
        assert contact.emails == []
        assert contact.telegram_links == []
        assert contact.linkedin_links == []
        assert contact.phone_numbers == []
    
    def test_contact_info_with_none_values(self):
        """Test creating ContactInfo handles None values"""
        with pytest.raises(ValidationError):
            ContactInfo(
                emails=None,
                telegram_links=None,
                linkedin_links=None,
                phone_numbers=None
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
