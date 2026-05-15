from services.extraction_service import ExtractionService


def test_json_ld_extracts_email():
    html = """
    <script type="application/ld+json">
    {"@type": "Organization", "email": "sales@acme-corp.com", "name": "Acme"}
    </script>
    """
    svc = ExtractionService()
    emails, tg, li = svc._extract_json_ld_contacts(html)
    assert "sales@acme-corp.com" in emails
