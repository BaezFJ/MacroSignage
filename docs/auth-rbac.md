# Auth and RBAC

MacroSignage uses Flask-Login for browser sessions and API bearer tokens for external clients.

## First Admin Setup

Open `/auth/setup` on a new installation to create the first admin account. This page is only available while the user table is empty. The account created here is active and has the `ADMIN` role.

After the first account exists, use `/auth/login` to sign in and `/auth/logout` to end the browser session. Admin pages redirect anonymous users to the login page.

If the first admin password is lost before any other admin exists, recover access at the database or deployment layer. MacroSignage intentionally does not provide an unauthenticated way to create another admin after setup is complete.

## Roles

- `ADMIN`: full access, including users, settings, fonts, API tokens, and player token management.
- `EDITOR`: can create, update, and delete displays, media, and schedules.
- `VIEWER`: can read admin screens and read API resources but cannot mutate resources.

Inactive users cannot sign in, and API tokens owned by inactive users are rejected.

Role checks map to the admin UI this way:

| Role | Typical access |
| --- | --- |
| `ADMIN` | Manage users, settings, fonts, logo settings, database settings, API tokens, display player tokens, displays, media, and schedules. |
| `EDITOR` | Manage display, media, and schedule records, but cannot manage users, app settings, API tokens, fonts, or player tokens. |
| `VIEWER` | Read admin screens and API resources for inspection without changing records. |

## User Management

Admins manage users from `/admin/users/`.

The user management page supports creating users, editing username/email/role/active state, and deleting users. Use inactive state when you want to preserve ownership history but stop browser login and API token access.

Do not demote or deactivate the only usable admin account unless another active admin already exists.

## Password Reset

Users can request a password reset at `/auth/password-reset`.

MacroSignage creates a short-lived reset token for the matching email address. In development, or when reset-link display is explicitly enabled in app config, the reset URL is shown on screen for testing. In normal production deployments, the request page shows a generic success message and does not expose the reset link.

Before relying on self-service password reset in production, connect the reset-token flow to an outbound email or operator-controlled delivery process. Until then, admins should reset user access by editing users from `/admin/users/`.

## Browser Sessions and API Tokens

Browser sessions use the signed Flask session cookie. Set a strong `MACROSIGNAGE_SECRET_KEY` and use secure cookie settings in production.

API bearer tokens are managed separately from browser passwords. Tokens inherit the owner's role and are rejected when the owner is inactive. See [API Tokens](api-tokens.md) and [REST API](rest-api.md) for integration details.
