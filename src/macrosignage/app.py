__version__ = "0.2.1"

import os
from os import PathLike

from flask import Flask, abort, redirect, request, url_for
from flask_login import current_user
from sqlalchemy import inspect, text

from .config import DATABASE_ENV_KEY, default_database_uri, load_environment
from .extensions import csrf, db, login_manager, migrate
from .features.auth.permissions import current_user_can, required_admin_role
from .web.routes import web_bp
from .features import features_bp


ADMIN_ENDPOINT_PREFIXES = (
    "admin.",
    "admin_displays.",
    "admin_media.",
    "admin_schedules.",
    "admin_users.",
    "admin_tokens.",
)
MUTATING_CONTENT_ENDPOINT_PREFIXES = (
    "admin.",
    "admin_displays.",
    "admin_media.",
    "admin_schedules.",
    "admin_tokens.",
    "api.",
)


def ensure_runtime_schema() -> None:
    inspector = inspect(db.engine)
    statements = []
    tables = set(inspector.get_table_names())

    if "media_slides" in tables:
        columns = {column["name"] for column in inspector.get_columns("media_slides")}
        if "text_font_family" not in columns:
            statements.append("ALTER TABLE media_slides ADD COLUMN text_font_family VARCHAR(80) NOT NULL DEFAULT 'Inter'")
        if "text_font_size" not in columns:
            statements.append("ALTER TABLE media_slides ADD COLUMN text_font_size INTEGER NOT NULL DEFAULT 72")
        if "foreground_size" not in columns:
            statements.append("ALTER TABLE media_slides ADD COLUMN foreground_size INTEGER NOT NULL DEFAULT 50")
        if "foreground_position" not in columns:
            statements.append("ALTER TABLE media_slides ADD COLUMN foreground_position VARCHAR(24) NOT NULL DEFAULT 'CENTER'")
        if "foreground_animation" not in columns:
            statements.append("ALTER TABLE media_slides ADD COLUMN foreground_animation VARCHAR(40) NOT NULL DEFAULT 'NONE'")
        if "text_animation" not in columns:
            statements.append("ALTER TABLE media_slides ADD COLUMN text_animation VARCHAR(40) NOT NULL DEFAULT 'NONE'")

    if "displays" in tables:
        columns = {column["name"] for column in inspector.get_columns("displays")}
        if "player_token_hash" not in columns:
            statements.append("ALTER TABLE displays ADD COLUMN player_token_hash VARCHAR(64)")
        if "player_token_enabled" not in columns:
            statements.append("ALTER TABLE displays ADD COLUMN player_token_enabled BOOLEAN NOT NULL DEFAULT 0")
        if "player_access_key" not in columns:
            statements.append("ALTER TABLE displays ADD COLUMN player_access_key VARCHAR(64)")
        if "player_token_created_at" not in columns:
            statements.append("ALTER TABLE displays ADD COLUMN player_token_created_at DATETIME")
        if "player_token_last_used_at" not in columns:
            statements.append("ALTER TABLE displays ADD COLUMN player_token_last_used_at DATETIME")

    if "schedules" in tables:
        columns = {column["name"] for column in inspector.get_columns("schedules")}
        if "times_are_utc" not in columns:
            statements.append("ALTER TABLE schedules ADD COLUMN times_are_utc BOOLEAN NOT NULL DEFAULT 0")

    for statement in statements:
        db.session.execute(text(statement))
    if statements:
        db.session.commit()


def create_app(config: dict | None = None, env_file: str | PathLike[str] | None = None):
    resolved_env_file = load_environment(env_file)

    app = Flask(__name__)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        APP_VERSION=__version__,
        MACROSIGNAGE_ENV_FILE=str(resolved_env_file),
        MACROSIGNAGE_TIMEZONE=os.environ.get("MACROSIGNAGE_TIMEZONE", ""),
        SECRET_KEY=os.environ.get("MACROSIGNAGE_SECRET_KEY", "dev-secret-key-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            DATABASE_ENV_KEY,
            default_database_uri(app.instance_path),
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MEDIA_UPLOAD_FOLDER=os.environ.get(
            "MACROSIGNAGE_MEDIA_UPLOAD_FOLDER",
            os.path.join(app.instance_path, "media"),
        ),
        MAX_CONTENT_LENGTH=int(os.environ.get("MACROSIGNAGE_MAX_UPLOAD_BYTES", str(100 * 1024 * 1024))),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("MACROSIGNAGE_SESSION_COOKIE_SECURE", "").lower()
        in {"1", "true", "yes"},
        AUTH_RESET_TOKEN_HOURS=1,
        AUTH_SHOW_RESET_LINKS=False,
    )
    if config:
        app.config.update(config)

    os.makedirs(app.config["MEDIA_UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.get_login"
    login_manager.login_message_category = "warning"
    migrate.init_app(app, db)

    app.register_blueprint(web_bp)
    for feature_bp in features_bp:
        app.register_blueprint(feature_bp)

    @app.before_request
    def require_admin_login():
        endpoint = request.endpoint or ""
        if endpoint.startswith(ADMIN_ENDPOINT_PREFIXES):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.get_login", next=request.full_path.rstrip("?")))
            required_role = required_admin_role(endpoint, request.method)
            if not current_user_can(required_role):
                abort(403)

    @app.context_processor
    def template_permissions():
        return {
            "can_admin": lambda: current_user_can("ADMIN"),
            "can_edit": lambda: current_user_can("EDITOR"),
            "can_view": lambda: current_user_can("VIEWER"),
        }

    @app.after_request
    def mark_content_changes(response):
        endpoint = request.endpoint or ""
        if (
            request.method in {"POST", "PATCH", "PUT", "DELETE"}
            and response.status_code < 400
            and endpoint.startswith(MUTATING_CONTENT_ENDPOINT_PREFIXES)
            and endpoint not in {"auth.get_login", "auth.logout"}
        ):
            from .features.admin.services import touch_content_version

            touch_content_version()
        return response

    with app.app_context():
        db.create_all()
        ensure_runtime_schema()
        from .features.media.services import seed_default_fonts

        seed_default_fonts()

    return app
