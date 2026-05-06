__version__ = "0.2.0"

import os
from os import PathLike

from dotenv import load_dotenv
from flask import Flask, redirect, request, url_for
from flask_login import current_user
from sqlalchemy import inspect, text

from .extensions import csrf, db, login_manager, migrate
from .web.routes import web_bp
from .features import features_bp


ADMIN_ENDPOINT_PREFIXES = ("admin.", "admin_displays.", "admin_media.", "admin_schedules.", "admin_users.")


def load_environment(env_file: str | PathLike[str] | None = None) -> None:
    load_dotenv(env_file, override=False)


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

    for statement in statements:
        db.session.execute(text(statement))
    if statements:
        db.session.commit()


def create_app(config: dict | None = None, env_file: str | PathLike[str] | None = None):
    load_environment(env_file)

    app = Flask(__name__)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        APP_VERSION=__version__,
        SECRET_KEY=os.environ.get("MACROSIGNAGE_SECRET_KEY", "dev-secret-key-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "MACROSIGNAGE_DATABASE_URI",
            f"sqlite:///{os.path.join(app.instance_path, 'macrosignage.sqlite3')}",
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
        if endpoint.startswith(ADMIN_ENDPOINT_PREFIXES) and not current_user.is_authenticated:
            return redirect(url_for("auth.get_login", next=request.full_path.rstrip("?")))

    with app.app_context():
        db.create_all()
        ensure_runtime_schema()
        from .features.media.services import seed_default_fonts

        seed_default_fonts()

    return app
