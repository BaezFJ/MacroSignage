# Development

This guide is for contributors maintaining MacroSignage from source. User and operator setup starts in [Installation](installation.md) and [Deployment](deployment.md).

## Local Setup

```bash
git clone https://github.com/BaezFJ/MacroSignage.git
cd MacroSignage
uv sync --all-groups
cp .env.example .env
uv run macrosignage dev
```

The development server reads `.env`, creates the SQLite database automatically, and serves the app at `http://127.0.0.1:5000` unless you pass different CLI options.

Useful commands:

```bash
uv run macrosignage dev --host 127.0.0.1 --port 5000
uv run macrosignage dev --no-debug
uv run macrosignage-prod --host 127.0.0.1 --port 8080 --threads 4
```

## Run Checks

These commands match `.github/workflows/ci.yml`:

```bash
uv lock --check
uv run python -m pytest
uv run python -m unittest discover -s tests
uv run python -m compileall src/macrosignage tests
uv build
uv run twine check dist/*
```

Run focused tests while iterating:

```bash
uv run python -m pytest tests/test_api.py
uv run python -m pytest tests/test_display_player.py
uv run python -m pytest tests/test_operational_readiness.py
```

## Packaging

Build the main Python package:

```bash
uv build
uv run twine check dist/*
```

The main package exposes:

```text
macrosignage = macrosignage.cli:main
macrosignage-prod = macrosignage.cli:prod_main
```

The standalone display client is separate:

```bash
cd client
uv sync --extra build
uv run macrosignage-client --help
uv run pyinstaller --onefile --windowed --name MacroSignageClient macrosignage_client/app.py
```

See [Standalone Client](client.md) for operator-facing client setup.

## Project Structure

```text
src/macrosignage/
├── app.py                 # Flask application factory, security headers, error handling, runtime schema checks
├── cli.py                 # macrosignage and macrosignage-prod entry points
├── config.py              # .env loading, database URI helpers, database form options
├── diagnostics.py         # health check and admin diagnostics payloads
├── extensions.py          # Flask extension instances
├── time_utils.py          # configured timezone and datetime conversion helpers
├── features/
│   ├── admin/             # dashboard, settings, database/logo/font admin pages
│   ├── api/               # /api/v1 routes and serializers
│   ├── auth/              # login, password reset, users, API tokens, RBAC
│   ├── displays/          # display CRUD, player pairing, browser player, SSE
│   ├── media/             # media CRUD, uploads, sliders, Google Fonts
│   └── schedules/         # schedule CRUD and schedule form helpers
├── static/                # CSS, JavaScript, images, vendored frontend libraries
├── templates/             # shared error and layout templates
└── web/                   # public marketing/index routes
```

Other top-level paths:

```text
client/                    # Separate pywebview client package and lockfile
deploy/                    # systemd and Docker deployment examples
docs/                      # User, operator, API, architecture, and maintainer docs
tests/                     # pytest/unittest test suite
.github/workflows/         # CI, PyPI publish, and client executable workflows
```

## Feature Blueprint Pattern

Feature packages follow a small, explicit pattern:

```text
features/<feature>/
├── __init__.py
├── routes.py
├── models.py
├── services.py
├── forms.py
└── templates/
```

Use the existing structure when adding or changing a feature:

- `routes.py`: Flask routes, request/response control flow, redirects, and templates.
- `models.py`: SQLAlchemy models and model-level convenience properties.
- `services.py`: database queries, token generation, file storage, and business rules.
- `forms.py`: form parsing, validation constants, and UI option lists.
- `templates/`: Jinja templates grouped under the feature's admin/player/auth path.

Register new blueprints from `src/macrosignage/features/__init__.py`. Keep admin routes behind the existing admin endpoint prefixes so login and role checks apply.

## Static Assets

Application CSS and JavaScript live in `src/macrosignage/static/`.

Vendored frontend libraries are checked in under `src/macrosignage/static/vendor/` so installed packages do not depend on a CDN:

- Bootstrap v5.3.8 in `vendor/bootstrap/`
- Animate.css v4.1.1 in `vendor/animate/`

When replacing a vendored library, keep its license file and update package data patterns in `pyproject.toml` only if new file types are required.

## Tests

The automated suite covers Flask route contracts, admin CRUD workflows, API authorization, player-token access, schedule selection logic, package metadata, production hardening, deployment docs, client configuration helpers, and CLI entry point parsing.

Browser media playback for real image, video, YouTube, HTML iframe, and slider timing should still be checked manually before a production release because it depends on browser codecs, network access, and display hardware behavior.

## Release Automation

- `.github/workflows/ci.yml`: runs on pull requests and pushes to `main`.
- `.github/workflows/publish-pypi.yml`: publishes MacroSignage to PyPI when a `v*` tag is pushed.
- `.github/workflows/client-build.yml`: builds standalone client executables on demand and for `v*` tags.
- `.github/workflows/client-release.yml`: uploads standalone client executables to the matching GitHub Release.

Before tagging, run the checks above, complete the [Release Documentation Checklist](release-documentation-checklist.md), and review [Architecture](architecture.md), [Deployment](deployment.md), and the active roadmaps.
