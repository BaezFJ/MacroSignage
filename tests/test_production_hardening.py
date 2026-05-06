from __future__ import annotations

import pytest

from macrosignage import cli
from macrosignage.app import DEFAULT_SECRET_KEY, create_app
from macrosignage.extensions import db
from macrosignage.features.auth.models import User
from macrosignage.features.auth.services import hash_password
from macrosignage.features.displays.models import Display


def app_config(tmp_path, **overrides):
    config = {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'macrosignage.sqlite3'}",
        "MEDIA_UPLOAD_FOLDER": str(tmp_path / "media"),
    }
    config.update(overrides)
    return config


def create_admin(app):
    with app.app_context():
        user = User(
            username="admin",
            email="admin@example.com",
            password_hash=hash_password("password123"),
            role="ADMIN",
            active=True,
        )
        db.session.add(user)
        db.session.commit()


@pytest.fixture(autouse=True)
def clear_production_env(monkeypatch):
    for key in (
        "MACROSIGNAGE_SECRET_KEY",
        "MACROSIGNAGE_SESSION_COOKIE_SECURE",
        "MACROSIGNAGE_ENABLE_HSTS",
        "MACROSIGNAGE_ENV",
    ):
        monkeypatch.delenv(key, raising=False)


def test_production_mode_rejects_default_secret_key(tmp_path):
    with pytest.raises(RuntimeError, match="MACROSIGNAGE_SECRET_KEY"):
        create_app(app_config(tmp_path, MACROSIGNAGE_PRODUCTION=True, SECRET_KEY=DEFAULT_SECRET_KEY))


def test_production_mode_allows_safe_secret_and_reports_cookie_warning(tmp_path):
    app = create_app(app_config(tmp_path, MACROSIGNAGE_PRODUCTION=True, SECRET_KEY="prod-secret-value"))

    assert app.config["MACROSIGNAGE_CONFIG_WARNINGS"] == [
        "Set MACROSIGNAGE_SESSION_COOKIE_SECURE=true when MacroSignage is served over HTTPS."
    ]


def test_development_mode_does_not_show_production_warnings(tmp_path):
    app = create_app(app_config(tmp_path, SECRET_KEY="test-secret"))

    assert app.config["MACROSIGNAGE_CONFIG_WARNINGS"] == []


def test_admin_settings_show_production_config_warnings(tmp_path):
    app = create_app(app_config(tmp_path, MACROSIGNAGE_PRODUCTION=True, SECRET_KEY="prod-secret-value"))
    create_admin(app)

    client = app.test_client()
    assert client.post("/auth/login", data={"identifier": "admin", "password": "password123"}).status_code == 302

    response = client.get("/admin/settings/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Production Warnings" in body
    assert "MACROSIGNAGE_SESSION_COOKIE_SECURE=true" in body


def test_prod_help_still_works():
    with pytest.raises(SystemExit) as exit_info:
        cli.prod_main(["--help"])

    assert exit_info.value.code == 0


@pytest.mark.parametrize("path", ["/", "/admin/", "/auth/login", "/api/v1/health"])
def test_security_headers_are_added_to_major_route_groups(tmp_path, path):
    app = create_app(app_config(tmp_path, SECRET_KEY="test-secret"))
    response = app.test_client().get(path)

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert "https://www.youtube-nocookie.com" in response.headers["Content-Security-Policy"]


def test_security_headers_are_added_to_player_route(tmp_path):
    app = create_app(app_config(tmp_path, SECRET_KEY="test-secret"))
    with app.app_context():
        display = Display(
            name="Lobby",
            status="ONLINE",
            player_token_enabled=True,
            player_token_hash="token-hash",
            player_access_key="access-key",
        )
        db.session.add(display)
        db.session.commit()
        display_id = display.id

    client = app.test_client()
    with client.session_transaction() as session:
        session["display_player_access"] = {str(display_id): "access-key"}
    response = client.get(f"/displays/{display_id}/play")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com" in response.headers[
        "Content-Security-Policy"
    ]


def test_hsts_header_can_be_enabled_for_https_deployments(tmp_path):
    app = create_app(app_config(tmp_path, SECRET_KEY="test-secret", MACROSIGNAGE_ENABLE_HSTS=True))
    response = app.test_client().get("/")

    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"


def test_html_500_uses_generic_error_page(tmp_path):
    app = create_app(app_config(tmp_path, SECRET_KEY="test-secret", PROPAGATE_EXCEPTIONS=False))

    @app.get("/broken")
    def broken():
        raise ValueError("sensitive internal detail")

    response = app.test_client().get("/broken")
    body = response.get_data(as_text=True)

    assert response.status_code == 500
    assert "Something went wrong." in body
    assert "sensitive internal detail" not in body


def test_debug_mode_can_still_propagate_exceptions(tmp_path):
    app = create_app(app_config(tmp_path, SECRET_KEY="test-secret", DEBUG=True, PROPAGATE_EXCEPTIONS=True))

    @app.get("/debug-broken")
    def debug_broken():
        raise ValueError("developer detail")

    with pytest.raises(ValueError, match="developer detail"):
        app.test_client().get("/debug-broken")


def test_api_404_405_and_500_use_json_errors(tmp_path):
    app = create_app(app_config(tmp_path, SECRET_KEY="test-secret", PROPAGATE_EXCEPTIONS=False))

    @app.get("/api/v1/broken")
    def broken_api():
        raise ValueError("sensitive internal detail")

    client = app.test_client()

    missing = client.get("/api/v1/missing")
    assert missing.status_code == 404
    assert missing.json["error"]["code"] == "NOT_FOUND"

    method_not_allowed = client.post("/api/v1/health")
    assert method_not_allowed.status_code == 405
    assert method_not_allowed.json["error"]["code"] == "METHOD_NOT_ALLOWED"

    broken = client.get("/api/v1/broken")
    assert broken.status_code == 500
    assert broken.json == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred.",
        }
    }
    assert "sensitive internal detail" not in broken.get_data(as_text=True)
