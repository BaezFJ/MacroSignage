from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_systemd_deployment_example_matches_current_cli_and_config_names():
    service = (ROOT / "deploy" / "systemd" / "macrosignage.service").read_text(encoding="utf-8")
    deployment = (ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")

    assert "User=macrosignage" in service
    assert "WorkingDirectory=/opt/macrosignage" in service
    assert "EnvironmentFile=/etc/macrosignage/macrosignage.env" in service
    assert "ExecStart=/opt/macrosignage/.venv/bin/macrosignage-prod --host 127.0.0.1 --port 8080 --threads 4" in service
    assert "Restart=on-failure" in service
    assert "journalctl -u macrosignage -f" in deployment
    assert "MACROSIGNAGE_SECRET_KEY" in deployment
    assert "MACROSIGNAGE_DATABASE_URI" in deployment
    assert "MACROSIGNAGE_MEDIA_UPLOAD_FOLDER" in deployment


def test_docker_deployment_example_uses_persistent_volumes_and_current_cli():
    dockerfile = (ROOT / "deploy" / "docker" / "Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "deploy" / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    deployment = (ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")

    assert 'CMD ["macrosignage-prod", "--host", "0.0.0.0", "--port", "8080", "--threads", "4"]' in dockerfile
    assert "MACROSIGNAGE_DATABASE_URI: sqlite:////data/macrosignage.sqlite3" in compose
    assert "MACROSIGNAGE_MEDIA_UPLOAD_FOLDER: /data/media" in compose
    assert "macrosignage-data:/data" in compose
    assert "restart: unless-stopped" in compose
    assert "docker compose -f deploy/docker/docker-compose.yml up -d --build" in deployment


def test_reverse_proxy_and_health_check_docs_use_current_endpoint_and_https_flags():
    deployment = (ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")
    installation = (ROOT / "docs" / "installation.md").read_text(encoding="utf-8")

    assert "curl http://127.0.0.1:8080/api/v1/health" in deployment
    assert "X-Forwarded-Proto" in deployment
    assert "MACROSIGNAGE_SESSION_COOKIE_SECURE=true" in deployment
    assert "MACROSIGNAGE_ENABLE_HSTS=true" in deployment
    assert "macrosignage-prod --host 127.0.0.1 --port 8080 --threads 4" in installation
