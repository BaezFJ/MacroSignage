# ADR-001: Runtime Schema Strategy During Pre-Alpha

## Status

Accepted

## Date

2026-05-06

## Context

MacroSignage is still pre-alpha and has been evolving quickly. The app needs to keep local SQLite installs usable while models gain fields for sliders, player tokens, logo settings, and schedule timezone behavior.

The project already initializes Flask-Migrate, but many current installs are small self-hosted deployments where startup simplicity matters. Operators still need clear backup guidance before upgrades.

## Decision

Use SQLAlchemy table creation on startup plus additive runtime schema checks in `src/macrosignage/app.py` for the v0.x line.

Runtime schema checks may add missing columns for supported earlier v0.x databases. They should remain additive and conservative. Deployment docs require backing up the database, uploaded media, and environment file before upgrades.

## Alternatives Considered

### Flask-Migrate-only upgrades

- Pros: standard migration history and explicit upgrade steps.
- Cons: higher operator burden for early pre-alpha installs and local SQLite users.
- Rejected for now because the product is still changing quickly.

### Drop-and-recreate development databases

- Pros: simple for developers.
- Cons: unacceptable for real displays, uploaded media, users, tokens, and schedules.
- Rejected because users already operate persistent installs.

## Consequences

- Startup remains simple for current users.
- Schema changes must be additive during this phase.
- Operators must still back up before upgrades.
- A future stable release can move to explicit migration commands once the schema contract settles.
