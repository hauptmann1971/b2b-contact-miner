import os
import secrets
from functools import wraps

from flask import Response, jsonify, request, session


def get_csrf_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def inject_csrf_token():
    return {"csrf_token": get_csrf_token}


def validate_csrf_or_reject(app):
    if app.config.get("TESTING"):
        return None
    if request.method != "POST":
        return None

    sent_token = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
    session_token = session.get("_csrf_token")
    if not sent_token or not session_token or not secrets.compare_digest(sent_token, session_token):
        return jsonify({"error": "CSRF validation failed"}), 400
    return None


def admin_auth_enabled() -> bool:
    return bool(os.getenv("ADMIN_USERNAME") and os.getenv("ADMIN_PASSWORD"))


def check_admin_auth() -> bool:
    if not admin_auth_enabled():
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


def admin_auth_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if check_admin_auth():
            return view_func(*args, **kwargs)
        return Response(
            "Authentication required",
            401,
            {"WWW-Authenticate": 'Basic realm="Admin Console"'},
        )

    return wrapped
