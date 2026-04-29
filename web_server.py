from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, Response
from sqlalchemy import func, desc, text
from datetime import datetime, timezone
import sys
import os
import secrets
import json
import logging
import re
from functools import wraps
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal, Keyword, SearchResult, DomainContact, Contact, CrawlLog, PipelineState, init_db
from models.task_queue import TaskQueue

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
logger = logging.getLogger(__name__)

DEFAULT_LANGUAGES = ['ru', 'en', 'kk', 'uz', 'ky', 'tg', 'az', 'hy', 'ka', 'be', 'ro', 'de', 'fr']
DEFAULT_COUNTRIES = ['RU', 'KZ', 'UZ', 'KG', 'TJ', 'TM', 'AZ', 'AM', 'GE', 'BY', 'MD', 'UA', 'MN', 'AF', 'PK', 'US', 'GB', 'DE', 'FR']


def _get_csrf_token() -> str:
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf_token'] = token
    return token


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": _get_csrf_token}


@app.before_request
def validate_csrf():
    if app.config.get("TESTING"):
        return
    if request.method != 'POST':
        return
    sent_token = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
    session_token = session.get('_csrf_token')
    if not sent_token or not session_token or not secrets.compare_digest(sent_token, session_token):
        return jsonify({"error": "CSRF validation failed"}), 400


def _admin_auth_enabled() -> bool:
    return bool(os.getenv("ADMIN_USERNAME") and os.getenv("ADMIN_PASSWORD"))


def _check_admin_auth() -> bool:
    if not _admin_auth_enabled():
        return True
    expected_user = os.getenv("ADMIN_USERNAME", "")
    expected_password = os.getenv("ADMIN_PASSWORD", "")
    auth = request.authorization
    if not auth:
        return False
    return (
        secrets.compare_digest(auth.username or "", expected_user)
        and secrets.compare_digest(auth.password or "", expected_password)
    )


def _admin_auth_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if _check_admin_auth():
            return view_func(*args, **kwargs)
        return Response(
            "Authentication required",
            401,
            {"WWW-Authenticate": 'Basic realm="Admin Console"'},
        )
    return wrapped


def _sanitize_keyword_text(value: str) -> str:
    return value.replace('<', '').replace('>', '').replace('"', '').replace("'", '').strip()


def _get_contact_type_counts(db):
    """Return contact type counters robustly for enum and legacy rows."""
    rows = db.execute(text("""
        SELECT LOWER(CAST(contact_type AS CHAR)) AS contact_type, COUNT(*) AS cnt
        FROM contacts
        GROUP BY LOWER(CAST(contact_type AS CHAR))
    """)).mappings().all()
    counts = {row["contact_type"]: int(row["cnt"]) for row in rows}
    return {
        "email": counts.get("email", 0),
        "telegram": counts.get("telegram", 0),
        "linkedin": counts.get("linkedin", 0),
        "phone": counts.get("phone", 0),
    }


def _normalize_language(value: str, fallback: str = 'ru') -> str:
    value = (value or '').strip().lower()
    if re.fullmatch(r'[a-z]{2,8}', value):
        return value
    return fallback


def _normalize_country(value: str, fallback: str = 'RU') -> str:
    value = (value or '').strip().upper()
    if re.fullmatch(r'[A-Z]{2,3}', value):
        return value
    return fallback


def _resolve_locale_from_form():
    selected_language = request.form.get('language', 'ru')
    selected_country = request.form.get('country', 'RU')
    custom_language = request.form.get('custom_language', '').strip()
    custom_country = request.form.get('custom_country', '').strip()
    language = _normalize_language(custom_language if selected_language == '__custom__' else selected_language)
    country = _normalize_country(custom_country if selected_country == '__custom__' else selected_country)
    return language, country


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.route('/')
def index():
    """User workspace landing page."""
    return user_workspace()


