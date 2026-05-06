# Development

## Run checks

```bash
uv lock --check
uv run python -m pytest
uv run python -m unittest discover -s tests
uv run python -m compileall src/macrosignage tests
uv build
uv run twine check dist/*
```

## Project shape

Feature code lives under `src/macrosignage/features/`. Admin, displays, media, schedules, auth, and API routes are registered through the application factory.

Use the existing blueprint pattern for new features and keep templates grouped by feature.
