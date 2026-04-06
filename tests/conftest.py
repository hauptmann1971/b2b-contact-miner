import pytest
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def sample_html_content():
    """Sample HTML content for testing"""
    return """
    <html>
    <body>
        <h1>Contact Us</h1>
        <p>Email: ceo@company.com</p>
        <p>Support: support@company.com</p>
        <a href="mailto:info@company.com">Email Us</a>
        <a href="https://t.me/company_channel">Telegram</a>
        <a href="https://linkedin.com/in/john-doe">LinkedIn</a>
        <p>Phone: +1-234-567-8900</p>
    </body>
    </html>
    """


@pytest.fixture
def obfuscated_email_content():
    """Content with obfuscated emails"""
    return """
    Contact us at: ceo[at]company.com
    Or reach out to: info (at) company (dot) com
    Telegram: t.me/support
    """


@pytest.fixture
def empty_content():
    """Empty content for edge case testing"""
    return ""
