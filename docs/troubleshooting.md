# Troubleshooting

Use this guide by symptom. Do not paste real passwords, API tokens, display tokens, or database URIs with credentials into issue trackers or shared chats.

## Login Redirects Repeatedly

Likely causes:

- No first admin account exists.
- The user account is inactive.
- The browser session cookie cannot be stored.
- `MACROSIGNAGE_SECRET_KEY` changed and existing sessions were invalidated.

Checks:

- Open `/auth/setup` only on a new install. If users already exist, use `/auth/login`.
- Ask an admin to verify the user is active from `/admin/users/`.
- If served over HTTPS, set `MACROSIGNAGE_SESSION_COOKIE_SECURE=true`.
- If served over plain HTTP in local development, leave `MACROSIGNAGE_SESSION_COOKIE_SECURE=false`.

See [Auth and RBAC](auth-rbac.md) and [Configuration](configuration.md).

## Password Reset Does Not Send Email

MacroSignage prepares password reset tokens but does not include an outbound email sender. In development, reset links can be shown on screen when reset-link display is enabled by app config.

Checks:

- For production, use admin user management at `/admin/users/` until an email delivery process is integrated.
- Confirm the account email is correct and the user is active.

See [Auth and RBAC](auth-rbac.md).

## API Returns `401`

Likely causes:

- Missing `Authorization: Bearer ...` header.
- Token was reset, revoked, or deleted.
- Token owner is inactive.
- A display player endpoint is being called with an API bearer token instead of display headers.

Checks:

```bash
curl http://127.0.0.1:8080/api/v1/health
curl http://127.0.0.1:8080/api/v1/displays -H "Authorization: Bearer ms_PLACEHOLDER_TOKEN"
```

Verify the token in `/admin/api-tokens/` and the owner in `/admin/users/`.

See [API Tokens](api-tokens.md) and [REST API](rest-api.md).

## API Returns `403`

The token is valid, but the owner role is too low for the action.

Checks:

- `VIEWER` tokens can read resources.
- `EDITOR` tokens can mutate displays, media, and schedules.
- `ADMIN` tokens are required for users and font creation.

See [REST API](rest-api.md).

## Display Pairing Fails

Likely causes:

- Display token was copied incorrectly.
- Display token was disabled or rotated.
- Browser or client is posting to the wrong server URL.
- The player was already paired before the token was rotated.

Checks:

- Generate or rotate the token from the admin display detail page and copy the newly shown token immediately.
- Confirm the standalone client server URL points to the MacroSignage base URL, not `/admin`.
- Use `--reset` with the standalone client before pairing a reassigned device:

```bash
cd client
uv run macrosignage-client --reset --setup --windowed
```

See [Display Management and Player Pairing](displays.md) and [Standalone Client](client.md).

## Display Shows Offline or Maintenance

The display status overrides scheduled media.

Checks:

- Open the display detail page from `/admin/displays/`.
- Set status to `Online` when the player should evaluate schedules.
- Use `Offline` or `Maintenance` intentionally for remote stop/maintenance states.

See [Display Management and Player Pairing](displays.md).

## Display Shows "No Active Schedules for Display"

Likely causes:

- No schedule is assigned to the display.
- Schedule is `Draft` or `Paused`.
- Start/end time window does not include the current time.
- Weekday rules do not include the current local weekday.
- Schedule has no media assigned.
- `MACROSIGNAGE_TIMEZONE` is missing or not the intended timezone.

Checks:

- Open `/admin/schedules/` and inspect the schedule status, display assignments, media assignments, weekdays, and start/end times.
- Check `/admin/settings/` for operational diagnostics.
- Confirm `MACROSIGNAGE_TIMEZONE` in `.env`, then restart MacroSignage after changing it.

See [Scheduling and Playback](scheduling.md) and [Configuration](configuration.md).

## Player Does Not Update

Likely causes:

- The player is not paired anymore.
- The reverse proxy closes server-sent event connections.
- The browser lost network access.

Checks:

- Refresh the player page once.
- Confirm `/displays/<display_id>/events` is reachable from the player browser after pairing.
- For reverse proxies, use a long read timeout; Nginx deployments can set `proxy_read_timeout 3600`.
- Check `/api/v1/health` and compare `contentVersion` after admin content changes.

See [Realtime and Player Behavior](realtime-player.md) and [Deployment](deployment.md).

## Media Upload Fails

Likely causes:

- Unsupported file extension or MIME type.
- Upload exceeds `MACROSIGNAGE_MAX_UPLOAD_BYTES`.
- Reverse proxy upload limit is lower than MacroSignage's limit.
- `MACROSIGNAGE_MEDIA_UPLOAD_FOLDER` is missing or not writable.

Checks:

- Use supported image/video formats from [Media Library](media.md).
- Check the configured max upload size in [Configuration](configuration.md).
- Verify the app process can write to the media upload directory.
- For Nginx, set `client_max_body_size` to match the intended upload limit.

## Database Driver or Connection Fails

Likely causes:

- `MACROSIGNAGE_DATABASE_URI` has the wrong dialect/driver.
- Required Python database driver is not installed.
- Database host, port, username, password, or database name is wrong.
- SQLite path is not writable by the app process.

Checks:

- Open `/admin/settings/database` and review the selected database type and driver help.
- Install the required driver in the same environment that runs MacroSignage.
- Restart MacroSignage after changing `.env`.
- Check `/api/v1/health`; database readiness should be `ready: true`.

See [Configuration](configuration.md) and [Deployment](deployment.md).

## Client Reports Missing Qt or GTK

The standalone pywebview client needs a GUI backend.

Checks on Ubuntu:

```bash
cd client
uv sync --reinstall
uv run macrosignage-client --setup --windowed
```

If platform libraries are missing:

```bash
sudo apt update
sudo apt install libegl1 libgl1 libxcb-cursor0 libxkbcommon-x11-0
```

Prebuilt executables are available from `https://github.com/BaezFJ/MacroSignage/releases`.

See [Standalone Client](client.md).

## Health Check Is Degraded

`/api/v1/health` returns `503` when database or media storage readiness fails.

Checks:

```bash
curl http://127.0.0.1:8080/api/v1/health
```

Review:

- `checks.database.ready`
- `checks.mediaStorage.exists`
- `checks.mediaStorage.writable`
- app logs from `journalctl -u macrosignage -f` for systemd
- container logs from `docker compose -f deploy/docker/docker-compose.yml logs -f`

See [Deployment](deployment.md).

## Upgrade Fails on Startup

Stop MacroSignage and keep the failed database unchanged for inspection. Restore the pre-upgrade database and media backups if the app must return to service quickly, then check the startup log for the first schema or driver error.

Common checks:

- Confirm `MACROSIGNAGE_DATABASE_URI` points to the expected database.
- Confirm the selected database driver is installed.
- Confirm the app process can write to the SQLite database file or connect to the external database.
- Confirm the media folder exists and is writable.
- Review [Deployment](deployment.md) for the backup, upgrade, restore, and rollback order.
