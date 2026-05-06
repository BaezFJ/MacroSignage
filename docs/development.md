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

## Release automation

- `.github/workflows/ci.yml` runs tests, compile checks, package build, and `twine check`.
- `.github/workflows/publish-pypi.yml` publishes MacroSignage to PyPI when a `v*` tag is pushed.
- `.github/workflows/client-build.yml` builds standalone client executables on demand and for `v*` tags.
- `.github/workflows/client-release.yml` uploads standalone client executables to the matching GitHub Release.

## Test coverage notes

The automated suite covers Flask route contracts, admin CRUD workflows, API authorization, player-token access, schedule selection logic, package metadata, and CLI entry point parsing. Browser media playback for real image, video, YouTube, HTML iframe, and slider timing should still be checked manually before a production release because it depends on browser codecs, network access, and display hardware behavior.

## Project shape

Feature code lives under `src/macrosignage/features/`. Admin, displays, media, schedules, auth, and API routes are registered through the application factory.

Use the existing blueprint pattern for new features and keep templates grouped by feature.
