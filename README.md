# MacroSignage

[![PyPI version](https://img.shields.io/pypi/v/MacroSignage)](https://pypi.org/project/MacroSignage/)
[![Python versions](https://img.shields.io/pypi/pyversions/MacroSignage)](https://pypi.org/project/MacroSignage/)
[![License](https://img.shields.io/github/license/BaezFJ/MacroSignage)](https://github.com/BaezFJ/MacroSignage/blob/master/LICENSE)
[![CI](https://github.com/BaezFJ/MacroSignage/actions/workflows/ci.yml/badge.svg)](https://github.com/BaezFJ/MacroSignage/actions/workflows/ci.yml)

MacroSignage is a Flask-based digital signage manager with an admin console, token-secured display players, scheduling, media playback, REST API access, and a standalone pywebview display client.

> **Status:** Pre-alpha v0.2.3. Data models and API contracts can change before v1.0.

## Features

- Admin dashboard with recent activity, diagnostics, and settings pages.
- Display CRUD with online, offline, and maintenance states.
- Token-secured display player pairing with remote disable/rotation.
- Media CRUD for images, text, video, HTML, YouTube, and slider media.
- Slider media with backgrounds, foreground images, fonts, positions, durations, and Animate.css effects.
- Schedule CRUD with active windows, weekday rules, display targets, playlists, and no-active-schedule fallback.
- Auth, password reset flow, user CRUD, RBAC, and API token lifecycle management.
- REST API for displays, media, schedules, users, fonts, settings, health, and player playlists.
- Server-sent events for display player refresh.
- Global logo overlay settings and managed Google Fonts.
- SQLite by default with configurable Flask-SQLAlchemy database URI support.
- Waitress-backed production CLI plus systemd and Docker examples.
- Separate pywebview client package with GitHub Release executables.

## Quick Start

Install from PyPI:

```bash
pip install MacroSignage
macrosignage dev
```

Or run from source:

```bash
git clone https://github.com/BaezFJ/MacroSignage.git
cd MacroSignage
uv sync --all-groups
cp .env.example .env
uv run macrosignage dev
```

Open `http://127.0.0.1:5000`, then create the first admin account at `/auth/setup`.

## Production

Use the dedicated production script behind a reverse proxy:

```bash
MACROSIGNAGE_SECRET_KEY='replace-with-a-long-random-secret' \
MACROSIGNAGE_DATABASE_URI='sqlite:////var/lib/macrosignage/macrosignage.sqlite3' \
MACROSIGNAGE_MEDIA_UPLOAD_FOLDER='/var/lib/macrosignage/media' \
MACROSIGNAGE_SESSION_COOKIE_SECURE=true \
macrosignage-prod --host 127.0.0.1 --port 8080 --threads 4
```

See [Deployment](https://github.com/BaezFJ/MacroSignage/blob/master/docs/deployment.md) for systemd, Docker, HTTPS, health checks, backups, restore, and rollback.

## Client Executables

Prebuilt standalone display client executables are available on the GitHub Releases page:

```text
https://github.com/BaezFJ/MacroSignage/releases
```

The client source package lives in `client/`. See [Standalone Client](https://github.com/BaezFJ/MacroSignage/blob/master/docs/client.md).

## Documentation

Start with [docs/index.md](https://github.com/BaezFJ/MacroSignage/blob/master/docs/index.md).

Core guides:

- [Installation](https://github.com/BaezFJ/MacroSignage/blob/master/docs/installation.md)
- [Configuration](https://github.com/BaezFJ/MacroSignage/blob/master/docs/configuration.md)
- [Auth and RBAC](https://github.com/BaezFJ/MacroSignage/blob/master/docs/auth-rbac.md)
- [Display Management and Player Pairing](https://github.com/BaezFJ/MacroSignage/blob/master/docs/displays.md)
- [Media Library](https://github.com/BaezFJ/MacroSignage/blob/master/docs/media.md)
- [Scheduling and Playback](https://github.com/BaezFJ/MacroSignage/blob/master/docs/scheduling.md)
- [REST API](https://github.com/BaezFJ/MacroSignage/blob/master/docs/rest-api.md)
- [API Tokens](https://github.com/BaezFJ/MacroSignage/blob/master/docs/api-tokens.md)
- [Deployment](https://github.com/BaezFJ/MacroSignage/blob/master/docs/deployment.md)
- [Troubleshooting](https://github.com/BaezFJ/MacroSignage/blob/master/docs/troubleshooting.md)
- [Development](https://github.com/BaezFJ/MacroSignage/blob/master/docs/development.md)
- [Architecture](https://github.com/BaezFJ/MacroSignage/blob/master/docs/architecture.md)

## Development Commands

```bash
uv lock --check
uv run python -m pytest
uv run python -m unittest discover -s tests
uv run python -m compileall src/macrosignage tests
uv build
uv run twine check dist/*
```

## Release Automation

- CI runs on pull requests and pushes to `main`.
- PyPI publishing runs when a `v*` tag is pushed.
- Client executable build and release workflows produce Windows, macOS, and Linux assets.
- Release documentation review is tracked in [the checklist](https://github.com/BaezFJ/MacroSignage/blob/master/docs/release-documentation-checklist.md).

## v1.0 Remaining Work

- [ ] Production-hardened and fully tested ([roadmap](https://github.com/BaezFJ/MacroSignage/blob/master/docs/production-hardening-roadmap.md))
- [x] Complete documentation ([roadmap](https://github.com/BaezFJ/MacroSignage/blob/master/docs/documentation-roadmap.md))
- [x] Deployment guides for Docker, systemd, health checks, backups, and rollback

## License

MacroSignage is licensed under the MIT License. See [LICENSE](https://github.com/BaezFJ/MacroSignage/blob/master/LICENSE).

Copyright (c) 2022 Javier Baez

## Links

[GitHub Repository](https://github.com/BaezFJ/MacroSignage) |
[PyPI Package](https://pypi.org/project/MacroSignage/) |
[Issue Tracker](https://github.com/BaezFJ/MacroSignage/issues)
