# MacroSignage

[![PyPI version](https://img.shields.io/pypi/v/MacroSignage)](https://pypi.org/project/MacroSignage/)
[![Python versions](https://img.shields.io/pypi/pyversions/MacroSignage)](https://pypi.org/project/MacroSignage/)
[![License](https://img.shields.io/github/license/BaezFJ/MacroSignage)](LICENSE)
[![CI](https://github.com/BaezFJ/MacroSignage/actions/workflows/ci.yml/badge.svg)](https://github.com/BaezFJ/MacroSignage/actions/workflows/ci.yml)

**A web-based digital signage system built with Flask and Bootstrap.**

MacroSignage lets you manage and display digital signage content through a modern browser-based interface. It uses Bootstrap v5.3.8 for responsive styling and Animate.css for smooth transitions.

> **Note:** This project is in Pre-Alpha (v0.2.1). APIs and features are subject to change.

## Features

- Flask application factory pattern (`create_app`)
- Bootstrap v5.3.8 CSS and JavaScript integration (vendored)
- Bootstrap theme overrides with light and dark mode support via CSS custom properties
- Animate.css for UI transitions (vendored)
- Jinja2 layouts for public, auth, admin, and display player pages
- Admin dashboard with recent activity and settings diagnostics
- Display management CRUD with token-secured player pairing
- Media library CRUD for images, text, video, HTML, YouTube, and slider media
- Slider media with background, foreground image, text, font, position, duration, and animation options
- Global logo overlay settings
- Schedule CRUD with active windows, weekday rules, display targets, media playlists, and no-active-schedule fallback
- User authentication, password reset flow, and role-based access control
- API token management with create, reset, revoke, and delete actions
- REST API for displays, media, schedules, users, fonts, settings, health, and player playlists
- Real-time display updates through server-sent events
- Standalone pywebview display client under `client/`
- SQLite by default with configurable Flask-SQLAlchemy database URI support
- CSRF protection for admin state-changing forms
- Waitress-backed production command and deployment examples for systemd and Docker
- GitHub Actions for CI, PyPI publishing, and client executable builds
- Installable via PyPI (`pip install MacroSignage`)

## v1.0 Focus

- Finish user, operator, API, client, and maintainer documentation.
- Complete manual browser playback checks for all media types.
- Finalize production-readiness review for deployment, backup, restore, and rollback workflows.

## Tech Stack

| Layer     | Technology                 | Version  |
|-----------|----------------------------|----------|
| Backend   | Flask                      | >= 3.1.3 |
| Auth      | Flask-Login                | >= 0.6.3 |
| Forms     | Flask-WTF                  | >= 1.3.0 |
| ORM       | Flask-SQLAlchemy           | >= 3.1.1 |
| WSGI      | Waitress                   | >= 3.0.2 |
| Frontend  | Bootstrap                  | 5.3.8    |
| Animation | Animate.css                | 4.1.1    |
| Theme     | Bootstrap CSS variables    | --       |
| Language  | Python                     | >= 3.10  |
| Packaging | setuptools + uv            | --       |

## Prerequisites

- **Python 3.10 or higher** (3.10, 3.11, 3.12, or 3.13)
- **uv** (recommended) -- a fast Python package manager. [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Alternatively, **pip** >= 21.0 works for basic installation
- **Git** (for development from source)

## Installation

### From PyPI

```bash
pip install MacroSignage
```

### From Source

```bash
# Clone the repository
git clone https://github.com/BaezFJ/MacroSignage.git
cd MacroSignage

# Create virtual environment and install with uv
uv venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
uv sync --all-groups

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install build twine
```

## Quick Start

1. **Run the development server:**

   ```bash
   # Using the MacroSignage CLI
   macrosignage dev
   ```

2. **Open your browser** and navigate to `http://127.0.0.1:5000`

### Production Deployment

For production, use the packaged Waitress-backed command:

```bash
macrosignage prod --host 0.0.0.0 --port 8080
```

Installed packages also include a dedicated production script:

```bash
macrosignage-prod --host 0.0.0.0 --port 8080
```

## Project Structure

```
MacroSignage/
├── client/                         # Standalone pywebview display client
├── deploy/                         # systemd and Docker deployment examples
├── docs/                           # User, operator, API, and maintainer docs
├── src/
│   └── macrosignage/              # Main application package
│       ├── app.py                  # App factory and runtime setup
│       ├── cli.py                  # Development and production CLI commands
│       ├── features/               # Admin, auth, API, display, media, schedule features
│       ├── static/
│       │   ├── css/
│       │   │   └── theme.css      # Bootstrap theme overrides
│       │   ├── js/                # Application JavaScript
│       │   └── vendor/            # Vendored frontend libraries
│       │       ├── bootstrap/     # Bootstrap v5.3.8
│       │       └── animate/       # Animate.css v4.1.1
│       └── templates/
│           ├── layouts/            # Shared layouts
│           └── pages/              # Public pages
├── pyproject.toml                 # Project metadata and dependencies
├── uv.lock                        # Dependency lock file
├── LICENSE                        # MIT License
└── .gitignore
```

## Development

### Running in Development Mode

```bash
macrosignage dev
```

The development command enables Flask debug mode by default.

### Building for Distribution

```bash
python -m build
```

This creates source and wheel distributions in `dist/`.

### Publishing to PyPI

```bash
twine upload dist/*
```

### Adding Dependencies

```bash
# Add a runtime dependency
uv add <package-name>

# Add a dev dependency
uv add --group dev <package-name>
```

## Contributing

Contributions are welcome! MacroSignage is in early development and there are many areas where help is needed.

### How to Contribute

1. **Fork** the repository
2. **Create a feature branch:** `git checkout -b feature/your-feature-name`
3. **Make your changes** and ensure the app runs without errors
4. **Commit** with a descriptive message
5. **Push** to your fork and open a **Pull Request**

### Guidelines

- Follow PEP 8 for Python code style
- Use the Flask application factory pattern when adding new functionality
- Keep vendored frontend libraries in `src/macrosignage/static/vendor/`
- Place new templates under appropriate subdirectories in `templates/`
- Use CSS custom properties from `theme.css` for consistent theming
- Write descriptive commit messages

## Documentation

Expanded documentation is available in [docs/index.md](docs/index.md).

### Areas Looking for Contributions

- User authentication system
- Database models and migrations
- Admin dashboard UI
- Test coverage expansion
- CI/CD pipeline (GitHub Actions)
- Documentation improvements

## Roadmap

### v0.2.0 -- Foundation

- [x] Application configuration system (python-dotenv integration)
- [x] Database setup with Flask-SQLAlchemy
- [x] User model and authentication with Flask-Login
- [x] Form infrastructure with Flask-WTF
- [x] Basic test suite with pytest

### v0.3.0 -- Core Features

- [x] Admin dashboard layout
- [x] Content/media management (upload, organize, delete)
- [x] Display/screen registration and management
- [x] Content-to-display assignment

### v0.4.0 -- Scheduling and Playback

- [x] Content scheduling (time-based rotation)
- [x] Signage display player view (fullscreen, auto-rotation)
- [x] Playlist management

### v0.5.0 -- Polish and Scale

- [x] REST API
- [x] Real-time updates with server-sent events
- [x] Multi-user role support (admin, editor, viewer)
- [x] CI/CD pipeline with GitHub Actions
- [x] Production and documentation roadmaps

### v1.0.0 -- Stable Release

- [ ] Production-hardened and fully tested ([roadmap](docs/production-hardening-roadmap.md))
- [ ] Complete documentation ([roadmap](docs/documentation-roadmap.md))
- [ ] Deployment guides (Docker, systemd, cloud)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Copyright (c) 2022 Javier Baez

## Author

**Javier Baez**

- Email: baezdevs@gmail.com
- GitHub: [@BaezFJ](https://github.com/BaezFJ)

---

**Project Links:**
[GitHub Repository](https://github.com/BaezFJ/MacroSignage) |
[PyPI Package](https://pypi.org/project/MacroSignage/) |
[Issue Tracker](https://github.com/BaezFJ/MacroSignage/issues)
