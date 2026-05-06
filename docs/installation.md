# Installation

## Requirements

- Python 3.10 or newer
- `uv`

## Local install

```bash
uv sync
uv run macrosignage dev
```

The development server reads `.env` automatically and creates the SQLite database and media folder under the Flask instance directory unless configured otherwise.

## Package build

```bash
uv build
uv run twine check dist/*
```
