# API Tokens

Admins manage API tokens at `/admin/api-tokens/`.

API tokens authenticate external integrations against `/api/v1`. They are different from display player tokens and browser login sessions.

## Token Lifecycle

### Create

An admin creates a token by choosing a name and active owner user. MacroSignage shows the plaintext token once. Copy it immediately.

Token strings start with `ms_`, for example:

```text
ms_PLACEHOLDER_TOKEN_VALUE
```

Do not store the plaintext token in source control, docs, screenshots, or issue comments.

### Store

MacroSignage stores:

- token name
- short token prefix for identification
- SHA-256 token hash
- active/inactive state
- owner user
- last used timestamp
- created/updated timestamps

MacroSignage does not store the plaintext token. If it is lost, reset it.

### Reset

Resetting a token generates a new plaintext token, replaces the stored hash and prefix, marks the token active, and clears `last_used_at`.

The previous plaintext token stops working immediately.

### Revoke

Revoking a token marks it inactive. The database record remains for audit and ownership context. Requests using a revoked token return `401`.

### Delete

Deleting a token removes the database record. Requests using the deleted token return `401`.

## Ownership and Roles

Every API token belongs to a user. The token inherits the owner's current role:

| Owner role | Token can do |
| --- | --- |
| `VIEWER` | Read API resources. |
| `EDITOR` | Read resources and mutate displays, media, and schedules. |
| `ADMIN` | Editor access plus users and font creation. |

If the owner user is inactive, the token is rejected even when the token itself is active.

## Curl Examples

Use placeholders in docs and scripts, then inject real tokens from your secret manager or environment.

Viewer read:

```bash
curl http://localhost:5000/api/v1/displays \
  -H "Authorization: Bearer ms_PLACEHOLDER_VIEWER_TOKEN"
```

Editor create display:

```bash
curl -X POST http://localhost:5000/api/v1/displays \
  -H "Authorization: Bearer ms_PLACEHOLDER_EDITOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Lobby","status":"ONLINE","orientation":"LANDSCAPE"}'
```

Admin create user:

```bash
curl -X POST http://localhost:5000/api/v1/users \
  -H "Authorization: Bearer ms_PLACEHOLDER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"operator","email":"operator@example.invalid","password":"replace-with-a-long-password","role":"EDITOR","active":true}'
```

## Operational Notes

Create separate tokens per integration instead of sharing one token across tools. Give the token owner the lowest role that can perform the required action.

Rotate tokens when a team member leaves, a deployment secret may have been exposed, or an integration no longer needs long-lived access.

Use display player tokens for player pairing. Use API bearer tokens for administrative integrations.
