# Deployment

## Production checklist

- Run MacroSignage with `macrosignage-prod` behind a reverse proxy.
- Set `MACROSIGNAGE_SECRET_KEY` to a unique non-default value. The production CLI refuses to start with the development default.
- Use a persistent `MACROSIGNAGE_DATABASE_URI`. SQLite is the default, and PostgreSQL/MySQL-style SQLAlchemy URIs are supported when the matching database driver is installed.
- Use a persistent `MACROSIGNAGE_MEDIA_UPLOAD_FOLDER`.
- Set `MACROSIGNAGE_TIMEZONE` before creating schedules.
- Serve over HTTPS and set `MACROSIGNAGE_SESSION_COOKIE_SECURE=true`.
- Set `MACROSIGNAGE_ENABLE_HSTS=true` after HTTPS is stable for the domain.
- Configure health checks against `/api/v1/health`.
- Back up the database, upload folder, env file, and package version before upgrades.
- Review production warnings on the admin settings page after startup.

## Production command

```bash
MACROSIGNAGE_SECRET_KEY='change-this-to-a-long-random-value' \
MACROSIGNAGE_DATABASE_URI='sqlite:////var/lib/macrosignage/macrosignage.sqlite3' \
MACROSIGNAGE_MEDIA_UPLOAD_FOLDER='/var/lib/macrosignage/media' \
MACROSIGNAGE_TIMEZONE=America/Chicago \
MACROSIGNAGE_SESSION_COOKIE_SECURE=true \
MACROSIGNAGE_ENABLE_HSTS=true \
macrosignage-prod --host 127.0.0.1 --port 8080 --threads 4
```

The `macrosignage-prod` command runs Waitress. Use `--threads` to set the Waitress worker thread count. If Waitress logs short queue-depth warnings under load, increase threads, reduce slow requests, or place the app behind a reverse proxy/load balancer that can queue traffic.

## Health and diagnostics

Use the unauthenticated health endpoint for load balancers and uptime checks:

```bash
curl http://127.0.0.1:8080/api/v1/health
```

Response fields:

```json
{
  "status": "ok",
  "ready": true,
  "version": "0.2.4",
  "contentVersion": 1,
  "playerUpdates": {
    "contentVersion": 1
  },
  "checks": {
    "database": {
      "status": "ok",
      "ready": true
    },
    "mediaStorage": {
      "status": "ok",
      "ready": true,
      "configured": true,
      "exists": true,
      "writable": true
    }
  }
}
```

The endpoint returns `200` when `ready` is true and `503` when database or media storage checks fail. It intentionally does not include secrets, bearer tokens, display tokens, or database passwords.

Admins can also review Operational Diagnostics from `/admin/settings/`. That page shows redacted configuration status, including whether the secret key is configured, secure cookies are enabled, HSTS is enabled, the database is reachable, media storage is writable, and the player content version.

## systemd

The repository includes a unit at `deploy/systemd/macrosignage.service`. It runs:

```text
/opt/macrosignage/.venv/bin/macrosignage-prod --host 127.0.0.1 --port 8080 --threads 4
```

A typical host layout is:

```bash
sudo useradd --system --home /opt/macrosignage --shell /usr/sbin/nologin macrosignage
sudo install -d -o macrosignage -g macrosignage /opt/macrosignage
sudo install -d -o macrosignage -g macrosignage /var/lib/macrosignage/media
sudo install -d -m 0750 -o root -g macrosignage /etc/macrosignage
sudo install -m 0755 "$(command -v uv)" /usr/local/bin/uv
sudo -u macrosignage -H sh -c 'cd /opt/macrosignage && /usr/local/bin/uv venv && /usr/local/bin/uv pip install MacroSignage'
```

Run the `uv venv` and `uv pip install` commands as the `macrosignage` service user. The virtual environment is created at `/opt/macrosignage/.venv`, so running `uv venv` as a different user will fail with `Permission denied` unless that user can write to `/opt/macrosignage`. Use `/usr/local/bin/uv` because user-local installs such as `~/.local/bin/uv` are usually not available in the sanitized `sudo -u macrosignage` environment.

