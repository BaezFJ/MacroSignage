# MacroSignage

A web-based digital signage system built with Flask. Create, manage, and display
dynamic signage content from any browser.

## Features

- Web-based administration interface
- User authentication and management
- Template-driven signage displays
- File upload support for media content
- SQLite database (no external database required)

## Installation

```bash
pip install macrosignage
```

## Quick Start

Run the built-in development server:

```bash
macrosignage
```

This starts the application at `http://127.0.0.1:5000`. Visit
`http://127.0.0.1:5000/init-db` on first run to initialize the database.

### Options

```bash
macrosignage --host=0.0.0.0 --port=8080 --debug
```

### Using Flask directly

```bash
export FLASK_APP=macrosignage:macro_signage_app
flask run
```

## Development

Clone the repository and install with development dependencies:

```bash
git clone https://github.com/baezfb/MacroSignage.git
cd MacroSignage
uv sync
uv run macrosignage --debug
```

## License

MIT License. See [LICENSE](LICENSE) for details.
