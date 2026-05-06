# ADR-002: Token-Secured Display Players

## Status

Accepted

## Date

2026-05-06

## Context

Display players often run on unattended devices. They need to access the player page without a human admin session, but admins must be able to pair, rotate, disable, and remotely invalidate player access.

The same app also supports API bearer tokens for integrations. Display devices need a narrower authentication model than general API clients.

## Decision

Use display-specific player tokens for pairing and paired display access keys for ongoing browser/player access.

Each display can have one player token. The plaintext token is shown once, stored hashed, and can be rotated or disabled by an admin. Pairing stores a display access key in the browser session. Disabling or rotating access changes the display access key so existing paired sessions stop working.

Player API endpoints accept `X-Display-Token` or `X-Display-Access-Key`. Admin API endpoints continue to use user-owned bearer API tokens.

## Alternatives Considered

### Require admin login on every player

- Pros: reuses existing browser authentication.
- Cons: awkward on unattended devices, exposes admin session behavior to players, and makes remote device setup harder.
- Rejected because player identity should be display-specific.

### Use general API bearer tokens for players

- Pros: one token system.
- Cons: API tokens inherit user roles and can grant broader access than a player needs.
- Rejected because player access should be narrow and remotely revocable per display.

## Consequences

- Display devices can be paired without admin credentials.
- Admins can disable or rotate a single display's access remotely.
- Player token handling must avoid query-string tokens and must show plaintext secrets only once.
- API docs must distinguish display player headers from bearer API tokens.
