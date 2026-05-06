# Installation

## Requirements

- Python 3.10 or newer
- `uv`

## Local install

```bash
uv sync
cp .env.example .env
uv run macrosignage dev
```

The development server reads `.env` automatically and creates the SQLite database and media folder under the Flask instance directory unless configured otherwise.

## Package build

```bash
uv build
uv run twine check dist/*
```

## Production install

For self-hosted production installs, use the production CLI behind a reverse proxy:

```bash
uv pip install MacroSignage
MACROSIGNAGE_SECRET_KEY='change-this-to-a-long-random-value' \
MACROSIGNAGE_DATABASE_URI='sqlite:////var/lib/macrosignage/macrosignage.sqlite3' \
MACROSIGNAGE_MEDIA_UPLOAD_FOLDER='/var/lib/macrosignage/media' \
macrosignage-prod --host 127.0.0.1 --port 8080 --threads 4
```

See [Configuration](configuration.md) for all environment variables and [Deployment](deployment.md) for systemd, Docker, health checks, backups, HTTPS, and rollback examples.
