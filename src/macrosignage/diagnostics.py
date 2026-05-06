from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit

from flask import current_app
from sqlalchemy import text

from .extensions import db

DEVELOPMENT_SECRET_KEY = "dev-secret-key-change-me"


def redacted_database_label(uri: str | None) -> str:
    if not uri:
        return "Not configured"
    if uri.startswith("sqlite:///"):
        return f"SQLite / {uri.removeprefix('sqlite:///')}"

    parsed = urlsplit(uri)
    if parsed.scheme and parsed.hostname:
        port = f":{parsed.port}" if parsed.port else ""
        database = parsed.path.strip("/") or "default"
        return f"{parsed.scheme} / {parsed.hostname}{port}/{database}"
    if parsed.scheme:
        return f"{parsed.scheme} / configured"
    return "Configured"


def database_check() -> dict[str, object]:
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        current_app.logger.exception("Database readiness check failed")
        return {"status": "error", "ready": False}
    return {"status": "ok", "ready": True}


def media_storage_check() -> dict[str, object]:
    folder = Path(current_app.config.get("MEDIA_UPLOAD_FOLDER", ""))
    exists = folder.exists()
    writable = exists and os.access(folder, os.W_OK)
    return {
        "status": "ok" if exists and writable else "error",
        "ready": exists and writable,
        "configured": bool(str(folder)),
        "exists": exists,
        "writable": writable,
    }


def secret_key_status() -> str:
    secret_key = str(current_app.config.get("SECRET_KEY") or "")
    if secret_key and secret_key != DEVELOPMENT_SECRET_KEY:
        return "Configured"
    return "Using development default"


def production_config_status() -> dict[str, object]:
    return {
        "secretKey": secret_key_status(),
        "sessionCookieSecure": bool(current_app.config.get("SESSION_COOKIE_SECURE")),
        "hstsEnabled": bool(current_app.config.get("MACROSIGNAGE_ENABLE_HSTS"))
        or bool(current_app.config.get("SESSION_COOKIE_SECURE")),
        "productionMode": bool(current_app.config.get("MACROSIGNAGE_PRODUCTION")),
        "warnings": list(current_app.config.get("MACROSIGNAGE_CONFIG_WARNINGS", [])),
    }


def health_payload(content_version: int) -> dict[str, object]:
    database = database_check()
    media_storage = media_storage_check()
    ready = bool(database["ready"] and media_storage["ready"])
    return {
        "status": "ok" if ready else "degraded",
        "ready": ready,
        "version": current_app.config.get("APP_VERSION", "Unknown"),
        "contentVersion": content_version,
        "playerUpdates": {"contentVersion": content_version},
        "checks": {
            "database": database,
            "mediaStorage": media_storage,
        },
    }


def settings_diagnostics(content_version: int) -> list[tuple[str, str]]:
    payload = health_payload(content_version)
    config = production_config_status()
    return [
        ("Application version", str(payload["version"])),
        ("Health status", "Ready" if payload["ready"] else "Degraded"),
        ("Database readiness", "Ready" if payload["checks"]["database"]["ready"] else "Unavailable"),
        ("Media storage", "Writable" if payload["checks"]["mediaStorage"]["writable"] else "Unavailable"),
        ("Secret key", str(config["secretKey"])),
        ("Secure session cookie", "Enabled" if config["sessionCookieSecure"] else "Disabled"),
        ("HSTS", "Enabled" if config["hstsEnabled"] else "Disabled"),
        ("Content version", str(content_version)),
        ("Player update state", f"Content version {content_version}"),
    ]
