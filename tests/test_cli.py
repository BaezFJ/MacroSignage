from pathlib import Path
import subprocess
import sys
import tomllib
from unittest.mock import Mock, call, patch

import pytest

from macrosignage import cli
from macrosignage import upgrade

CLIENT_PATH = Path(__file__).resolve().parents[1] / "client"
sys.path.insert(0, str(CLIENT_PATH))

from macrosignage_client import app as client_app


ROOT = Path(__file__).resolve().parents[1]


def test_dev_subcommand_runs_flask_development_server():
    app = Mock()

    with patch.object(cli, "create_app", return_value=app):
        exit_code = cli.main(["dev", "--host", "127.0.0.1", "--port", "5050", "--no-debug"])

    assert exit_code == 0
    app.run.assert_called_once_with(host="127.0.0.1", port=5050, debug=False)


def test_prod_main_serves_with_waitress_options():
    app = object()
    serve = Mock()

    with (
        patch.object(cli, "create_app", return_value=app),
        patch("waitress.serve", serve),
    ):
        exit_code = cli.prod_main(["--host", "127.0.0.1", "--port", "9090", "--threads", "8"])

    assert exit_code == 0
    serve.assert_called_once_with(app, host="127.0.0.1", port=9090, threads=8)


def test_client_entry_point_help_exits_before_pywebview_import():
    with patch.dict(sys.modules, {"webview": None}):
        with pytest.raises(SystemExit) as exit_info:
            client_app.main(["--help"])
        assert exit_info.value.code == 0


def test_project_entry_points_and_package_data_are_declared():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    client_project = tomllib.loads((ROOT / "client" / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"] == {
        "macrosignage": "macrosignage.cli:main",
        "macrosignage-prod": "macrosignage.cli:prod_main",
        "macrosignage-upgrade": "macrosignage.cli:upgrade_main",
    }
    assert client_project["project"]["scripts"]["macrosignage-client"] == "macrosignage_client.app:main"

    package_data = set(project["tool"]["setuptools"]["package-data"]["macrosignage"])
    assert {"**/*.html", "**/*.css", "**/*.js", "**/*.png", "**/*.svg", "**/LICENSE*"}.issubset(package_data)


def test_release_workflows_are_documented_and_present():
    development_docs = (ROOT / "docs" / "development.md").read_text(encoding="utf-8")
    for workflow_name in ("ci.yml", "publish-pypi.yml", "client-build.yml", "client-release.yml"):
        assert workflow_name in development_docs
        assert (ROOT / ".github" / "workflows" / workflow_name).exists()


def test_prod_subcommand_uses_same_waitress_options():
    app = object()
    serve = Mock()

    with (
        patch.object(cli, "create_app", return_value=app),
        patch("waitress.serve", serve),
    ):
        exit_code = cli.main(["prod", "--host", "127.0.0.1", "--port", "9090", "--threads", "8"])

    assert exit_code == 0
    serve.assert_called_once_with(app, host="127.0.0.1", port=9090, threads=8)


def test_upgrade_dry_run_prints_planned_versioned_install(capsys):
    with (
        patch("macrosignage.upgrade.shutil.which", return_value="/usr/local/bin/uv"),
        patch("macrosignage.upgrade.subprocess.run") as run,
    ):
        exit_code = cli.upgrade_main(["--dry-run", "--version", "0.2.5", "--no-backup"])

    output = capsys.readouterr().out

    assert exit_code == 0
    run.assert_not_called()
    assert "Would inspect environment file:" in output
    assert "Would skip backups." in output
    assert "/usr/local/bin/uv pip install" in output
    assert "MacroSignage==0.2.5" in output


def test_upgrade_subcommand_runs_uv_install_with_confirmation_skipped():
    completed = subprocess.CompletedProcess(args=[], returncode=0)

    with (
        patch("macrosignage.upgrade.shutil.which", return_value="/usr/local/bin/uv"),
        patch("macrosignage.upgrade.subprocess.run", return_value=completed) as run,
    ):
        exit_code = cli.main(["upgrade", "--yes", "--no-backup"])

    assert exit_code == 0
    run.assert_called_once_with(
        [
            "/usr/local/bin/uv",
            "pip",
            "install",
            "--python",
            sys.executable,
            "--upgrade",
            "MacroSignage",
        ],
        check=False,
    )


def test_upgrade_uses_pip_when_uv_is_not_available():
    completed = subprocess.CompletedProcess(args=[], returncode=0)

    with (
        patch("macrosignage.upgrade.shutil.which", return_value=None),
        patch("macrosignage.upgrade.subprocess.run", return_value=completed) as run,
    ):
        exit_code = cli.upgrade_main(["--yes", "--no-backup"])

    assert exit_code == 0
    run.assert_called_once_with(
        [sys.executable, "-m", "pip", "install", "--upgrade", "MacroSignage"],
        check=False,
    )


def test_upgrade_uses_explicit_uv_binary():
    completed = subprocess.CompletedProcess(args=[], returncode=0)

    with (
        patch("macrosignage.upgrade.shutil.which", return_value=None),
        patch("macrosignage.upgrade.subprocess.run", return_value=completed) as run,
    ):
        exit_code = cli.upgrade_main(["--yes", "--no-backup", "--uv-bin", "/usr/local/bin/uv"])

    assert exit_code == 0
    run.assert_called_once_with(
        [
            "/usr/local/bin/uv",
            "pip",
            "install",
            "--python",
            sys.executable,
            "--upgrade",
            "MacroSignage",
        ],
        check=False,
    )


def test_upgrade_restarts_service_when_backup_fails():
    completed = subprocess.CompletedProcess(args=[], returncode=0)

    with (
        patch("macrosignage.upgrade.shutil.which", return_value="/usr/local/bin/uv"),
        patch("macrosignage.upgrade.subprocess.run", return_value=completed) as run,
        patch("macrosignage.upgrade.create_backup", side_effect=RuntimeError("backup failed")),
    ):
        with pytest.raises(RuntimeError, match="backup failed"):
            cli.upgrade_main(["--yes", "--service", "macrosignage"])

    assert run.call_args_list == [
        call(["systemctl", "stop", "macrosignage"], check=False),
        call(["systemctl", "start", "macrosignage"], check=False),
    ]


def test_upgrade_backup_copies_env_sqlite_and_media(tmp_path):
    database_path = tmp_path / "macrosignage.sqlite3"
    media_path = tmp_path / "media"
    env_path = tmp_path / ".env"
    database_path.write_bytes(b"database")
    media_path.mkdir()
    (media_path / "logo.png").write_bytes(b"image")
    env_path.write_text(
        "\n".join(
            [
                f"MACROSIGNAGE_DATABASE_URI=sqlite:///{database_path}",
                f"MACROSIGNAGE_MEDIA_UPLOAD_FOLDER={media_path}",
            ]
        ),
        encoding="utf-8",
    )
    _, environment = upgrade.load_upgrade_environment(env_path)

    backup = upgrade.create_backup(
        env_path=env_path,
        environment=environment,
        backup_root=tmp_path / "backups",
        timestamp="20260506-203000",
    )

    backup_files = {path.name for path in backup.created}

    assert backup.backup_dir == tmp_path / "backups" / "macrosignage-20260506-203000"
    assert backup_files == {".env", "macrosignage.sqlite3", "media.tar.gz"}
    assert backup.warnings == ()
