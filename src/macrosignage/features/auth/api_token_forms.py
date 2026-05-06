from __future__ import annotations

from .models import User


def api_token_form_data(form) -> tuple[dict[str, object], dict[str, str]]:
    errors: dict[str, str] = {}
    name = form.get("name", "").strip()
    user_id_raw = form.get("user_id", "").strip()
    user = None

    if not name:
        errors["name"] = "Token name is required."
    elif len(name) > 120:
        errors["name"] = "Token name cannot exceed 120 characters."

    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        user_id = 0
    if user_id:
        user = User.query.filter_by(id=user_id, active=True).first()
    if user is None:
        errors["user_id"] = "Choose an active token owner."

    return {"name": name, "user": user}, errors
