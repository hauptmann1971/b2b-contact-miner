from flask import flash, redirect, render_template, request, url_for

from utils.app_settings import get_default_theme
from utils.auth_flow import handle_telegram_login_request
from utils.telegram_auth import get_bot_username, telegram_auth_configured
from utils.web_security import _safe_next_url, login_password_user, logout_user
from utils.basic_auth import verify_basic_auth


def register_auth_routes(app):
    @app.route("/login")
    def login_page():
        if request.args.get("id") and request.args.get("hash"):
            return handle_telegram_login_request(_safe_next_url(request.args.get("next")))

        next_url = _safe_next_url(request.args.get("next"))
        return render_template(
            "login.html",
            next_url=next_url,
            telegram_bot_username=get_bot_username(),
            telegram_auth_enabled=telegram_auth_configured(),
            default_theme=get_default_theme(),
        )

    @app.route("/auth/telegram/callback")
    def telegram_callback():
        return handle_telegram_login_request(url_for("admin_dashboard"))

    @app.route("/auth/login", methods=["POST"])
    def auth_login():
        from utils.web_security import login_password_user

        next_url = _safe_next_url(request.form.get("next"))
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not login_password_user(username, password):
            flash("Неверный логин или пароль", "error")
            return redirect(url_for("login_page", next=next_url))
        flash("Вход выполнен", "success")
        return redirect(next_url)

    @app.route("/auth/logout", methods=["POST"])
    def auth_logout():
        logout_user()
        flash("Вы вышли из системы", "success")
        return redirect(url_for("user_workspace"))

    @app.route("/auth/theme", methods=["POST"])
    def set_theme_preference():
        theme = (request.form.get("theme") or request.json.get("theme") if request.is_json else request.form.get("theme") or "").strip()
        if theme not in {"light", "dark"}:
            return {"ok": False, "error": "Unknown theme"}, 400
        if request.is_json:
            return {"ok": True, "theme": theme}
        flash(f"Тема переключена: {theme}", "success")
        return redirect(request.referrer or url_for("user_workspace"))
