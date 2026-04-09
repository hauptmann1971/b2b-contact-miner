"""
Manual tests without pytest dependency
Run this to verify extraction logic works correctly
"""
import re
import sys
from services.extraction_service import ExtractionService
from models.schemas import ContactInfo


def test_mailto_extraction():
    """Test email extraction from mailto links"""
    service = ExtractionService()
    content = '<a href="mailto:ceo@company.com">Email</a>'
    contacts = service.extract_contacts([{"content": content, "type": "regular_page"}])
    assert "ceo@company.com" in contacts.emails, f"Expected ceo@company.com, got {contacts.emails}"
    print("✅ Test 1 passed: mailto extraction")


def test_mailto_with_parameters():
    """Test mailto with subject parameter - should strip query params"""
    service = ExtractionService()
    content = '<a href="mailto:info@company.com?subject=Hello">Contact</a>'
    contacts = service.extract_contacts([{"content": content, "type": "regular_page"}])
    assert "info@company.com" in contacts.emails, f"Expected info@company.com, got {contacts.emails}"
    assert not any("?" in email for email in contacts.emails), "Query params should be stripped"
    print("✅ Test 2 passed: mailto with parameters")


def test_obfuscated_email_detection():
    """Test detection of obfuscated emails"""
    service = ExtractionService()
    content = "Contact us: ceo[at]company.com"
    has_obfuscation = any(re.search(p, content, re.IGNORECASE) 
                         for p in service.obfuscation_patterns)
    assert has_obfuscation is True, "Should detect [at] obfuscation"
    print("✅ Test 3 passed: obfuscated email detection")


def test_regular_email_extraction():
    """Test regular email extraction"""
    service = ExtractionService()
    content = "Contact: john.doe@company.com or jane@business.org"
    contacts = service.extract_contacts([{"content": content, "type": "regular_page"}])
    assert "john.doe@company.com" in contacts.emails, f"Expected john.doe@company.com"
    assert "jane@business.org" in contacts.emails, f"Expected jane@business.org"
    print("✅ Test 4 passed: regular email extraction")


def test_blocked_emails_filtered():
    """Test that blocked emails are filtered out"""
    service = ExtractionService()
    content = """
        noreply@company.com
        support@company.com
        admin@company.com
        valid.person@company.com
    """
    contacts = service.extract_contacts([{"content": content, "type": "regular_page"}])
    
    assert "noreply@company.com" not in contacts.emails, "noreply should be blocked"
    assert "support@company.com" not in contacts.emails, "support should be blocked"
    assert "admin@company.com" not in contacts.emails, "admin should be blocked"
    assert "valid.person@company.com" in contacts.emails, "valid email should pass"
    print("✅ Test 5 passed: blocked emails filtered")


def test_free_email_providers_excluded():
    """Test that free email providers are excluded"""
    service = ExtractionService()
    content = """
        user@gmail.com
        person@yahoo.com
        contact@hotmail.com
        business@company.com
    """
    contacts = service.extract_contacts([{"content": content, "type": "regular_page"}])
    
    assert "user@gmail.com" not in contacts.emails, "gmail should be excluded"
    assert "person@yahoo.com" not in contacts.emails, "yahoo should be excluded"
    assert "contact@hotmail.com" not in contacts.emails, "hotmail should be excluded"
    assert "business@company.com" in contacts.emails, "business email should pass"
    print("✅ Test 6 passed: free email providers excluded")


def test_telegram_extraction():
    """Test Telegram link extraction"""
    service = ExtractionService()
    content = """
        Telegram: https://t.me/company_channel
        Contact: t.me/support_bot
    """
    contacts = service.extract_contacts([{"content": content, "type": "regular_page"}])
    
    assert "https://t.me/company_channel" in contacts.telegram_links, "Telegram link not found"
    assert "https://t.me/support_bot" in contacts.telegram_links, "Telegram bot not found"
    print("✅ Test 7 passed: telegram extraction")


def test_linkedin_extraction():
    """Test LinkedIn profile extraction"""
    service = ExtractionService()
    content = """
        LinkedIn: https://linkedin.com/in/john-doe
        Company: https://www.linkedin.com/company/acme-corp
    """
    contacts = service.extract_contacts([{"content": content, "type": "regular_page"}])
    
    assert len(contacts.linkedin_links) >= 2, f"Expected at least 2 LinkedIn links, got {len(contacts.linkedin_links)}"
    print("✅ Test 8 passed: linkedin extraction")


def test_confidence_score_calculation():
    """Test confidence score calculation"""
    service = ExtractionService()
    
    # High confidence: multiple emails + telegram + linkedin
    contacts = ContactInfo(
        emails=["ceo@company.com", "info@company.com"],
        telegram_links=["https://t.me/company"],
        linkedin_links=["https://linkedin.com/in/ceo"],
        phone_numbers=[]
    )
    score = service.calculate_confidence(contacts)
    assert score >= 90, f"Expected score >= 90, got {score}"
    
    # Medium confidence: single email
    contacts = ContactInfo(
        emails=["contact@company.com"],
        telegram_links=[],
        linkedin_links=[],
        phone_numbers=[]
    )
    score = service.calculate_confidence(contacts)
    assert score == 40, f"Expected score 40, got {score}"
    
    # Low confidence: only phone
    contacts = ContactInfo(
        emails=[],
        telegram_links=[],
        linkedin_links=[],
        phone_numbers=["+1234567890"]
    )
    score = service.calculate_confidence(contacts)
    assert score == 10, f"Expected score 10, got {score}"
    
    print("✅ Test 9 passed: confidence score calculation")


def test_empty_content():
    """Test extraction from empty content"""
    service = ExtractionService()
    contacts = service.extract_contacts([{"content": "", "type": "regular_page"}])
    
    assert len(contacts.emails) == 0, "Should have no emails"
    assert len(contacts.telegram_links) == 0, "Should have no telegrams"
    assert len(contacts.linkedin_links) == 0, "Should have no linkedins"
    print("✅ Test 10 passed: empty content handling")


def run_all_tests():
    """Run all manual tests"""
    print("="*60)
    print("Running Manual Tests (No pytest required)")
    print("="*60)
    print()
    
    tests = [
        test_mailto_extraction,
        test_mailto_with_parameters,
        test_obfuscated_email_detection,
        test_regular_email_extraction,
        test_blocked_emails_filtered,
        test_free_email_providers_excluded,
        test_telegram_extraction,
        test_linkedin_extraction,
        test_confidence_score_calculation,
        test_empty_content,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed += 1
    
    print()
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 All tests passed! Code is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the code.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
