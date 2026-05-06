from __future__ import annotations

from datetime import datetime, timezone

from flask_login import UserMixin

from macrosignage.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(24), nullable=False, default="ADMIN")
    active = db.Column(db.Boolean, nullable=False, default=True)
    reset_token_hash = db.Column(db.String(64), nullable=True, index=True)
    reset_token_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def is_active(self) -> bool:
        return self.active

    @property
    def is_admin(self) -> bool:
        return self.role == "ADMIN"
