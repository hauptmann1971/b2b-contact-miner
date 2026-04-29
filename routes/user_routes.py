import re

from flask import current_app, flash, redirect, render_template, request, url_for
from sqlalchemy import desc, text

from models.database import Contact, DomainContact, Keyword, PipelineState, SearchResult, SessionLocal
from utils.web_stats import get_contact_type_counts

DEFAULT_LANGUAGES = ["ru", "en", "kk", "uz", "ky", "tg", "az", "hy", "ka", "be", "ro", "de", "fr"]
DEFAULT_COUNTRIES = ["RU", "KZ", "UZ", "KG", "TJ", "TM", "AZ", "AM", "GE", "BY", "MD", "UA", "MN", "AF", "PK", "US", "GB", "DE", "FR"]


def _sanitize_keyword_text(value: str) -> str:
    return value.replace("<", "").replace(">", "").replace('"', "").replace("'", "").strip()


def _normalize_language(value: str, fallback: str = "ru") -> str:
    value = (value or "").strip().lower()
    if re.fullmatch(r"[a-z]{2,8}", value):
        return value
    return fallback


def _normalize_country(value: str, fallback: str = "RU") -> str:
    value = (value or "").strip().upper()
    if re.fullmatch(r"[A-Z]{2,3}", value):
        return value
    return fallback


def _resolve_locale_from_form():
    selected_language = request.form.get("language", "ru")
    selected_country = request.form.get("country", "RU")
    custom_language = request.form.get("custom_language", "").strip()
    custom_country = request.form.get("custom_country", "").strip()
    language = _normalize_language(custom_language if selected_language == "__custom__" else selected_language)
    country = _normalize_country(custom_country if selected_country == "__custom__" else selected_country)
    return language, country


def _build_user_dashboard_context(db):
    total_keywords = db.query(Keyword).count()
    processed_keywords = db.query(Keyword).filter(Keyword.is_processed.is_(True)).count()
    total_domains = db.query(DomainContact).count()
    total_contacts = db.query(Contact).count()

    recent_keywords = db.query(Keyword).order_by(desc(Keyword.created_at)).limit(10).all()
    recent_runs = db.query(PipelineState).order_by(desc(PipelineState.started_at)).limit(10).all()
    recent_domains = (
        db.query(DomainContact)
        .filter(DomainContact.contacts_json.isnot(None))
        .order_by(desc(DomainContact.created_at))
        .limit(20)
        .all()
    )
    recent_contact_rows = []
    for domain_item in recent_domains:
        payload = domain_item.contacts_json or {}
        if not isinstance(payload, dict):
            continue
        for email in (payload.get("emails") or [])[:2]:
            recent_contact_rows.append({"contact_type": "email", "value": email, "domain": domain_item.domain, "created_at": domain_item.created_at})
        for tg in (payload.get("telegram") or [])[:2]:
            recent_contact_rows.append({"contact_type": "telegram", "value": tg, "domain": domain_item.domain, "created_at": domain_item.created_at})
        for li in (payload.get("linkedin") or [])[:2]:
            recent_contact_rows.append({"contact_type": "linkedin", "value": li, "domain": domain_item.domain, "created_at": domain_item.created_at})
        social_payload = payload.get("social") or {}
        if isinstance(social_payload, dict):
            for social_type, links in social_payload.items():
                for link in (links or [])[:1]:
                    recent_contact_rows.append({"contact_type": social_type, "value": link, "domain": domain_item.domain, "created_at": domain_item.created_at})
        if len(recent_contact_rows) >= 20:
            break

    type_counts = get_contact_type_counts(db)
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
        "email_count": type_counts["email"],
        "telegram_count": type_counts["telegram"],
        "linkedin_count": type_counts["linkedin"],
        "phone_count": type_counts["phone"],
        "recent_runs": recent_runs,
        "recent_contacts": recent_contact_rows[:20],
        "language_options": language_options,
        "country_options": country_options,
    }


def _db_session():
    factory = current_app.config.get("SESSION_LOCAL_FACTORY", SessionLocal)
    return factory()


