import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Response, flash, redirect, render_template, request, url_for
from sqlalchemy import desc, func

from models.database import CrawlLog, PipelineState, SessionLocal
from models.task_queue import TaskQueue
from models.tenant import Tenant, UserRole
from services.user_admin_service import (
    MANAGEABLE_ROLES,
    UserAdminError,
    create_tenant_user,
    list_tenant_users,
    set_user_active,
    set_user_password,
    update_user_role,
)
from utils.app_settings import get_default_theme, set_default_theme
from utils.auth_flow import handle_telegram_login_request
from utils.telegram_auth import get_bot_username, telegram_auth_configured
from utils.tenant_context import get_request_context_or_raise, scoped_query
from utils.web_security import auth_enabled, check_admin_auth, owner_required

ROLE_LABELS = {
    UserRole.VIEWER.value: "viewer — просмотр",
    UserRole.MEMBER.value: "member — редактирование",
    UserRole.OWNER.value: "owner — администратор",
}


def register_admin_routes(app):
    def _render_admin_login():
        return render_template(
            "admin_login.html",
            next_url=url_for("admin_dashboard"),
            telegram_bot_username=get_bot_username(),
            telegram_auth_enabled=telegram_auth_configured(),
        )

    def _admin_login_required_response():
        if not auth_enabled():
            return Response("Authentication is not configured.", 503)
        if request.authorization:
            return Response(
                "Authentication required",
                401,
                {"WWW-Authenticate": 'Basic realm="B2B Contact Miner"'},
            )
        return _render_admin_login()

    @app.route("/admin")
    def admin_dashboard():
        if request.args.get("id") and request.args.get("hash"):
            return handle_telegram_login_request(
                url_for("admin_dashboard"),
                error_route="admin_dashboard",
            )

        if not check_admin_auth():
            return _admin_login_required_response()

        db = SessionLocal()
        try:
            ctx = get_request_context_or_raise()
            task_q = scoped_query(db, TaskQueue, ctx)
            task_stats_rows = task_q.with_entities(TaskQueue.status, func.count(TaskQueue.id)).group_by(TaskQueue.status).all()
            task_stats = {status: count for status, count in task_stats_rows}
            total_tasks = sum(task_stats.values())

            from config.settings import settings

            now_ts = datetime.now(timezone.utc).timestamp()
            stale_tasks = []
            running_tasks = (
                task_q.filter(TaskQueue.status == "running", TaskQueue.locked_at.isnot(None))
                .order_by(desc(TaskQueue.locked_at))
                .all()
            )
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

            failed_tasks = task_q.filter(TaskQueue.status == "failed").order_by(desc(TaskQueue.created_at)).limit(10).all()
            latest_runs = scoped_query(db, PipelineState, ctx).order_by(desc(PipelineState.started_at)).limit(10).all()
            crawl_q = scoped_query(db, CrawlLog, ctx)
            recent_crawl_errors = (
                crawl_q.filter(CrawlLog.error_message.isnot(None)).order_by(desc(CrawlLog.crawled_at)).limit(10).all()
            )

            smoke_reports_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent / "artifacts" / "smoke-reports"
            smoke_reports = []
            if smoke_reports_dir.exists():
                for report in sorted(smoke_reports_dir.glob("smoke_quality_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
                    smoke_reports.append(
                        {"name": report.name, "path": str(report), "modified_at": datetime.fromtimestamp(report.stat().st_mtime, tz=timezone.utc)}
                    )

            return render_template(
                "admin.html",
                task_stats=task_stats,
                total_tasks=total_tasks,
                running_tasks=running_tasks[:10],
                stale_tasks=stale_tasks[:10],
                failed_tasks=failed_tasks,
                latest_runs=latest_runs,
                recent_crawl_errors=recent_crawl_errors,
                smoke_reports=smoke_reports,
                active_worker_locks=len(running_tasks),
                oldest_lock_minutes=round(oldest_lock_minutes, 1),
                default_theme=get_default_theme(),
            )
        finally:
            db.close()

    @app.route("/admin/actions/recover-stale", methods=["POST"])
    @owner_required
    def admin_recover_stale():
        db = SessionLocal()
        try:
            ctx = get_request_context_or_raise()
            from config.settings import settings

            timeout_threshold = datetime.now(timezone.utc).timestamp() - settings.TASK_LOCK_TIMEOUT
            stale_tasks = scoped_query(db, TaskQueue, ctx).filter(TaskQueue.status == "running", TaskQueue.locked_at.isnot(None)).all()
            recovered = 0
            for task in stale_tasks:
                try:
                    if task.locked_at and task.locked_at.timestamp() < timeout_threshold:
                        task.status = "pending"
                        task.locked_by = None
                        task.locked_at = None
                        task.error_message = "Recovered manually from admin console stale state"
                        recovered += 1
                except Exception:
                    continue
            db.commit()
            flash(f"Recovered stale tasks: {recovered}", "success")
        except Exception as e:
            db.rollback()
            flash(f"Failed to recover stale tasks: {e}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/actions/retry-failed", methods=["POST"])
    @owner_required
    def admin_retry_failed():
        db = SessionLocal()
        try:
            ctx = get_request_context_or_raise()
            limit = request.form.get("limit", 20, type=int)
            limit = max(1, min(limit, 200))
            failed_tasks = scoped_query(db, TaskQueue, ctx).filter(TaskQueue.status == "failed").order_by(desc(TaskQueue.created_at)).limit(limit).all()
            retried = 0
            for task in failed_tasks:
                task.status = "pending"
                task.completed_at = None
                task.locked_by = None
                task.locked_at = None
                retried += 1
            db.commit()
            flash(f"Requeued failed tasks: {retried}", "success")
        except Exception as e:
            db.rollback()
            flash(f"Failed to requeue failed tasks: {e}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_dashboard"))

    @app.route("/llm-data")
    @owner_required
    def llm_data_page():
        return render_template("llm_data.html")

    @app.route("/api-docs")
    @owner_required
    def api_docs_page():
        return render_template("api_docs.html")

    @app.route("/admin/settings/password", methods=["POST"])
    @owner_required
    def admin_change_password():
        from models.tenant import User
        from werkzeug.security import check_password_hash, generate_password_hash

        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        if new_password != confirm_password:
            flash("Новый пароль и подтверждение не совпадают", "error")
            return redirect(url_for("admin_dashboard"))
        if len(new_password) < 8:
            flash("Новый пароль должен быть не короче 8 символов", "error")
            return redirect(url_for("admin_dashboard"))
        ctx = get_request_context_or_raise()
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == ctx.user_id).first()
            if not user or not user.password_hash or not check_password_hash(user.password_hash, current_password):
                flash("Текущий пароль неверный", "error")
                return redirect(url_for("admin_dashboard"))
            user.password_hash = generate_password_hash(new_password)
            db.commit()
            flash("Пароль обновлён", "success")
        finally:
            db.close()
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/users")
    @owner_required
    def admin_users_page():
        ctx = get_request_context_or_raise()
        db = SessionLocal()
        try:
            tenant = db.query(Tenant).filter(Tenant.id == ctx.tenant_id).first()
            users = list_tenant_users(db, ctx.tenant_id)
            return render_template(
                "admin_users.html",
                users=users,
                tenant_name=tenant.name if tenant else ctx.tenant_id,
                manageable_roles=MANAGEABLE_ROLES,
                role_labels=ROLE_LABELS,
                current_user_id=ctx.user_id,
                telegram_bot_username=get_bot_username(),
            )
        finally:
            db.close()

    @app.route("/admin/users/create", methods=["POST"])
    @owner_required
    def admin_users_create():
        ctx = get_request_context_or_raise()
        telegram_raw = request.form.get("telegram_id", "").strip()
        telegram_id = int(telegram_raw) if telegram_raw.isdigit() else None
        db = SessionLocal()
        try:
            create_tenant_user(
                db,
                tenant_id=ctx.tenant_id,
                username=request.form.get("username", ""),
                display_name=request.form.get("display_name", ""),
                role=request.form.get("role", ""),
                password=request.form.get("password", ""),
                telegram_id=telegram_id,
            )
            flash("Пользователь создан", "success")
        except UserAdminError as e:
            flash(str(e), "error")
        except Exception as e:
            db.rollback()
            flash(f"Ошибка создания пользователя: {e}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_users_page"))

    @app.route("/admin/users/<int:user_id>/role", methods=["POST"])
    @owner_required
    def admin_users_update_role(user_id: int):
        ctx = get_request_context_or_raise()
        db = SessionLocal()
        try:
            update_user_role(
                db,
                tenant_id=ctx.tenant_id,
                user_id=user_id,
                role=request.form.get("role", ""),
                actor_user_id=ctx.user_id,
            )
            flash("Роль обновлена", "success")
        except UserAdminError as e:
            flash(str(e), "error")
        except Exception as e:
            db.rollback()
            flash(f"Ошибка смены роли: {e}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_users_page"))

    @app.route("/admin/users/<int:user_id>/active", methods=["POST"])
    @owner_required
    def admin_users_set_active(user_id: int):
        ctx = get_request_context_or_raise()
        is_active = request.form.get("is_active", "0") == "1"
        db = SessionLocal()
        try:
            set_user_active(
                db,
                tenant_id=ctx.tenant_id,
                user_id=user_id,
                is_active=is_active,
                actor_user_id=ctx.user_id,
            )
            flash("Статус пользователя обновлён", "success")
        except UserAdminError as e:
            flash(str(e), "error")
        except Exception as e:
            db.rollback()
            flash(f"Ошибка изменения статуса: {e}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_users_page"))

    @app.route("/admin/users/<int:user_id>/password", methods=["POST"])
    @owner_required
    def admin_users_set_password(user_id: int):
        ctx = get_request_context_or_raise()
        db = SessionLocal()
        try:
            set_user_password(
                db,
                tenant_id=ctx.tenant_id,
                user_id=user_id,
                password=request.form.get("password", ""),
            )
            flash("Пароль обновлён", "success")
        except UserAdminError as e:
            flash(str(e), "error")
        except Exception as e:
            db.rollback()
            flash(f"Ошибка смены пароля: {e}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_users_page"))

    @app.route("/admin/settings/theme", methods=["POST"])
    @owner_required
    def admin_change_theme():
        theme = (request.form.get("theme") or "").strip()
        ok, message = set_default_theme(theme)
        flash(message, "success" if ok else "error")
        return redirect(url_for("admin_dashboard"))
