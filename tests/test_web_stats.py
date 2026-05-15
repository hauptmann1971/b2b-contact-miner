from unittest.mock import MagicMock

from utils.web_stats import get_recent_contacts


def test_get_recent_contacts_maps_rows():
    db = MagicMock()
    db.execute.return_value.mappings.return_value.all.return_value = [
        {
            "contact_type": "email",
            "value": "a@example.com",
            "domain": "example.com",
            "created_at": None,
        }
    ]
    rows = get_recent_contacts(db, limit=5)
    assert len(rows) == 1
    assert rows[0]["value"] == "a@example.com"
    assert rows[0]["domain"] == "example.com"
