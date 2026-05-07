# Architecture

MacroSignage is a Flask application with feature-oriented blueprints, SQLAlchemy models, server-rendered admin/player views, a JSON API, and a separate pywebview client package.

## Application Factory

`src/macrosignage/app.py` exposes `create_app()`. The factory:

- loads `.env` through `src/macrosignage/config.py`
- configures Flask, SQLAlchemy, Flask-Login, Flask-WTF/CSRF, and Flask-Migrate
- registers public, admin, feature, API, and display-player blueprints
- applies admin login/RBAC checks before admin requests
- adds security headers and optional HSTS
- normalizes API-style error responses for `/api/*`
- creates database tables and applies additive runtime schema checks
- seeds default Google Fonts

CLI entry points in `src/macrosignage/cli.py` call the same factory for development and production, and expose the package upgrade command. `macrosignage-prod` runs Waitress.

## Feature Blueprints

Feature blueprints are assembled in `src/macrosignage/features/__init__.py`.

Current feature packages:

- `admin`: dashboard, settings, database/logo/font management, diagnostics
- `auth`: setup, login, logout, password reset, users, API tokens, role checks
- `api`: `/api/v1` JSON routes and serializers
- `displays`: admin display CRUD, player token lifecycle, browser player, SSE
- `media`: media CRUD, upload handling, slider media, Google Font helpers
- `schedules`: schedule CRUD and time/window form helpers

The admin, display, media, and schedule features follow the `routes.py`, `models.py`, `services.py`, and `forms.py` pattern documented in [Development](development.md).

## Data Model

SQLAlchemy models live inside feature packages:

- `auth.models.User` and `auth.models.ApiToken`
- `displays.models.Display`
- `media.models.MediaAsset`, `MediaSlide`, and `MediaFont`
- `schedules.models.Schedule`
- `admin.models.SignageSettings` and `ContentVersion`

Many-to-many relationships live in `src/macrosignage/features/associations.py`:

- displays to media
- displays to schedules
- schedules to media

The player playlist is selected from playable schedules assigned to a display. Schedule selection uses the configured timezone helpers in `src/macrosignage/time_utils.py`.

## Runtime Schema Strategy

MacroSignage currently creates tables at startup and applies additive runtime schema checks in `ensure_runtime_schema()` inside `src/macrosignage/app.py`. This keeps early installations moving while the project is still pre-alpha and schema changes are additive.

Flask-Migrate is initialized, but the current v0.x deployment path relies on startup schema compatibility checks. Operators should still back up the database before upgrading. See [Deployment](deployment.md) and [ADR-001](decisions/001-runtime-schema-strategy.md).

## Authentication and Authorization

Browser sessions use Flask-Login. Admin route access is guarded by `required_admin_role()` in `src/macrosignage/features/auth/permissions.py`.

API integrations use bearer API tokens. API tokens are shown once, stored hashed, and inherit the owner's current role.

Display players use display-specific tokens and paired access keys, not API bearer tokens. See [ADR-002](decisions/002-token-secured-display-players.md), [Auth and RBAC](auth-rbac.md), [API Tokens](api-tokens.md), and [Display Management and Player Pairing](displays.md).

## Display Playback and SSE

Browser players live under `/displays`. A player pairs by posting a display token, then keeps a paired access key in its browser session.

The player page evaluates display status first:

- `OFFLINE`: show offline page
- `MAINTENANCE`: show maintenance page
- `ONLINE`: build a playlist from active schedules

If no playable schedules are available, the online player shows "No active schedules for display".

The player listens to server-sent events at `/displays/<display_id>/events`. Admin/API content mutations increment the content version, which prompts paired players to reload. The player also reloads around future active schedule start/end boundaries.

See [Realtime and Player Behavior](realtime-player.md).

## REST API

The JSON API is mounted at `/api/v1` in `src/macrosignage/features/api/routes.py`. Serializer functions in `src/macrosignage/features/api/serializers.py` define response shapes for users, displays, media, schedules, fonts, settings, and player payloads.

The API uses consistent `{"data": ...}` success responses and `{"error": ...}` error responses. See [REST API](rest-api.md).

## Static Vendoring

MacroSignage vendors frontend dependencies under `src/macrosignage/static/vendor/`:

- Bootstrap v5.3.8
- Animate.css v4.1.1

Vendoring keeps the installed package self-contained and avoids CDN requirements for admin/player screens. The package data list in `pyproject.toml` includes templates, static assets, and license files.

## Standalone Client

The standalone display client lives in `client/` with its own package metadata, lockfile, CLI, and GitHub Actions build workflows. It uses pywebview to open the paired browser player in a desktop webview.

The client is intentionally not part of the main `src/macrosignage` package so it can be built into OS-specific executables without adding GUI dependencies to the server package. See [ADR-003](decisions/003-standalone-client-packaging.md) and [Standalone Client](client.md).
