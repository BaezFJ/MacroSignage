# Auth and RBAC

MacroSignage uses Flask-Login for browser sessions and API bearer tokens for external clients.

## Roles

- `ADMIN`: full access, including users, settings, fonts, API tokens, and player token management.
- `EDITOR`: can create, update, and delete displays, media, and schedules.
- `VIEWER`: can read admin screens and read API resources but cannot mutate resources.

Inactive users cannot sign in, and API tokens owned by inactive users are rejected.
