from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_FILES = [ROOT / "README.md", ROOT / "client" / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\((?!https?://|mailto:)([^)]+)\)")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def github_anchor(text: str) -> str:
    slug = text.strip().lower()
    slug = re.sub(r"`([^`]+)`", r"\1", slug)
    slug = re.sub(r"<[^>]+>", "", slug)
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug.strip("-")


def anchors_for(path: Path) -> set[str]:
    anchors = set()
    seen: dict[str, int] = {}
    for match in HEADING_PATTERN.finditer(path.read_text(encoding="utf-8")):
        base = github_anchor(match.group(2))
        if not base:
            continue
        count = seen.get(base, 0)
        seen[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def split_link(raw_link: str) -> tuple[str, str]:
    target = raw_link.strip()
    if " " in target and not target.startswith("<"):
        target = target.split(" ", 1)[0]
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if "#" in target:
        path, fragment = target.split("#", 1)
        return path, fragment
    return target, ""


def test_markdown_local_links_resolve_to_files_and_anchors():
    failures = []
    anchor_cache: dict[Path, set[str]] = {}

    for source in MARKDOWN_FILES:
        text = source.read_text(encoding="utf-8")
        for raw_link in LINK_PATTERN.findall(text):
            target_path, fragment = split_link(raw_link)
            if not target_path and not fragment:
                continue
            resolved = (source.parent / target_path).resolve() if target_path else source.resolve()
            if not resolved.exists():
                failures.append(f"{source.relative_to(ROOT)} -> {raw_link} missing file")
                continue
            if fragment and resolved.suffix == ".md":
                anchors = anchor_cache.setdefault(resolved, anchors_for(resolved))
                if fragment not in anchors:
                    failures.append(f"{source.relative_to(ROOT)} -> {raw_link} missing anchor")

    assert failures == []


def test_docs_index_and_readme_reference_core_documentation():
    docs_index = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for guide in (
        "installation.md",
        "configuration.md",
        "auth-rbac.md",
        "displays.md",
        "media.md",
        "scheduling.md",
        "client.md",
        "api-tokens.md",
        "rest-api.md",
        "deployment.md",
        "troubleshooting.md",
        "development.md",
        "architecture.md",
        "documentation-roadmap.md",
        "production-hardening-roadmap.md",
    ):
        assert guide in docs_index or f"docs/{guide}" in readme

    assert "docs/documentation-roadmap.md" in readme
    assert "docs/production-hardening-roadmap.md" in readme


def test_release_documentation_checklist_is_linked():
    checklist = ROOT / "docs" / "release-documentation-checklist.md"
    development = (ROOT / "docs" / "development.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert checklist.exists()
    assert "release-documentation-checklist.md" in development
    assert "docs/release-documentation-checklist.md" in readme
