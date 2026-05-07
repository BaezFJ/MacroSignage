__version__ = "0.2.4"

import os
from os import PathLike

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import inspect, text
from werkzeug.exceptions import HTTPException

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
DEFAULT_SECRET_KEY = "dev-secret-key-change-me"
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Frame-Options": "SAMEORIGIN",
    "Content-Security-Policy": "; ".join(
        [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: blob: https:",
            "media-src 'self' data: blob: https:",
            "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com",
            "connect-src 'self'",
            "frame-ancestors 'self'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
    ),
}


def production_config_warnings(app: Flask) -> list[str]:
    warnings = []
    if not app.config.get("SESSION_COOKIE_SECURE"):
        warnings.append(
            "Set MACROSIGNAGE_SESSION_COOKIE_SECURE=true when MacroSignage is served over HTTPS."
        )
    return warnings


def validate_production_config(app: Flask) -> None:
    if not app.config.get("MACROSIGNAGE_PRODUCTION"):
        app.config["MACROSIGNAGE_CONFIG_WARNINGS"] = []
        return

    secret_key = str(app.config.get("SECRET_KEY") or "")
    if not secret_key or secret_key == DEFAULT_SECRET_KEY:
        raise RuntimeError(
            "Production mode requires MACROSIGNAGE_SECRET_KEY to be set to a non-default value."
        )
    app.config["MACROSIGNAGE_CONFIG_WARNINGS"] = production_config_warnings(app)


def wants_api_error_response() -> bool:
    if request.path.startswith("/api/"):
        return True
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "application/json" and request.accept_mimetypes[best] > request.accept_mimetypes["text/html"]


def json_error_response(status_code: int, code: str, message: str):
    return jsonify({"error": {"code": code, "message": message}}), status_code


def ensure_runtime_schema() -> None:
    inspector = inspect(db.engine)
    statements = []
    tables = set(inspector.get_table_names())

    if "media_slides" in tables:
        columns = {column["name"] for column in inspector.get_columns("media_slides")}
        if "foreground_file_path" not in columns:
            statements.append("ALTER TABLE media_slides ADD COLUMN foreground_file_path VARCHAR(260)")
        if "foreground_original_filename" not in columns:
            statements.append("ALTER TABLE media_slides ADD COLUMN foreground_original_filename VARCHAR(260)")
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

    if "media_assets" in tables:
        columns = {column["name"] for column in inspector.get_columns("media_assets")}
        if "neon_text_color" not in columns:
            statements.append("ALTER TABLE media_assets ADD COLUMN neon_text_color VARCHAR(7)")
        if "neon_frame_color" not in columns:
            statements.append("ALTER TABLE media_assets ADD COLUMN neon_frame_color VARCHAR(7)")
        if "neon_background_color" not in columns:
            statements.append("ALTER TABLE media_assets ADD COLUMN neon_background_color VARCHAR(7)")

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

    if "signage_settings" in tables:
        columns = {column["name"] for column in inspector.get_columns("signage_settings")}
        if "logo_enabled" not in columns:
            statements.append("ALTER TABLE signage_settings ADD COLUMN logo_enabled BOOLEAN NOT NULL DEFAULT 0")
        if "logo_position" not in columns:
            statements.append("ALTER TABLE signage_settings ADD COLUMN logo_position VARCHAR(24) NOT NULL DEFAULT 'TOP_RIGHT'")
        if "logo_file_path" not in columns:
            statements.append("ALTER TABLE signage_settings ADD COLUMN logo_file_path VARCHAR(260)")
        if "logo_original_filename" not in columns:
            statements.append("ALTER TABLE signage_settings ADD COLUMN logo_original_filename VARCHAR(260)")
        if "logo_mime_type" not in columns:
            statements.append("ALTER TABLE signage_settings ADD COLUMN logo_mime_type VARCHAR(120)")

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
        MACROSIGNAGE_PRODUCTION=os.environ.get("MACROSIGNAGE_ENV", "").lower() in {"prod", "production"},
        MACROSIGNAGE_TIMEZONE=os.environ.get("MACROSIGNAGE_TIMEZONE", ""),
        SECRET_KEY=os.environ.get("MACROSIGNAGE_SECRET_KEY", DEFAULT_SECRET_KEY),
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
        MACROSIGNAGE_ENABLE_HSTS=os.environ.get("MACROSIGNAGE_ENABLE_HSTS", "").lower() in {"1", "true", "yes"},
    )
    if config:
        app.config.update(config)

    validate_production_config(app)

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
    def add_security_headers(response):
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        if app.config.get("MACROSIGNAGE_ENABLE_HSTS") or app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

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

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        status_code = error.code or 500
        if wants_api_error_response():
            code = error.name.upper().replace(" ", "_")
            return json_error_response(status_code, code, error.description or error.name)
        return error

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        if isinstance(error, HTTPException):
            return handle_http_error(error)
        if app.config.get("PROPAGATE_EXCEPTIONS"):
            raise error
        app.logger.exception("Unhandled application error", exc_info=error)
        if wants_api_error_response():
            return json_error_response(500, "INTERNAL_SERVER_ERROR", "An internal server error occurred.")
        return render_template("errors/500.html", title="Server Error"), 500

    with app.app_context():
        db.create_all()
        ensure_runtime_schema()
        from .features.media.services import seed_default_fonts

        seed_default_fonts()

    return app