def register_user_routes(app):
    @app.route("/")
    def index():
        return user_workspace()

    @app.route("/user")
    def user_workspace():
        db = _db_session()
        try:
            return render_template("index.html", **_build_user_dashboard_context(db))
        finally:
            db.close()

    @app.route("/add_keyword", methods=["POST"])
    def add_keyword():
        keyword_text = request.form.get("keyword", "").strip()
        language, country = _resolve_locale_from_form()
        if not keyword_text:
            flash("Ключевое слово не может быть пустым", "error")
            return redirect(url_for("index"))
        if len(keyword_text) > 500:
            flash("Ключевое слово слишком длинное (максимум 500 символов)", "error")
            return redirect(url_for("index"))

        keyword_text = _sanitize_keyword_text(keyword_text)
        db = _db_session()
        try:
            existing = db.query(Keyword).filter(Keyword.keyword == keyword_text).first()
            if existing:
                flash(f'Ключевое слово "{keyword_text}" уже существует', "warning")
                return redirect(url_for("index"))
            db.add(Keyword(keyword=keyword_text, language=language, country=country, is_processed=False))
            db.commit()
            flash(f'Ключевое слово "{keyword_text}" успешно добавлено!', "success")
            return redirect(url_for("index"))
        except Exception as e:
            db.rollback()
            flash(f"Ошибка при добавлении: {e}", "error")
            return redirect(url_for("index"))
        finally:
            db.close()

    @app.route("/add_keywords_bulk", methods=["POST"])
    def add_keywords_bulk():
        bulk_keywords = request.form.get("bulk_keywords", "")
        language, country = _resolve_locale_from_form()
        rows = []
        for line in bulk_keywords.splitlines():
            row = _sanitize_keyword_text(line)
            if row:
                rows.append(row[:500])
        if not rows:
            flash("Не найдено валидных ключевых слов для массового добавления", "error")
            return redirect(url_for("index"))
        rows = list(dict.fromkeys(rows))

        db = _db_session()
        try:
            existing = set(item[0] for item in db.query(Keyword.keyword).filter(Keyword.keyword.in_(rows)).all())
            added, skipped = 0, 0
            for row in rows:
                if row in existing:
                    skipped += 1
                    continue
                db.add(Keyword(keyword=row, language=language, country=country, is_processed=False))
                added += 1
            db.commit()
            flash(f"Массовое добавление завершено: добавлено {added}, пропущено {skipped}", "success")
        except Exception as e:
            db.rollback()
            flash(f"Ошибка массового добавления: {e}", "error")
        finally:
            db.close()
        return redirect(url_for("index"))

    @app.route("/keywords")
    def keywords_list():
        db = _db_session()
        try:
            page = request.args.get("page", 1, type=int)
            per_page = 20
            keywords_query = db.query(Keyword).order_by(desc(Keyword.created_at))
            total = keywords_query.count()
            keywords = keywords_query.offset((page - 1) * per_page).limit(per_page).all()
            return render_template("keywords.html", keywords=keywords, page=page, per_page=per_page, total=total)
        finally:
            db.close()

    @app.route("/keyword/<int:keyword_id>")
    def keyword_detail(keyword_id):
        db = _db_session()
        try:
            keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
            if not keyword:
                flash("Ключевое слово не найдено", "error")
                return redirect(url_for("keywords_list"))
            search_results = db.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).order_by(SearchResult.position).all()
            domain_contacts = []
            for sr in search_results:
                domains = db.query(DomainContact).filter(DomainContact.search_result_id == sr.id).all()
                for domain in domains:
                    contacts = db.query(Contact).filter(Contact.domain_contact_id == domain.id).all()
                    domain_contacts.append({"domain": domain, "contacts": contacts, "search_result": sr})
            return render_template("keyword_detail.html", keyword=keyword, search_results=search_results, domain_contacts=domain_contacts)
        finally:
            db.close()

    @app.route("/contacts")
    def contacts_list():
        db = _db_session()
        try:
            page = request.args.get("page", 1, type=int)
            per_page = 50
            contact_type = request.args.get("type", "")
            query = request.args.get("q", "").strip()
            where_parts = []
            params = {}
            if contact_type:
                where_parts.append("LOWER(c.contact_type) = :contact_type")
                params["contact_type"] = contact_type.lower()
            if query:
                where_parts.append("(c.value LIKE :q OR dc.domain LIKE :q OR k.keyword LIKE :q)")
                params["q"] = f"%{query}%"
            where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
            total_sql = text(
                f"""
                SELECT COUNT(*)
                FROM contacts c
                JOIN domain_contacts dc ON dc.id = c.domain_contact_id
                JOIN search_results sr ON sr.id = dc.search_result_id
                JOIN keywords k ON k.id = sr.keyword_id
                {where_sql}
                """
            )
            total = db.execute(total_sql, params).scalar() or 0
            params.update({"limit": per_page, "offset": (page - 1) * per_page})
            data_sql = text(
                f"""
                SELECT c.id, c.contact_type, c.value, c.is_verified, c.created_at,
                       dc.domain AS domain_name, k.id AS keyword_id, k.keyword AS keyword_text
                FROM contacts c
                JOIN domain_contacts dc ON dc.id = c.domain_contact_id
                JOIN search_results sr ON sr.id = dc.search_result_id
                JOIN keywords k ON k.id = sr.keyword_id
                {where_sql}
                ORDER BY c.created_at DESC
                LIMIT :limit OFFSET :offset
                """
            )
            contacts = db.execute(data_sql, params).mappings().all()
            return render_template(
                "contacts.html",
                contacts=contacts,
                page=page,
                per_page=per_page,
                total=total,
                selected_type=contact_type,
                q=query,
            )
        finally:
            db.close()

    @app.route("/delete_keyword/<int:keyword_id>", methods=["POST"])
    def delete_keyword(keyword_id):
        db = _db_session()
        try:
            keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
            if keyword:
                db.delete(keyword)
                db.commit()
                flash(f'Ключевое слово "{keyword.keyword}" удалено', "success")
            else:
                flash("Ключевое слово не найдено", "error")
        except Exception as e:
            db.rollback()
            flash(f"Ошибка при удалении: {e}", "error")
        finally:
            db.close()
        return redirect(url_for("keywords_list"))
