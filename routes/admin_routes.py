import os
from datetime import datetime, timezone
from pathlib import Path

from flask import flash, redirect, render_template, request, url_for
from sqlalchemy import desc, func

from models.database import CrawlLog, PipelineState, SessionLocal
from models.task_queue import TaskQueue
from utils.web_security import admin_auth_required


def register_admin_routes(app):
    @app.route("/admin")
    @admin_auth_required
    def admin_dashboard():
        db = SessionLocal()
        try:
            task_stats_rows = db.query(TaskQueue.status, func.count(TaskQueue.id)).group_by(TaskQueue.status).all()
            task_stats = {status: count for status, count in task_stats_rows}
            total_tasks = sum(task_stats.values())

            from config.settings import settings

            now_ts = datetime.now(timezone.utc).timestamp()
            stale_tasks = []
            running_tasks = (
                db.query(TaskQueue)
                .filter(TaskQueue.status == "running", TaskQueue.locked_at.isnot(None))
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

            failed_tasks = db.query(TaskQueue).filter(TaskQueue.status == "failed").order_by(desc(TaskQueue.created_at)).limit(10).all()
            latest_runs = db.query(PipelineState).order_by(desc(PipelineState.started_at)).limit(10).all()
            recent_crawl_errors = (
                db.query(CrawlLog).filter(CrawlLog.error_message.isnot(None)).order_by(desc(CrawlLog.crawled_at)).limit(10).all()
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
            )
        finally:
            db.close()

    @app.route("/admin/actions/recover-stale", methods=["POST"])
    @admin_auth_required
    def admin_recover_stale():
        db = SessionLocal()
        try:
            from config.settings import settings

            timeout_threshold = datetime.now(timezone.utc).timestamp() - settings.TASK_LOCK_TIMEOUT
            stale_tasks = db.query(TaskQueue).filter(TaskQueue.status == "running", TaskQueue.locked_at.isnot(None)).all()
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
    @admin_auth_required
    def admin_retry_failed():
        db = SessionLocal()
        try:
            limit = request.form.get("limit", 20, type=int)
            limit = max(1, min(limit, 200))
            failed_tasks = db.query(TaskQueue).filter(TaskQueue.status == "failed").order_by(desc(TaskQueue.created_at)).limit(limit).all()
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
    @admin_auth_required
    def llm_data_page():
        return render_template("llm_data.html")

    @app.route("/api-docs")
    @admin_auth_required
    def api_docs_page():
        return render_template("api_docs.html")
