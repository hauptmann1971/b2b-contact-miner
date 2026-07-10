from flask import flash, redirect, url_for

from models.database import SessionLocal
from services.auth_service import find_user_by_telegram_id
from utils.telegram_auth import telegram_auth_configured, verify_telegram_login
from utils.web_security import _safe_next_url, login_user


def handle_telegram_login_request(default_next: str, *, error_route: str = "login_page"):
    from flask import request

    data = {k: request.args.get(k) for k in request.args if k != "next"}
    next_url = _safe_next_url(request.args.get("next") or default_next)

    if not telegram_auth_configured():
        flash("Telegram-авторизация не настроена", "error")
        return redirect(url_for(error_route, next=next_url))

    if not verify_telegram_login(data):
        flash("Не удалось подтвердить вход через Telegram", "error")
        return redirect(url_for(error_route, next=next_url))

    db = SessionLocal()
    try:
        user = find_user_by_telegram_id(db, int(data["id"]))
        if not user:
            flash("Telegram-аккаунт не привязан к пользователю. Обратитесь к администратору.", "error")
            return redirect(url_for(error_route, next=next_url))
        login_user(user, auth_method="telegram")
    finally:
        db.close()

    flash("Вход через Telegram выполнен", "success")
    return redirect(next_url)
