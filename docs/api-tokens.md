# API Tokens

Admins manage API tokens at `/admin/api-tokens/`.

Tokens are shown only once when created. MacroSignage stores a SHA-256 hash and a short prefix, not the plaintext token.

Use a token with the REST API:

```bash
curl -H "Authorization: Bearer ms_example" http://localhost:5000/api/v1/displays
```

The token inherits the role of its owner. Revoke tokens immediately when a client should no longer have API access.
