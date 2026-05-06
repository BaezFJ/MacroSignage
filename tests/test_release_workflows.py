from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def workflow_text(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def test_pypi_publish_workflow_runs_on_version_tags_and_uses_trusted_publishing():
    workflow = workflow_text("publish-pypi.yml")

    assert "tags:" in workflow
    assert '- "v*"' in workflow
    assert "id-token: write" in workflow
    assert "uv lock --check" in workflow
    assert "uv run python -m pytest" in workflow
    assert "uv build" in workflow
    assert "uv run twine check dist/*" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow


def test_client_build_workflow_runs_on_version_tags_and_manual_dispatch():
    workflow = workflow_text("client-build.yml")

    assert "workflow_dispatch:" in workflow
    assert "tags:" in workflow
    assert '- "v*"' in workflow
    assert "working-directory: client" in workflow
    assert "uv sync --extra build --frozen" in workflow
    assert "uv run macrosignage-client --help" in workflow
    assert "uv run pyinstaller --onefile --windowed --name MacroSignageClient macrosignage_client/app.py" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "path: client/dist/*" in workflow


def test_client_release_workflow_can_upload_assets_for_tag_or_manual_rerun():
    workflow = workflow_text("client-release.yml")

    assert "workflow_dispatch:" in workflow
    assert "tag:" in workflow
    assert "tags:" in workflow
    assert '- "v*"' in workflow
    assert "contents: write" in workflow
    assert "working-directory: client" in workflow
    assert "executable-path: dist/MacroSignageClient.exe" in workflow
    assert "executable-path: dist/MacroSignageClient" in workflow
    assert "client/dist/MacroSignageClient" not in workflow
    assert 'mv "${{ matrix.executable-path }}" "dist/${{ matrix.asset-name }}"' in workflow
    assert "tag_name: ${{ github.event_name == 'workflow_dispatch' && inputs.tag || github.ref_name }}" in workflow
    assert "files: client/dist/${{ matrix.asset-name }}" in workflow
    assert "fail_on_unmatched_files: true" in workflow
