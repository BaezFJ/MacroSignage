from __future__ import annotations

from functools import wraps

from flask import abort
from flask_login import current_user, login_required


ROLE_ORDER = {
    "VIEWER": 1,
    "EDITOR": 2,
    "ADMIN": 3,
}

ADMIN_ONLY_ENDPOINTS = {
    "admin.manage_logo_settings",
    "admin.manage_database_settings",
    "admin.list_fonts",
    "admin.create_font",
    "admin.edit_font",
    "admin.delete_font",
    "admin_tokens.list_tokens",
    "admin_tokens.create_token",
    "admin_tokens.revoke_token",
    "admin_tokens.reset_token",
    "admin_tokens.delete_token",
    "admin_displays.rotate_display_player_token",
    "admin_displays.enable_display_player_token",
    "admin_displays.disable_display_player_token",
}

ADMIN_ONLY_PREFIXES = ("admin_users.", "admin_tokens.")
EDITOR_PREFIXES = ("admin_displays.", "admin_media.", "admin_schedules.")


def user_role_rank(user) -> int:
    if not getattr(user, "is_authenticated", False):
        return 0
    return ROLE_ORDER.get(getattr(user, "role", ""), 0)


def has_role(user, minimum_role: str) -> bool:
    return user_role_rank(user) >= ROLE_ORDER[minimum_role]


def current_user_can(minimum_role: str) -> bool:
    return has_role(current_user, minimum_role)


def role_required(minimum_role: str):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user_can(minimum_role):
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


admin_required = role_required("ADMIN")
editor_required = role_required("EDITOR")
viewer_required = role_required("VIEWER")


def required_admin_role(endpoint: str, method: str) -> str:
    if endpoint in ADMIN_ONLY_ENDPOINTS or endpoint.startswith(ADMIN_ONLY_PREFIXES):
        return "ADMIN"
    if endpoint.startswith(EDITOR_PREFIXES) and method not in {"GET", "HEAD", "OPTIONS"}:
        return "EDITOR"
    if endpoint.startswith("admin."):
        if method in {"GET", "HEAD", "OPTIONS"}:
            return "VIEWER"
        return "ADMIN"
    return "VIEWER"
