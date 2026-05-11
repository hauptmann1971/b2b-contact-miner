from types import SimpleNamespace

import pytest
from flask import Flask

from models.database import ContactType
from services.export_service import ExportService
from services.serp_service import SerpService


def test_api_keywords_allows_null_created_at(monkeypatch):
    import routes.api_routes as api_routes

    app = Flask(__name__)
    api_routes.register_api_routes(app, logger=SimpleNamespace(error=lambda *args, **kwargs: None))

    keyword = SimpleNamespace(
        id=1,
        keyword="test",
        language="ru",
        country="RU",
        is_processed=False,
        last_crawled_at=None,
        created_at=None,
    )

    class FakeQuery:
        def order_by(self, *_args, **_kwargs):
            return self

        def all(self):
            return [keyword]

    class FakeDb:
        def query(self, *_args, **_kwargs):
            return FakeQuery()

        def close(self):
            pass

    monkeypatch.setattr(api_routes, "SessionLocal", lambda: FakeDb())

    response = app.test_client().get("/api/keywords")

    assert response.status_code == 200
    assert response.get_json()[0]["created_at"] is None


def test_export_formats_missing_dates_and_malformed_tags(monkeypatch):
    domain_contact = SimpleNamespace(
        domain="example.com",
        confidence_score=90,
        extraction_method="regex",
        tags=["b2b", 42, None, "analytics"],
        created_at=None,
    )
    contact = SimpleNamespace(
        contact_type=ContactType.EMAIL,
        value="team@example.com",
        domain_contact=domain_contact,
    )
    service = ExportService(db=None)
    monkeypatch.setattr(service, "_query_contacts", lambda filters=None: [contact])

    csv_data = service.export_to_csv()

    assert "team@example.com" in csv_data
    assert "b2b; analytics" in csv_data
    assert "42" not in csv_data


def test_flat_export_subject_area_ignores_non_string_tags():
    service = ExportService(db=None)

    assert service._extract_subject_area(["b2b", 42, None, "analytics"]) == "analytics"


def test_negative_page_argument_normalizes_to_first_page():
    from routes.user_routes import _normalize_page_arg

    app = Flask(__name__)
    with app.test_request_context("/keywords?page=-5"):
        assert _normalize_page_arg() == 1


def test_health_check_closes_session_when_execute_fails(monkeypatch):
    import routes.health_routes as health_routes

    app = Flask(__name__)
    health_routes.register_health_routes(app)
    session = SimpleNamespace(closed=False)

    def execute(_query):
        raise RuntimeError("db down")

    def close():
        session.closed = True

    session.execute = execute
    session.close = close
    monkeypatch.setattr(health_routes, "SessionLocal", lambda: session)

    response = app.test_client().get("/health")

    assert response.status_code == 503
    assert session.closed is True


def test_serp_save_results_skips_blank_urls():
    service = SerpService.__new__(SerpService)

    class FakeDb:
        def __init__(self):
            self.added = []
            self.committed = False

        def query(self, *_args, **_kwargs):
            return self

        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return None

        def add(self, item):
            self.added.append(item)

        def commit(self):
            self.committed = True

    db = FakeDb()

    service.save_results(
        db,
        keyword_id=1,
        results=[
            {"url": "", "title": "missing"},
            {"url": " https://example.com ", "title": "valid"},
        ],
    )

    assert db.committed is True
    assert [item.url for item in db.added] == ["https://example.com"]


@pytest.mark.asyncio
async def test_add_task_preserves_session_creation_failure(monkeypatch):
    import workers.db_task_queue as queue_module

    def raise_db_error():
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(queue_module, "SessionLocal", raise_db_error)

    queue = queue_module.DatabaseTaskQueue(max_concurrent=1)
    with pytest.raises(RuntimeError, match="db unavailable"):
        await queue.add_task("search", "search_keyword", {"keyword_id": 1, "keyword": "test"})