def _build_user_dashboard_context(db):
    """Collect data for user-facing dashboard."""
    # Получаем статистику
    total_keywords = db.query(Keyword).count()
    processed_keywords = db.query(Keyword).filter(Keyword.is_processed == True).count()
    total_domains = db.query(DomainContact).count()
    total_contacts = db.query(Contact).count()
    
    # Последние ключевые слова
    recent_keywords = db.query(Keyword).order_by(desc(Keyword.created_at)).limit(10).all()
    recent_runs = db.query(PipelineState).order_by(desc(PipelineState.started_at)).limit(10).all()
    recent_domains = db.query(DomainContact).filter(
        DomainContact.contacts_json.isnot(None)
    ).order_by(desc(DomainContact.created_at)).limit(20).all()
    recent_contact_rows = []
    for domain_item in recent_domains:
        payload = domain_item.contacts_json or {}
        if not isinstance(payload, dict):
            continue

        for email in (payload.get('emails') or [])[:2]:
            recent_contact_rows.append({
                'contact_type': 'email',
                'value': email,
                'domain': domain_item.domain,
                'created_at': domain_item.created_at
            })
        for tg in (payload.get('telegram') or [])[:2]:
            recent_contact_rows.append({
                'contact_type': 'telegram',
                'value': tg,
                'domain': domain_item.domain,
                'created_at': domain_item.created_at
            })
        for li in (payload.get('linkedin') or [])[:2]:
            recent_contact_rows.append({
                'contact_type': 'linkedin',
                'value': li,
                'domain': domain_item.domain,
                'created_at': domain_item.created_at
            })
        social_payload = payload.get('social') or {}
        if isinstance(social_payload, dict):
            for social_type, links in social_payload.items():
                for link in (links or [])[:1]:
                    recent_contact_rows.append({
                        'contact_type': social_type,
                        'value': link,
                        'domain': domain_item.domain,
                        'created_at': domain_item.created_at
                    })
        if len(recent_contact_rows) >= 20:
            break

    recent_contacts = recent_contact_rows[:20]
    
    # Статистика по типам контактов
    type_counts = _get_contact_type_counts(db)
    email_count = type_counts["email"]
    telegram_count = type_counts["telegram"]
    linkedin_count = type_counts["linkedin"]
    phone_count = type_counts["phone"]

    db_languages = [row[0] for row in db.query(Keyword.language).distinct().all() if row[0]]
    db_countries = [row[0] for row in db.query(Keyword.country).distinct().all() if row[0]]
    language_options = sorted(set(DEFAULT_LANGUAGES + db_languages))
    country_options = sorted(set(DEFAULT_COUNTRIES + db_countries))

    return {
        "total_keywords": total_keywords,
        "processed_keywords": processed_keywords,
        "total_domains": total_domains,
        "total_contacts": total_contacts,
        "recent_keywords": recent_keywords,
        "email_count": email_count,
        "telegram_count": telegram_count,
        "linkedin_count": linkedin_count,
        "phone_count": phone_count,
        "recent_runs": recent_runs,
        "recent_contacts": recent_contacts,
        "language_options": language_options,
        "country_options": country_options,
    }


@app.route('/user')
def user_workspace():
    """Отдельная user-страница (ввод, результаты, экспорт)."""
    db = SessionLocal()
    try:
        return render_template('index.html', **_build_user_dashboard_context(db))
    finally:
        db.close()


