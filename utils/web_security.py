import secrets
from functools import wraps
from urllib.parse import urlparse

from flask import Response, flash, g, jsonify, redirect, request, session, url_for

from models.database import SessionLocal
from models.tenant import User, UserRole
from services.auth_service import authenticate_password, find_user_by_telegram_id, verify_basic_user
from utils.app_settings import get_default_theme
from utils.telegram_auth import get_bot_username, telegram_auth_configured
from utils.tenant_context import RequestContext, get_request_context, load_context_from_session, set_request_context


def get_csrf_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def login_user(user: User, *, auth_method: str | None = None) -> None:
    session.pop("auth_logout", None)
    session["user_id"] = user.id
    session["tenant_id"] = user.tenant_id
    session["role"] = user.role.value
    session["auth_username"] = user.username
    if auth_method:
        session["auth_method"] = auth_method
    else:
        session["auth_method"] = "telegram" if user.telegram_id else "password"
    session["is_admin"] = user.role in {UserRole.SUPER_ADMIN, UserRole.OWNER}
    if user.telegram_id:
        session["telegram_user"] = {
            "id": user.telegram_id,
            "username": user.username,
            "first_name": user.display_name or user.username,
        }
    else:
        session.pop("telegram_user", None)
    session.permanent = True
    set_request_context(
        RequestContext(
            user_id=user.id,
            tenant_id=user.tenant_id,
            role=user.role,
            username=user.username,
            display_name=user.display_name or user.username,
        )
    )


def logout_user() -> None:
    session["auth_logout"] = True
    for key in ("user_id", "tenant_id", "role", "auth_username", "auth_method", "is_admin", "telegram_user"):
        session.pop(key, None)
    set_request_context(None)


def resolve_request_context() -> RequestContext | None:
    if session.get("auth_logout"):
        return None
    db = SessionLocal()
    try:
        ctx = load_context_from_session(db)
        if ctx:
            return ctx
        auth = request.authorization
        if auth and auth.username and auth.password:
            user = verify_basic_user(db, auth.username, auth.password)
            if user:
                login_user(user)
                return get_request_context()
        return None
    finally:
        db.close()


def check_admin_auth() -> bool:
    return get_request_context() is not None


def _auth_display_name(ctx: RequestContext | None) -> str | None:
    if not ctx:
        return None
    if ctx.role == UserRole.SUPER_ADMIN:
        return f"Super admin: {ctx.display_name}"
    return ctx.display_name


def inject_csrf_token():
    ctx = get_request_context()
    authenticated = ctx is not None
    return {
        "csrf_token": get_csrf_token,
        "default_theme": get_default_theme(),
        "telegram_bot_username": get_bot_username(),
        "telegram_auth_enabled": telegram_auth_configured(),
        "session_user": session.get("telegram_user"),
        "is_admin_session": bool(session.get("is_admin")),
        "is_authenticated": authenticated,
        "auth_can_logout": authenticated,
        "auth_display_name": _auth_display_name(ctx),
        "tenant_name": getattr(g, "tenant_name", None),
        "current_role": ctx.role.value if ctx else None,
    }


def bind_tenant_context():
    ctx = resolve_request_context()
    set_request_context(ctx)
    if ctx:
        db = SessionLocal()
        try:
            from models.tenant import Tenant

            tenant = db.query(Tenant).filter(Tenant.id == ctx.tenant_id).first()
            g.tenant_name = tenant.name if tenant else None
        finally:
            db.close()


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


def auth_enabled() -> bool:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.is_active.is_(True)).count() > 0 or telegram_auth_configured()
    finally:
        db.close()


def admin_auth_enabled() -> bool:
    return auth_enabled()


def _prefers_html_login() -> bool:
    if request.path.startswith("/api/") or request.path.startswith("/export/"):
        return False
    best = request.accept_mimetypes.best_match(["text/html", "application/json"])
    if best == "application/json":
        return False
    return request.method == "GET"


def _safe_next_url(next_url: str | None) -> str:
    if not next_url:
        return url_for("user_workspace")
    parsed = urlparse(next_url)
    if parsed.scheme or parsed.netloc:
        return url_for("user_workspace")
    if not next_url.startswith("/"):
        return url_for("user_workspace")
    return next_url


def _forbidden(message: str = "Forbidden"):
    if _prefers_html_login():
        flash(message, "error")
        return redirect(request.referrer or url_for("user_workspace"))
    return jsonify({"error": message}), 403


def _unauthorized():
    if not auth_enabled():
        return Response("Authentication is not configured.", 503)
    if request.authorization:
        return Response("Authentication required", 401, {"WWW-Authenticate": 'Basic realm="B2B Contact Miner"'})
    if _prefers_html_login():
        return redirect(url_for("login_page", next=request.full_path or request.path))
    return Response("Authentication required", 401, {"WWW-Authenticate": 'Basic realm="B2B Contact Miner"'})


def _role_required(*roles: UserRole):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            ctx = get_request_context() or resolve_request_context()
            if not ctx:
                return _unauthorized()
            if ctx.is_super_admin or ctx.role in roles:
                return view_func(*args, **kwargs)
            return _forbidden()

        return wrapped

    return decorator


login_required = _role_required(UserRole.VIEWER, UserRole.MEMBER, UserRole.OWNER, UserRole.SUPER_ADMIN)
viewer_required = login_required
member_required = _role_required(UserRole.MEMBER, UserRole.OWNER, UserRole.SUPER_ADMIN)
owner_required = _role_required(UserRole.OWNER, UserRole.SUPER_ADMIN)
admin_auth_required = owner_required
contacts_auth_required = viewer_required


def login_telegram_user(user_data: dict) -> None:
    db = SessionLocal()
    try:
        user = find_user_by_telegram_id(db, int(user_data["id"]))
        if user:
            login_user(user)
    finally:
        db.close()


def login_password_user(username: str, password: str) -> bool:
    db = SessionLocal()
    try:
        user = authenticate_password(db, username, password)
        if not user:
            return False
        login_user(user, auth_method="password")
        return True
    finally:
        db.close()
