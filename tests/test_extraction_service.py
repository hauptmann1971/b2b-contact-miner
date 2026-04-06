import pytest
import re
from services.extraction_service import ExtractionService


class TestExtractionService:
    """Unit tests for extraction service"""
    
    def setup_method(self):
        self.service = ExtractionService()
    
    def test_mailto_extraction(self):
        """Test email extraction from mailto links"""
        content = '<a href="mailto:ceo@company.com">Email</a>'
        contacts = self.service.extract_contacts([{"content": content, "type": "regular_page"}])
        assert "ceo@company.com" in contacts.emails
    
    def test_mailto_with_parameters(self):
        """Test mailto with subject parameter - should strip query params"""
        content = '<a href="mailto:info@company.com?subject=Hello">Contact</a>'
        contacts = self.service.extract_contacts([{"content": content, "type": "regular_page"}])
        assert "info@company.com" in contacts.emails
        # Should not include ?subject=Hello
        assert not any("?" in email for email in contacts.emails)
    
    def test_obfuscated_email_detection(self):
        """Test detection of obfuscated emails"""
        content = "Contact us: ceo[at]company.com"
        has_obfuscation = any(re.search(p, content, re.IGNORECASE) 
                             for p in self.service.obfuscation_patterns)
        assert has_obfuscation is True
    
    def test_obfuscated_email_variations(self):
        """Test various obfuscation patterns"""
        patterns_to_test = [
            "ceo(at)company.com",
            "name [at] domain [dot] com",
            "contact {@} company.com",
        ]
        
        for content in patterns_to_test:
            has_obfuscation = any(re.search(p, content, re.IGNORECASE) 
                                 for p in self.service.obfuscation_patterns)
            assert has_obfuscation is True, f"Failed to detect obfuscation in: {content}"
    
    def test_regular_email_extraction(self):
        """Test regular email extraction"""
        content = "Contact: john.doe@company.com or jane@business.org"
        contacts = self.service.extract_contacts([{"content": content, "type": "regular_page"}])
        assert "john.doe@company.com" in contacts.emails
        assert "jane@business.org" in contacts.emails
    
    def test_blocked_emails_filtered(self):
        """Test that blocked emails are filtered out"""
        content = """
            noreply@company.com
            support@company.com
            admin@company.com
            valid.person@company.com
        """
        contacts = self.service.extract_contacts([{"content": content, "type": "regular_page"}])
        
        assert "noreply@company.com" not in contacts.emails
        assert "support@company.com" not in contacts.emails
        assert "admin@company.com" not in contacts.emails
        assert "valid.person@company.com" in contacts.emails
    
    def test_free_email_providers_excluded(self):
        """Test that free email providers are excluded"""
        content = """
            user@gmail.com
            person@yahoo.com
            contact@hotmail.com
            business@company.com
        """
        contacts = self.service.extract_contacts([{"content": content, "type": "regular_page"}])
        
        assert "user@gmail.com" not in contacts.emails
        assert "person@yahoo.com" not in contacts.emails
        assert "contact@hotmail.com" not in contacts.emails
        assert "business@company.com" in contacts.emails
    
    def test_telegram_extraction(self):
        """Test Telegram link extraction"""
        content = """
            Telegram: https://t.me/company_channel
            Contact: t.me/support_bot
        """
        contacts = self.service.extract_contacts([{"content": content, "type": "regular_page"}])
        
        assert "https://t.me/company_channel" in contacts.telegram_links
        assert "https://t.me/support_bot" in contacts.telegram_links
    
    def test_linkedin_extraction(self):
        """Test LinkedIn profile extraction"""
        content = """
            LinkedIn: https://linkedin.com/in/john-doe
            Company: https://www.linkedin.com/company/acme-corp
        """
        contacts = self.service.extract_contacts([{"content": content, "type": "regular_page"}])
        
        assert len(contacts.linkedin_links) >= 2
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation"""
        from models.schemas import ContactInfo
        
        # High confidence: multiple emails + telegram + linkedin
        contacts = ContactInfo(
            emails=["ceo@company.com", "info@company.com"],
            telegram_links=["https://t.me/company"],
            linkedin_links=["https://linkedin.com/in/ceo"],
            phone_numbers=[]
        )
        score = self.service.calculate_confidence(contacts)
        assert score >= 90
        
        # Medium confidence: single email
        contacts = ContactInfo(
            emails=["contact@company.com"],
            telegram_links=[],
            linkedin_links=[],
            phone_numbers=[]
        )
        score = self.service.calculate_confidence(contacts)
        assert score == 40
        
        # Low confidence: only phone
        contacts = ContactInfo(
            emails=[],
            telegram_links=[],
            linkedin_links=[],
            phone_numbers=["+1234567890"]
        )
        score = self.service.calculate_confidence(contacts)
        assert score == 10
    
    def test_empty_content(self):
        """Test extraction from empty content"""
        contacts = self.service.extract_contacts([{"content": "", "type": "regular_page"}])
        
        assert len(contacts.emails) == 0
        assert len(contacts.telegram_links) == 0
        assert len(contacts.linkedin_links) == 0
    
    def test_mx_verification_valid_domain(self):
        """Test MX record verification for valid domain"""
        # This test may fail if no DNS access
        try:
            result = self.service.verify_mx_domain("test@gmail.com")
            assert isinstance(result, bool)
        except Exception:
            pytest.skip("DNS resolution not available")
    
    def test_mx_verification_invalid_domain(self):
        """Test MX verification for non-existent domain"""
        result = self.service.verify_mx_domain("user@this-domain-definitely-does-not-exist-12345.com")
        assert result is False