Create `/etc/macrosignage/macrosignage.env`:

```dotenv
MACROSIGNAGE_SECRET_KEY=change-this-to-a-long-random-value
MACROSIGNAGE_DATABASE_URI=sqlite:////var/lib/macrosignage/macrosignage.sqlite3
MACROSIGNAGE_MEDIA_UPLOAD_FOLDER=/var/lib/macrosignage/media
MACROSIGNAGE_MAX_UPLOAD_BYTES=104857600
MACROSIGNAGE_TIMEZONE=America/Chicago
MACROSIGNAGE_SESSION_COOKIE_SECURE=false
MACROSIGNAGE_ENABLE_HSTS=false
```

Set `MACROSIGNAGE_SESSION_COOKIE_SECURE=true` and `MACROSIGNAGE_ENABLE_HSTS=true` only after MacroSignage is served over HTTPS. If these are enabled while testing over plain HTTP, browsers will not send the session cookie back to the server and login forms can fail CSRF validation.

Install and start the service:

```bash
sudo cp deploy/systemd/macrosignage.service /etc/systemd/system/macrosignage.service
sudo systemctl daemon-reload
sudo systemctl enable --now macrosignage
sudo systemctl status macrosignage
sudo journalctl -u macrosignage -f
```

The service runs as the `macrosignage` user, reads `/etc/macrosignage/macrosignage.env`, starts `macrosignage-prod --host 127.0.0.1 --port 8080 --threads 4`, restarts on failure, and writes logs to journald.

If `systemctl status macrosignage` shows `status=203/EXEC`, systemd could not execute `/opt/macrosignage/.venv/bin/macrosignage-prod`. Confirm the virtual environment and entry point exist:

```bash
sudo ls -l /opt/macrosignage/.venv/bin/macrosignage-prod /opt/macrosignage/.venv/bin/python
sudo -u macrosignage -H /opt/macrosignage/.venv/bin/macrosignage-prod --help
sudo journalctl -u macrosignage -n 50 --no-pager
```

If the files are missing or not executable, recreate the virtual environment as the service user, then restart systemd:

```bash
sudo chown -R macrosignage:macrosignage /opt/macrosignage
sudo install -m 0755 "$(command -v uv)" /usr/local/bin/uv
sudo -u macrosignage -H sh -c 'cd /opt/macrosignage && /usr/local/bin/uv venv && /usr/local/bin/uv pip install MacroSignage'
sudo systemctl restart macrosignage
sudo systemctl status macrosignage
```

## Docker

The repository includes `deploy/docker/Dockerfile` and `deploy/docker/docker-compose.yml`.

Create `deploy/docker/.env`:

```dotenv
MACROSIGNAGE_SECRET_KEY=change-this-to-a-long-random-value
MACROSIGNAGE_TIMEZONE=America/Chicago
MACROSIGNAGE_SESSION_COOKIE_SECURE=true
MACROSIGNAGE_ENABLE_HSTS=true
```

Run:

```bash
docker compose -f deploy/docker/docker-compose.yml up -d --build
docker compose -f deploy/docker/docker-compose.yml logs -f
```

The compose file publishes port `8080`, stores SQLite and uploads in the `macrosignage-data` volume, and sets:

```dotenv
MACROSIGNAGE_DATABASE_URI=sqlite:////data/macrosignage.sqlite3
MACROSIGNAGE_MEDIA_UPLOAD_FOLDER=/data/media
```

For PostgreSQL or MySQL, replace `MACROSIGNAGE_DATABASE_URI` with the external SQLAlchemy URI and install the matching database driver in a derived image.

## Reverse proxy HTTPS

Terminate HTTPS at a reverse proxy such as Nginx, Caddy, Traefik, or a managed load balancer. Forward traffic to `http://127.0.0.1:8080` for systemd deployments or to the Docker service port.

