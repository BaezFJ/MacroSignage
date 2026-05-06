from pathlib import Path
import sys
import tomllib
from unittest.mock import Mock, patch

import pytest

from macrosignage import cli

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
