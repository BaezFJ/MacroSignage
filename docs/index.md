# MacroSignage Documentation

MacroSignage is a Flask-based digital signage manager with an admin console, display player, scheduling, token-secured players, and a JSON API.

## New Users

- [Installation](installation.md): install from source or PyPI, run locally, and find production install notes.
- [Configuration](configuration.md): configure environment variables, database settings, upload storage, and first-run setup.
- [Auth and RBAC](auth-rbac.md): understand sign-in, user roles, inactive users, and browser/API access control.
- [Display Management and Player Pairing](displays.md): create displays, manage player tokens, pair players, and handle offline or maintenance states.

## Admins and Operators

- [Media Library](media.md): manage image, text, video, HTML, YouTube, and slider media with fonts and logo overlays.
- [Scheduling and Playback](scheduling.md): configure active playback windows, weekdays, display assignments, and no-active-schedule behavior.
- [Standalone Client](client.md): install, pair, reset, debug, and package the pywebview display client.
- [API Tokens](api-tokens.md): create and manage bearer tokens for external integrations.
- [Realtime and Player Behavior](realtime-player.md): understand display player refresh behavior, SSE updates, and player API access.
- [Deployment](deployment.md): deploy with production settings, health checks, backups, systemd, Docker, and HTTPS.
- [Troubleshooting](troubleshooting.md): diagnose common sign-in, API, player, and upgrade issues.

## API Integrators

- [REST API](rest-api.md): review API authentication, error shape, and available JSON endpoints.

## Contributors

- [Development](development.md): run checks, understand project structure, and follow release automation.
- [Architecture](architecture.md): understand app factory setup, feature blueprints, data model, player auth, SSE, and ADRs.
- [Release Documentation Checklist](release-documentation-checklist.md): review docs, admin workflows, API guidance, deployment, client setup, and manual playback before tagging.

## Roadmaps

- [Production Hardening Roadmap](production-hardening-roadmap.md)
- [Complete Documentation Roadmap](documentation-roadmap.md)
