from datetime import datetime, timezone

from flask import render_template
from sqlalchemy import text

from models.database import SessionLocal


def register_health_routes(app):
    @app.route("/health-check")
    def health_check_page():
        return render_template("health.html")

    @app.route("/health")
    def health_check():
        db_status = "healthy"
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
        except Exception as e:
            db_status = f"unhealthy: {e}"

        status_code = 200 if db_status == "healthy" else 503
        return {
            "status": "healthy" if status_code == 200 else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": db_status,
            "web_server": "running",
            "monitoring_service": "not_available",
        }, status_code

    @app.route("/health/live")
    def liveness_check():
        return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}, 200

    @app.route("/health/ready")
    def readiness_check():
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()}, 200
        except Exception as e:
            return {"status": "not_ready", "timestamp": datetime.now(timezone.utc).isoformat(), "error": str(e)}, 503
