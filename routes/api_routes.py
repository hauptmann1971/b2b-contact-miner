import json
import os

import requests
from flask import Response, jsonify, request
from sqlalchemy import desc

from models.database import Contact, CrawlLog, DomainContact, Keyword, SearchResult, SessionLocal
from services.export_service import ExportService
from utils.web_security import admin_auth_required
from utils.web_stats import get_contact_type_counts


def register_api_routes(app, logger):
    @app.route("/api/llm-data")
    @admin_auth_required
    def api_llm_data():
        expected_token = os.getenv("LLM_DATA_API_TOKEN")
        provided_token = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "", 1).strip()
        if not expected_token or provided_token != expected_token:
            return jsonify({"error": "Unauthorized"}), 401

        def _sanitize(value):
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except Exception:
                    return value[:500]
            if isinstance(value, dict):
                redacted = {}
                for key, item in value.items():
                    key_lower = key.lower()
                    if any(token in key_lower for token in ["token", "secret", "password", "api_key", "authorization"]):
                        redacted[key] = "***REDACTED***"
                    else:
                        redacted[key] = _sanitize(item)
                return redacted
            if isinstance(value, list):
                return [_sanitize(item) for item in value[:50]]
            return value

        db = SessionLocal()
        try:
            total_search_results = db.query(SearchResult).count()
            total_crawl_logs = db.query(CrawlLog).count()
            llm_used_count = db.query(CrawlLog).filter(CrawlLog.llm_model.isnot(None)).count()
            domains_with_contacts = db.query(DomainContact).filter(DomainContact.contacts_json.isnot(None)).count()

            search_results = db.query(SearchResult).order_by(desc(SearchResult.id)).limit(50).all()
            search_results_data = [
                {
                    "id": sr.id,
                    "keyword_id": sr.keyword_id,
                    "url": sr.url,
                    "raw_search_query": _sanitize(sr.raw_search_query),
                    "raw_search_response": _sanitize(sr.raw_search_response),
                }
                for sr in search_results
            ]

            crawl_logs = db.query(CrawlLog).filter(CrawlLog.llm_model.isnot(None)).order_by(desc(CrawlLog.id)).limit(50).all()
            crawl_logs_data = [
                {"id": log.id, "domain": log.domain, "llm_model": log.llm_model, "llm_request": _sanitize(log.llm_request), "llm_response": _sanitize(log.llm_response)}
                for log in crawl_logs
            ]

            domain_contacts = db.query(DomainContact).filter(DomainContact.contacts_json.isnot(None)).order_by(desc(DomainContact.id)).limit(50).all()
            contacts_json_data = [{"id": dc.id, "domain": dc.domain, "contacts_json": _sanitize(dc.contacts_json)} for dc in domain_contacts]

            return jsonify(
                {
                    "stats": {
                        "total_search_results": total_search_results,
                        "total_crawl_logs": total_crawl_logs,
                        "llm_used_count": llm_used_count,
                        "domains_with_contacts": domains_with_contacts,
                    },
                    "search_results": search_results_data,
                    "crawl_logs": crawl_logs_data,
                    "contacts_json": contacts_json_data,
                }
            )
        finally:
            db.close()

    @app.route("/api/crawler-settings")
    def api_crawler_settings():
        from config.settings import settings

        return jsonify(
            {
                "domain_crawl_timeout": settings.DOMAIN_CRAWL_TIMEOUT,
                "request_timeout": settings.REQUEST_TIMEOUT,
                "max_pages_per_domain": settings.MAX_PAGES_PER_DOMAIN,
                "search_results_per_keyword": settings.SEARCH_RESULTS_PER_KEYWORD,
                "concurrent_browsers": settings.CONCURRENT_BROWSERS,
                "delay_between_requests": settings.DELAY_BETWEEN_REQUESTS,
            }
        )

    @app.route("/api/stats")
    def api_stats():
        db = SessionLocal()
        try:
            stats = {
                "total_keywords": db.query(Keyword).count(),
                "processed_keywords": db.query(Keyword).filter(Keyword.is_processed.is_(True)).count(),
                "total_domains": db.query(DomainContact).count(),
                "total_contacts": db.query(Contact).count(),
                "contacts_by_type": get_contact_type_counts(db),
            }
            return jsonify(stats)
        finally:
            db.close()

    @app.route("/api/keywords")
    def api_keywords():
        db = SessionLocal()
        try:
            keywords = db.query(Keyword).order_by(desc(Keyword.created_at)).all()
            return jsonify(
                [
                    {
                        "id": k.id,
                        "keyword": k.keyword,
                        "language": k.language,
                        "country": k.country,
                        "is_processed": k.is_processed,
                        "last_crawled_at": k.last_crawled_at.isoformat() if k.last_crawled_at else None,
                        "created_at": k.created_at.isoformat(),
                    }
                    for k in keywords
                ]
            )
        finally:
            db.close()

    @app.route("/api/export/flat-csv")
    def export_flat_csv():
        db = SessionLocal()
        try:
            csv_data = ExportService(db).export_to_flat_csv()
            return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=contacts_flat.csv"})
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()

    @app.route("/metrics/pipeline")
    @admin_auth_required
    def pipeline_metrics_proxy():
        """Proxy pipeline metrics from monitoring service to Flask app."""
        try:
            upstream = requests.get("http://127.0.0.1:8000/metrics/pipeline", timeout=5)
            content_type = upstream.headers.get("Content-Type", "application/json")
            return Response(upstream.content, status=upstream.status_code, content_type=content_type)
        except requests.RequestException as e:
            logger.warning(f"Metrics proxy unavailable: {e}")
            return jsonify({"error": "Monitoring service unavailable", "details": str(e)}), 503