Minimum proxy requirements:

- Preserve `Host`, `X-Forwarded-Proto`, and client IP headers.
- Redirect HTTP to HTTPS.
- Set `MACROSIGNAGE_SESSION_COOKIE_SECURE=true` after HTTPS is enabled.
- Set `MACROSIGNAGE_ENABLE_HSTS=true` only after HTTPS is stable for the domain.

Minimal Nginx location block:

```nginx
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 3600;
}
```

Use a long `proxy_read_timeout` so display player server-sent event streams can stay open.

If users upload large media files, also configure the proxy upload limit. For Nginx, set `client_max_body_size` to a value at least as large as `MACROSIGNAGE_MAX_UPLOAD_BYTES`.

## Upgrade order

MacroSignage currently applies additive runtime schema updates on startup for supported v0.x databases. Treat every package upgrade as a data change:

1. Stop MacroSignage.
2. Back up the database, uploaded media folder, and `.env` file.
3. Upgrade the package or deploy the new release.
4. Start MacroSignage once and watch the logs for startup errors.
5. Sign in to the admin dashboard and review Settings for database and production warnings.
6. Check `curl http://127.0.0.1:8080/api/v1/health`.
7. Confirm at least one display player can load its active schedule.

Do not switch database providers and upgrade the application in the same maintenance step. Upgrade first, verify, then change `MACROSIGNAGE_DATABASE_URI` in a separate step.

## Backups

Back up these items together so the database rows still match the files and configuration they reference:

- Database: `MACROSIGNAGE_DATABASE_URI`
- Uploaded media: `MACROSIGNAGE_MEDIA_UPLOAD_FOLDER`
- Environment file: `.env` or the file shown in admin Settings
- Package version: the exact MacroSignage version being replaced

### SQLite

For the default SQLite database, stop the app and copy the database file before upgrading:

```bash
cp instance/macrosignage.sqlite3 backups/macrosignage-$(date +%Y%m%d-%H%M%S).sqlite3
```

If the app must stay online while backing up SQLite, use SQLite's online backup command from the host:

```bash
sqlite3 instance/macrosignage.sqlite3 ".backup 'backups/macrosignage-$(date +%Y%m%d-%H%M%S).sqlite3'"
```

### PostgreSQL, MySQL, MariaDB, SQL Server, and Oracle

Use the native backup tool for the selected database engine. Examples:

```bash
pg_dump "$MACROSIGNAGE_DATABASE_URI" > backups/macrosignage-$(date +%Y%m%d-%H%M%S).sql
mysqldump --single-transaction macrosignage > backups/macrosignage-$(date +%Y%m%d-%H%M%S).sql
```

Keep database credentials out of shell history where possible by using protected environment files or native client configuration files.

### Uploaded media and environment

Back up the media directory and environment file in the same maintenance window as the database:

```bash
tar -czf backups/macrosignage-media-$(date +%Y%m%d-%H%M%S).tar.gz instance/media
cp .env backups/macrosignage-env-$(date +%Y%m%d-%H%M%S)
```

## Restore and rollback

1. Stop MacroSignage.
2. Restore the previous package version.
3. Restore `.env`.
4. Restore the database backup.
5. Restore `MACROSIGNAGE_MEDIA_UPLOAD_FOLDER`.
6. Start MacroSignage and check the admin dashboard plus a display player.

For SQLite, restoring usually means replacing the database file while the app is stopped:

```bash
cp backups/macrosignage-YYYYMMDD-HHMMSS.sqlite3 instance/macrosignage.sqlite3
```

For external databases, restore with the native tool for that engine. If an upgrade already added columns, rolling the package back may leave extra columns in place; restore the pre-upgrade database backup when you need a clean rollback.

After restore, verify:

```bash
curl http://127.0.0.1:8080/api/v1/health
```

Then sign in, open `/admin/settings/`, and load a paired display player.
