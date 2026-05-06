from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from macrosignage.extensions import db

from .models import User


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="scrypt")


def verify_password(user: User, password: str) -> bool:
    return check_password_hash(user.password_hash, password)


def apply_user_data(user: User, data: dict[str, object]) -> None:
    user.username = str(data["username"])
    user.email = str(data["email"])
    user.role = str(data["role"])
    user.active = bool(data["active"])
    if data.get("password"):
        user.password_hash = hash_password(str(data["password"]))


def authenticate_user(identifier: str, password: str) -> User | None:
    normalized = identifier.strip().lower()
    user = User.query.filter(
        or_(
            db.func.lower(User.email) == normalized,
            db.func.lower(User.username) == normalized,
        )
    ).first()
    if user is None or not user.active or not verify_password(user, password):
        return None
    return user


def count_users() -> int:
    return User.query.count()


def count_admin_users(exclude_user_id: int | None = None) -> int:
    query = User.query.filter_by(role="ADMIN", active=True)
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)
    return query.count()


def get_user(user_id: int) -> User:
    return db.get_or_404(User, user_id)


def list_users(search_query: str = "", role_filter: str = "") -> list[User]:
    query = User.query
    if search_query:
        like_query = f"%{search_query}%"
        query = query.filter(
            or_(
                User.username.ilike(like_query),
                User.email.ilike(like_query),
            )
        )
    if role_filter:
        query = query.filter_by(role=role_filter)
    return query.order_by(User.username.asc()).all()


def user_conflict_errors(user: User, errors: dict[str, str]) -> None:
    user_data_conflict_errors(
        user_id=user.id,
        username=user.username,
        email=user.email,
        errors=errors,
    )


def user_data_conflict_errors(
    user_id: int | None,
    username: str,
    email: str,
    errors: dict[str, str],
) -> None:
    existing_username = User.query.filter(
        db.func.lower(User.username) == username.lower(),
        User.id != user_id,
    ).first()
    if existing_username:
        errors["username"] = "Username is already in use."

    existing_email = User.query.filter(
        db.func.lower(User.email) == email.lower(),
        User.id != user_id,
    ).first()
    if existing_email:
        errors["email"] = "Email is already in use."


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_password_reset_token(user: User) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=current_app.config["AUTH_RESET_TOKEN_HOURS"]
    )
    user.reset_token_hash = token_hash(token)
    user.reset_token_expires_at = expires_at
    db.session.commit()
    return token


def find_user_by_reset_token(token: str) -> User | None:
    hashed = token_hash(token)
    user = User.query.filter_by(reset_token_hash=hashed).first()
    if user is None or user.reset_token_expires_at is None:
        return None

    expires_at = user.reset_token_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None

    return user


def reset_user_password(user: User, password: str) -> None:
    user.password_hash = hash_password(password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    db.session.commit()
