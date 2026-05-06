# MacroSignage

[![PyPI version](https://img.shields.io/pypi/v/MacroSignage)](https://pypi.org/project/MacroSignage/)
[![Python versions](https://img.shields.io/pypi/pyversions/MacroSignage)](https://pypi.org/project/MacroSignage/)
[![License](https://img.shields.io/github/license/BaezFJ/MacroSignage)](LICENSE)
<!-- Replace with GitHub Actions badge URL once CI is configured -->
[![Build](https://img.shields.io/badge/build-pending-lightgrey)]()

**A web-based digital signage system built with Flask and Bootstrap.**

MacroSignage lets you manage and display digital signage content through a modern browser-based interface. It uses Bootstrap v5.3.8 for responsive styling and Animate.css for smooth transitions.

> **Note:** This project is in Pre-Alpha (v0.2.0). APIs and features are subject to change.

<!-- TODO: Add screenshot once the dashboard UI is implemented -->
<!-- ![MacroSignage Screenshot](docs/images/screenshot.png) -->

## Features

### Current

- Flask application factory pattern (`create_app`)
- Bootstrap v5.3.8 CSS and JavaScript integration (vendored)
- Bootstrap theme overrides with light and dark mode support via CSS custom properties
- Animate.css for UI transitions (vendored)
- Jinja2 template inheritance (base + page templates)
- Admin dashboard with display management CRUD
- Media library CRUD for images, text, video, HTML, and YouTube media
- Many-to-many media assignment between displays and media assets
- Schedule CRUD with active windows, weekday rules, display targets, and media playlists
- SQLite-backed display persistence with Flask-SQLAlchemy
- CSRF protection for admin state-changing forms
- WSGI-ready entry point for production deployment
- Installable via PyPI (`pip install MacroSignage`)

### Planned

- User authentication and session management (Flask-Login)
- Database migrations (Flask-Migrate)
- Form handling with CSRF protection (Flask-WTF)
- Admin dashboard for managing signage content
- Schedule playback execution
- Media upload and content rotation
- REST API for programmatic control
- Real-time display updates via WebSocket or SSE

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

   # Or using the WSGI entry point
   python wsgi.py
   ```

2. **Open your browser** and navigate to `http://127.0.0.1:5000`

### Production Deployment

For production, use the packaged Waitress-backed command:

```bash
macrosignage prod --host 0.0.0.0 --port 8080
```

## Project Structure

```
MacroSignage/
├── src/
│   └── macrosignage/              # Main application package
│       ├── __init__.py            # App factory (create_app)
│       ├── static/
│       │   ├── css/
│       │   │   └── theme.css      # Bootstrap theme overrides
│       │   ├── js/                # Application JavaScript
│       │   └── vendor/            # Vendored frontend libraries
│       │       ├── bootstrap/     # Bootstrap v5.3.8
│       │       └── animate/       # Animate.css v4.1.1
│       └── templates/
│           ├── base.html          # Base template (shared layout)
│           └── pages/
│               └── index.html     # Home page
├── wsgi.py                        # WSGI entry point
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

### Areas Looking for Contributions

- User authentication system
- Database models and migrations
- Admin dashboard UI
- Test suite setup (pytest)
- CI/CD pipeline (GitHub Actions)
- Documentation improvements

## Roadmap

### v0.2.0 -- Foundation

- [ ] Application configuration system (python-dotenv integration)
- [ ] Database setup with Flask-SQLAlchemy
- [ ] User model and authentication with Flask-Login
- [ ] Form infrastructure with Flask-WTF
- [ ] Basic test suite with pytest

### v0.3.0 -- Core Features

- [ ] Admin dashboard layout
- [ ] Content/media management (upload, organize, delete)
- [ ] Display/screen registration and management
- [ ] Content-to-display assignment

### v0.4.0 -- Scheduling and Playback

- [ ] Content scheduling (time-based rotation)
- [ ] Signage display player view (fullscreen, auto-rotation)
- [ ] Playlist management

### v0.5.0 -- Polish and Scale

- [ ] REST API
- [ ] Real-time updates (WebSocket or SSE)
- [ ] Multi-user role support (admin, editor, viewer)
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Comprehensive documentation

### v1.0.0 -- Stable Release

- [ ] Production-hardened and fully tested
- [ ] Complete documentation
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
