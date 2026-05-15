from utils.serp_snippet import (
    extract_serp_snippet_contacts,
    snippet_has_actionable_contacts,
)


def test_snippet_email_detected():
    title = "Acme Corp"
    snippet = "Reach us at sales@acme-corp.example for partnerships"
    assert snippet_has_actionable_contacts(title, snippet)


def test_snippet_telegram_detected():
    snippet = "Join our channel https://t.me/acme_official for updates"
    assert snippet_has_actionable_contacts("Acme", snippet)


def test_snippet_empty_not_actionable():
    assert not snippet_has_actionable_contacts("News", "Read more about fintech trends")


def test_extract_serp_snippet_contacts():
    contacts, _ = extract_serp_snippet_contacts(
        "https://example.com",
        "Example",
        "Email: info@example.com",
    )
    assert "info@example.com" in contacts.emails
