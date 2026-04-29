from flask import Flask
import sys
import os
import secrets
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal, init_db
from routes.admin_routes import register_admin_routes
from routes.api_routes import register_api_routes
from routes.health_routes import register_health_routes
from routes.user_routes import register_user_routes
from utils.web_security import inject_csrf_token, validate_csrf_or_reject

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
logger = logging.getLogger(__name__)


@app.context_processor
def _inject_csrf_token():
    return inject_csrf_token()


@app.before_request
def validate_csrf():
    app.config["SESSION_LOCAL_FACTORY"] = SessionLocal
    return validate_csrf_or_reject(app)

register_user_routes(app)
register_admin_routes(app)
register_api_routes(app, logger)
register_health_routes(app)


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
