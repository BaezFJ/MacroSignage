# Release Documentation Checklist

Use this checklist before pushing a release tag. It is intentionally manual because several display-player checks depend on browser codecs, YouTube availability, local network behavior, and display hardware.

## Landing and Install

- [ ] README status, quick start, production command, release automation, and v1.0 roadmap links are current.
- [ ] [Installation](installation.md) matches current PyPI/source setup commands.
- [ ] [Configuration](configuration.md) lists every supported `MACROSIGNAGE_*` setting and uses placeholder secrets only.
- [ ] `.env.example` matches the configuration reference.

## Admin Workflows

- [ ] [Auth and RBAC](auth-rbac.md) covers first admin setup, login/logout, password reset limits, users, and roles.
- [ ] [Display Management and Player Pairing](displays.md) covers display statuses, player token generation/rotation/disable, and browser/client pairing.
- [ ] [Media Library](media.md) covers image, text, neon sign, video, HTML, YouTube, slider media, fonts, uploads, and logo overlay.
- [ ] [Scheduling and Playback](scheduling.md) covers active/draft/paused schedules, weekdays, timezone handling, display/media assignments, and no-active-schedule behavior.
- [ ] Admin Settings pages remain readable at desktop and mobile widths, including diagnostics, database settings, logo settings, API tokens, and fonts.

## API and Integration

- [ ] [REST API](rest-api.md) matches current route methods, auth requirements, role requirements, response shapes, and validation errors.
- [ ] [API Tokens](api-tokens.md) covers create, reset, revoke, delete, ownership, hashed storage, and role inheritance.
- [ ] [Realtime and Player Behavior](realtime-player.md) covers SSE reload behavior, player states, and player API authentication.
- [ ] Example tokens, domains, passwords, and database URIs are placeholders.

## Deployment and Operations

- [ ] [Deployment](deployment.md) matches current `macrosignage-prod`, systemd, Docker, reverse proxy, health check, backup, restore, upgrade, and rollback guidance.
- [ ] [Troubleshooting](troubleshooting.md) covers login, API auth, display pairing, offline/maintenance pages, no active schedules, media uploads, database drivers, client GUI dependencies, health checks, and upgrade failures.
- [ ] Health check examples still match `/api/v1/health` response fields.
- [ ] Backup and rollback instructions avoid exposing secrets and credential-bearing database URIs.

## Client

- [ ] [Standalone Client](client.md) covers release executables, local run, CLI flags, saved config, pairing flow, Linux GUI dependencies, and release workflows.
- [ ] [client/README.md](../client/README.md) matches the client guide.
- [ ] GitHub Releases link points to `https://github.com/BaezFJ/MacroSignage/releases`.

## Manual Playback

- [ ] Browser player pairs with a generated display token.
- [ ] Rotating or disabling a display token invalidates existing player access.
- [ ] Online display with no playable schedules shows "No active schedules for display".
- [ ] Offline and maintenance display statuses show their dedicated pages.
- [ ] Image media renders.
- [ ] Text media renders.
- [ ] Video media renders on the target browser/device.
- [ ] HTML media renders in its sandboxed frame.
- [ ] YouTube media autoplays where browser policy allows it.
- [ ] Slider media cycles through backgrounds, foreground images, text, fonts, positions, durations, and animations.
- [ ] Global logo overlay appears in the configured position when enabled and stays hidden when disabled.
- [ ] Player reloads after media, schedule, status, logo, or font changes.

## Maintainer Docs

- [ ] [Development](development.md) matches CI commands and current package/client workflow names.
- [ ] [Architecture](architecture.md) matches current app factory, feature blueprints, data model, runtime schema strategy, player auth, SSE, API, static vendoring, and standalone client packaging.
- [ ] ADRs in `docs/decisions/` still describe accepted durable decisions.
- [ ] Documentation quality tests pass with `uv run python -m pytest tests/test_docs.py`.
