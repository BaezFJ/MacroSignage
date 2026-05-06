from __future__ import annotations

from email_validator import EmailNotValidError, validate_email
from python_usernames import is_safe_username

USER_ROLES = {
    "ADMIN": "Admin",
    "EDITOR": "Editor",
    "VIEWER": "Viewer",
}

MIN_PASSWORD_LENGTH = 8


def normalize_email(value: str) -> tuple[str, str | None]:
    email = value.strip().lower()
    if not email:
        return "", "Email is required."

    try:
        return validate_email(email, check_deliverability=False).normalized.lower(), None
    except EmailNotValidError:
        return email, "Enter a valid email address."


def normalize_username(value: str) -> tuple[str, str | None]:
    username = value.strip()
    if not username:
        return "", "Username is required."
    if len(username) > 80:
        return username, "Username cannot exceed 80 characters."
    if not is_safe_username(username):
        return username, "Use letters, numbers, dots, underscores, or hyphens."
    return username, None


def validate_password(value: str, *, required: bool) -> str | None:
    if not value:
        return "Password is required." if required else None
    if len(value) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    return None


def login_form_data(form) -> tuple[dict[str, str], dict[str, str]]:
    errors: dict[str, str] = {}
    identifier = form.get("identifier", "").strip()
    password = form.get("password", "")

    if not identifier:
        errors["identifier"] = "Username or email is required."
    if not password:
        errors["password"] = "Password is required."

    return {"identifier": identifier, "password": password}, errors


def password_reset_request_form_data(form) -> tuple[dict[str, str], dict[str, str]]:
    email, email_error = normalize_email(form.get("email", ""))
    errors = {"email": email_error} if email_error else {}
    return {"email": email}, errors


def password_reset_form_data(form) -> tuple[dict[str, str], dict[str, str]]:
    password = form.get("password", "")
    confirm_password = form.get("confirm_password", "")
    errors: dict[str, str] = {}

    password_error = validate_password(password, required=True)
    if password_error:
        errors["password"] = password_error
    if password != confirm_password:
        errors["confirm_password"] = "Passwords must match."

    return {"password": password, "confirm_password": confirm_password}, errors


def user_form_data(form, *, require_password: bool) -> tuple[dict[str, object], dict[str, str]]:
    username, username_error = normalize_username(form.get("username", ""))
    email, email_error = normalize_email(form.get("email", ""))
    role = form.get("role", "VIEWER").strip()
    active = form.get("active") == "on"
    password = form.get("password", "")
    confirm_password = form.get("confirm_password", "")
    errors: dict[str, str] = {}

    if username_error:
        errors["username"] = username_error
    if email_error:
        errors["email"] = email_error
    if role not in USER_ROLES:
        errors["role"] = "Choose a valid role."

    password_error = validate_password(password, required=require_password)
    if password_error:
        errors["password"] = password_error
    if password or confirm_password:
        if password != confirm_password:
            errors["confirm_password"] = "Passwords must match."

    return (
        {
            "username": username,
            "email": email,
            "role": role,
            "active": active,
            "password": password,
        },
        errors,
    )