@app.route('/admin')
@_admin_auth_required
def admin_dashboard():
    """Отдельная admin-страница (мониторинг системы и воркеров)."""
    db = SessionLocal()
    try:
        task_stats_rows = db.query(
            TaskQueue.status,
            func.count(TaskQueue.id)
        ).group_by(TaskQueue.status).all()
        task_stats = {status: count for status, count in task_stats_rows}
        total_tasks = sum(task_stats.values())
        
        from config.settings import settings
        now_ts = datetime.now(timezone.utc).timestamp()
        stale_tasks = []
        running_tasks = db.query(TaskQueue).filter(
            TaskQueue.status == 'running',
            TaskQueue.locked_at.isnot(None)
        ).order_by(desc(TaskQueue.locked_at)).all()
        oldest_lock_minutes = 0.0
        for task in running_tasks:
            try:
                if task.locked_at:
                    lock_age_min = (datetime.now(timezone.utc) - task.locked_at).total_seconds() / 60
                    oldest_lock_minutes = max(oldest_lock_minutes, lock_age_min)
                if task.locked_at and task.locked_at.timestamp() < (now_ts - settings.TASK_LOCK_TIMEOUT):
                    stale_tasks.append(task)
            except Exception:
                continue

        failed_tasks = db.query(TaskQueue).filter(
            TaskQueue.status == 'failed'
        ).order_by(desc(TaskQueue.created_at)).limit(10).all()

        latest_runs = db.query(PipelineState).order_by(desc(PipelineState.started_at)).limit(10).all()
        recent_crawl_errors = db.query(CrawlLog).filter(
            CrawlLog.error_message.isnot(None)
        ).order_by(desc(CrawlLog.crawled_at)).limit(10).all()
        smoke_reports_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "artifacts" / "smoke-reports"
        smoke_reports = []
        if smoke_reports_dir.exists():
            for report in sorted(smoke_reports_dir.glob("smoke_quality_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
                smoke_reports.append({
                    "name": report.name,
                    "path": str(report),
                    "modified_at": datetime.fromtimestamp(report.stat().st_mtime, tz=timezone.utc)
                })

        return render_template(
            'admin.html',
            task_stats=task_stats,
            total_tasks=total_tasks,
            running_tasks=running_tasks[:10],
            stale_tasks=stale_tasks[:10],
            failed_tasks=failed_tasks,
            latest_runs=latest_runs,
            recent_crawl_errors=recent_crawl_errors,
            smoke_reports=smoke_reports,
            active_worker_locks=len(running_tasks),
            oldest_lock_minutes=round(oldest_lock_minutes, 1)
        )
    finally:
        db.close()


@app.route('/admin/actions/recover-stale', methods=['POST'])
@_admin_auth_required
def admin_recover_stale():
    """Recover stale running tasks by returning them to pending state."""
    db = SessionLocal()
    try:
        from config.settings import settings
        timeout_threshold = datetime.now(timezone.utc).timestamp() - settings.TASK_LOCK_TIMEOUT
        stale_tasks = db.query(TaskQueue).filter(
            TaskQueue.status == 'running',
            TaskQueue.locked_at.isnot(None)
        ).all()
        recovered = 0
        for task in stale_tasks:
            try:
                if task.locked_at and task.locked_at.timestamp() < timeout_threshold:
                    task.status = 'pending'
                    task.locked_by = None
                    task.locked_at = None
                    task.error_message = "Recovered manually from admin console stale state"
                    recovered += 1
            except Exception:
                continue
        db.commit()
        flash(f'Recovered stale tasks: {recovered}', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Failed to recover stale tasks: {e}', 'error')
    finally:
        db.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/actions/retry-failed', methods=['POST'])
@_admin_auth_required
def admin_retry_failed():
    """Move recent failed tasks back to pending for retry."""
    db = SessionLocal()
    try:
        limit = request.form.get('limit', 20, type=int)
        limit = max(1, min(limit, 200))
        failed_tasks = db.query(TaskQueue).filter(
            TaskQueue.status == 'failed'
        ).order_by(desc(TaskQueue.created_at)).limit(limit).all()

        retried = 0
        for task in failed_tasks:
            task.status = 'pending'
            task.completed_at = None
            task.locked_by = None
            task.locked_at = None
            # keep retry_count/error_message for traceability
            retried += 1
        db.commit()
        flash(f'Requeued failed tasks: {retried}', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Failed to requeue failed tasks: {e}', 'error')
    finally:
        db.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/add_keyword', methods=['POST'])
def add_keyword():
    """Добавление нового ключевого слова"""
    keyword_text = request.form.get('keyword', '').strip()
    language, country = _resolve_locale_from_form()
    
    # Валидация входных данных
    if not keyword_text:
        flash('Ключевое слово не может быть пустым', 'error')
        return redirect(url_for('index'))
    
    if len(keyword_text) > 500:
        flash('Ключевое слово слишком длинное (максимум 500 символов)', 'error')
        return redirect(url_for('index'))
    
    keyword_text = _sanitize_keyword_text(keyword_text)
    
    db = SessionLocal()
    try:
        # Проверяем, существует ли уже такое ключевое слово
        existing = db.query(Keyword).filter(Keyword.keyword == keyword_text).first()
        if existing:
            flash(f'Ключевое слово "{keyword_text}" уже существует', 'warning')
            return redirect(url_for('index'))
        
        # Создаем новое ключевое слово
        new_keyword = Keyword(
            keyword=keyword_text,
            language=language,
            country=country,
            is_processed=False
        )
        db.add(new_keyword)
        db.commit()
        
        flash(f'Ключевое слово "{keyword_text}" успешно добавлено!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db.rollback()
        flash(f'Ошибка при добавлении: {str(e)}', 'error')
        return redirect(url_for('index'))
    finally:
        db.close()


@app.route('/add_keywords_bulk', methods=['POST'])
def add_keywords_bulk():
    """Bulk add keywords from textarea."""
    bulk_keywords = request.form.get('bulk_keywords', '')
    language, country = _resolve_locale_from_form()

    rows = []
    for line in bulk_keywords.splitlines():
        row = _sanitize_keyword_text(line)
        if row:
            rows.append(row[:500])

    if not rows:
        flash('Не найдено валидных ключевых слов для массового добавления', 'error')
        return redirect(url_for('index'))

    rows = list(dict.fromkeys(rows))  # Deduplicate while preserving order

    db = SessionLocal()
    try:
        existing = set(
            item[0]
            for item in db.query(Keyword.keyword).filter(Keyword.keyword.in_(rows)).all()
        )
        added = 0
        skipped = 0
        for row in rows:
            if row in existing:
                skipped += 1
                continue
            db.add(Keyword(keyword=row, language=language, country=country, is_processed=False))
            added += 1
        db.commit()
        flash(f'Массовое добавление завершено: добавлено {added}, пропущено {skipped}', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Ошибка массового добавления: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('index'))


@app.route('/keywords')
def keywords_list():
    """Список всех ключевых слов"""
    db = SessionLocal()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        keywords_query = db.query(Keyword).order_by(desc(Keyword.created_at))
        total = keywords_query.count()
        keywords = keywords_query.offset((page - 1) * per_page).limit(per_page).all()
        
        return render_template('keywords.html', 
                             keywords=keywords, 
                             page=page, 
                             per_page=per_page, 
                             total=total)
    finally:
        db.close()


@app.route('/keyword/<int:keyword_id>')
def keyword_detail(keyword_id):
    """Детальная информация о ключевом слове"""
    db = SessionLocal()
    try:
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if not keyword:
            flash('Ключевое слово не найдено', 'error')
            return redirect(url_for('keywords_list'))
        
        # Получаем результаты поиска
        search_results = db.query(SearchResult).filter(
            SearchResult.keyword_id == keyword_id
        ).order_by(SearchResult.position).all()
        
        # Получаем домены и контакты
        domain_contacts = []
        for sr in search_results:
            domains = db.query(DomainContact).filter(
                DomainContact.search_result_id == sr.id
            ).all()
            for domain in domains:
                contacts = db.query(Contact).filter(
                    Contact.domain_contact_id == domain.id
                ).all()
                domain_contacts.append({
                    'domain': domain,
                    'contacts': contacts,
                    'search_result': sr
                })
        
        return render_template('keyword_detail.html',
                             keyword=keyword,
                             search_results=search_results,
                             domain_contacts=domain_contacts)
    finally:
        db.close()


@app.route('/contacts')
def contacts_list():
    """Список всех найденных контактов"""
    db = SessionLocal()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        contact_type = request.args.get('type', '')
        query = request.args.get('q', '').strip()

        where_parts = []
        params = {}
        if contact_type:
            where_parts.append("LOWER(c.contact_type) = :contact_type")
            params["contact_type"] = contact_type.lower()
        if query:
            where_parts.append("(c.value LIKE :q OR dc.domain LIKE :q OR k.keyword LIKE :q)")
            params["q"] = f"%{query}%"
        where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

        total_sql = text(f"""
            SELECT COUNT(*)
            FROM contacts c
            JOIN domain_contacts dc ON dc.id = c.domain_contact_id
            JOIN search_results sr ON sr.id = dc.search_result_id
            JOIN keywords k ON k.id = sr.keyword_id
            {where_sql}
        """)
        total = db.execute(total_sql, params).scalar() or 0

        params.update({"limit": per_page, "offset": (page - 1) * per_page})
        data_sql = text(f"""
            SELECT
                c.id,
                c.contact_type,
                c.value,
                c.is_verified,
                c.created_at,
                dc.domain AS domain_name,
                k.id AS keyword_id,
                k.keyword AS keyword_text
            FROM contacts c
            JOIN domain_contacts dc ON dc.id = c.domain_contact_id
            JOIN search_results sr ON sr.id = dc.search_result_id
            JOIN keywords k ON k.id = sr.keyword_id
            {where_sql}
            ORDER BY c.created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        contacts = db.execute(data_sql, params).mappings().all()
        
        return render_template('contacts.html',
                             contacts=contacts,
                             page=page,
                             per_page=per_page,
                             total=total,
                             selected_type=contact_type,
                             q=query)
    finally:
        db.close()


@app.route('/health-check')
def health_check_page():
    """Страница health check с визуальным интерфейсом"""
    return render_template('health.html')


@app.route('/llm-data')
@_admin_auth_required
def llm_data_page():
    """Страница для просмотра LLM и search данных"""
    return render_template('llm_data.html')


@app.route('/api/llm-data')
@_admin_auth_required
def api_llm_data():
    """API endpoint для получения LLM и search данных"""
    expected_token = os.getenv("LLM_DATA_API_TOKEN")
    provided_token = (
        request.headers.get("X-API-Key")
        or request.headers.get("Authorization", "").replace("Bearer ", "", 1).strip()
    )
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
        # Статистика
        total_search_results = db.query(SearchResult).count()
        total_crawl_logs = db.query(CrawlLog).count()
        llm_used_count = db.query(CrawlLog).filter(CrawlLog.llm_model.isnot(None)).count()
        domains_with_contacts = db.query(DomainContact).filter(DomainContact.contacts_json.isnot(None)).count()
        
        # Последние 50 поисковых результатов с raw_query и raw_response
        search_results = db.query(SearchResult).order_by(desc(SearchResult.id)).limit(50).all()
        search_results_data = [{
            'id': sr.id,
            'keyword_id': sr.keyword_id,
            'url': sr.url,
            'raw_search_query': _sanitize(sr.raw_search_query),
            'raw_search_response': _sanitize(sr.raw_search_response)
        } for sr in search_results]
        
        # Последние 50 crawl logs с LLM данными
        crawl_logs = db.query(CrawlLog).filter(
            CrawlLog.llm_model.isnot(None)
        ).order_by(desc(CrawlLog.id)).limit(50).all()
        crawl_logs_data = [{
            'id': log.id,
            'domain': log.domain,
            'llm_model': log.llm_model,
            'llm_request': _sanitize(log.llm_request),
            'llm_response': _sanitize(log.llm_response)
        } for log in crawl_logs]
        
        # Domain contacts с JSON
        domain_contacts = db.query(DomainContact).filter(
            DomainContact.contacts_json.isnot(None)
        ).order_by(desc(DomainContact.id)).limit(50).all()
        contacts_json_data = [{
            'id': dc.id,
            'domain': dc.domain,
            'contacts_json': _sanitize(dc.contacts_json)
        } for dc in domain_contacts]
        
        return jsonify({
            'stats': {
                'total_search_results': total_search_results,
                'total_crawl_logs': total_crawl_logs,
                'llm_used_count': llm_used_count,
                'domains_with_contacts': domains_with_contacts
            },
            'search_results': search_results_data,
            'crawl_logs': crawl_logs_data,
            'contacts_json': contacts_json_data
        })
    finally:
        db.close()


@app.route('/api-docs')
@_admin_auth_required
def api_docs_page():
    """Страница документации API"""
    return render_template('api_docs.html')


@app.route('/api/crawler-settings')
def api_crawler_settings():
    """API endpoint для получения настроек crawler"""
    from config.settings import settings
    return jsonify({
        'domain_crawl_timeout': settings.DOMAIN_CRAWL_TIMEOUT,
        'request_timeout': settings.REQUEST_TIMEOUT,
        'max_pages_per_domain': settings.MAX_PAGES_PER_DOMAIN,
        'search_results_per_keyword': settings.SEARCH_RESULTS_PER_KEYWORD,
        'concurrent_browsers': settings.CONCURRENT_BROWSERS,
        'delay_between_requests': settings.DELAY_BETWEEN_REQUESTS
    })


@app.route('/delete_keyword/<int:keyword_id>', methods=['POST'])
def delete_keyword(keyword_id):
    """Удаление ключевого слова"""
    db = SessionLocal()
    try:
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if keyword:
            db.delete(keyword)
            db.commit()
            flash(f'Ключевое слово "{keyword.keyword}" удалено', 'success')
        else:
            flash('Ключевое слово не найдено', 'error')
    except Exception as e:
        db.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'error')
    finally:
        db.close()
    
    return redirect(url_for('keywords_list'))


# Health Check Endpoints
@app.route('/health')
def health_check():
    """Полная проверка здоровья системы"""
    from sqlalchemy import text
    
    # Проверяем БД
    db_status = "healthy"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Возвращаем статус
    status_code = 200 if db_status == "healthy" else 503
    
    return {
        'status': 'healthy' if status_code == 200 else 'degraded',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'database': db_status,
        'web_server': 'running',
        'monitoring_service': 'not_available'
    }, status_code


@app.route('/health/live')
def liveness_check():
    """Проверка живости приложения"""
    return {
        'status': 'alive',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }, 200


@app.route('/health/ready')
def readiness_check():
    """Проверка готовности приложения"""
    # Проверяем подключение к БД
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {
            'status': 'ready',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, 200
    except Exception as e:
        return {
            'status': 'not_ready',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': str(e)
        }, 503


@app.route('/api/stats')
def api_stats():
    """API эндпоинт для получения статистики"""
    db = SessionLocal()
    try:
        type_counts = _get_contact_type_counts(db)
        stats = {
            'total_keywords': db.query(Keyword).count(),
            'processed_keywords': db.query(Keyword).filter(Keyword.is_processed == True).count(),
            'total_domains': db.query(DomainContact).count(),
            'total_contacts': db.query(Contact).count(),
            'contacts_by_type': type_counts
        }
        return jsonify(stats)
    finally:
        db.close()


@app.route('/api/keywords')
def api_keywords():
    """API эндпоинт для получения списка ключевых слов"""
    db = SessionLocal()
    try:
        keywords = db.query(Keyword).order_by(desc(Keyword.created_at)).all()
        return jsonify([{
            'id': k.id,
            'keyword': k.keyword,
            'language': k.language,
            'country': k.country,
            'is_processed': k.is_processed,
            'last_crawled_at': k.last_crawled_at.isoformat() if k.last_crawled_at else None,
            'created_at': k.created_at.isoformat()
        } for k in keywords])
    finally:
        db.close()


@app.route('/api/export/flat-csv')
def export_flat_csv():
    """Export contacts to flat CSV with keyword info"""
    from services.export_service import ExportService
    
    db = SessionLocal()
    try:
        export_service = ExportService(db)
        csv_data = export_service.export_to_flat_csv()
        
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=contacts_flat.csv'
            }
        )
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


if __name__ == '__main__':
    # Инициализация базы данных
    init_db()
    
    # Запуск Flask сервера
    # SECURITY: Bind to localhost only (not all interfaces)
    # Use host='0.0.0.0' only if external access is required with proper firewall rules
    app.run(
        host='127.0.0.1',  # Changed from '0.0.0.0' for security
        port=5000,
        debug=os.getenv("FLASK_DEBUG", "false").strip().lower() == "true"
    )
