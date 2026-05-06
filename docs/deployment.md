# Deployment

## Production checklist

- Set `MACROSIGNAGE_SECRET_KEY` to a unique non-default value. The production CLI refuses to start with the development default.
- Use a persistent `MACROSIGNAGE_DATABASE_URI`. SQLite is the default, and PostgreSQL/MySQL-style SQLAlchemy URIs are supported when the matching database driver is installed.
- Use a persistent `MACROSIGNAGE_MEDIA_UPLOAD_FOLDER`.
- Serve over HTTPS and set `MACROSIGNAGE_SESSION_COOKIE_SECURE=true`.
- Set `MACROSIGNAGE_ENABLE_HSTS=true` after HTTPS is stable for the domain.
- Run behind a production WSGI server such as Waitress.
- Review production warnings on the admin settings page after startup.

## Example

```bash
MACROSIGNAGE_SECRET_KEY='change-this-to-a-long-random-value' \
MACROSIGNAGE_SESSION_COOKIE_SECURE=true \
MACROSIGNAGE_ENABLE_HSTS=true \
uv run macrosignage prod
```

## Health and diagnostics

Use the unauthenticated health endpoint for load balancers and uptime checks:

```bash
curl http://127.0.0.1:8080/api/v1/health
```

The response reports application version, database readiness, media storage readiness, and the current content version used by display players. It intentionally does not include secrets, bearer tokens, display tokens, or database passwords.

Admins can also review Operational Diagnostics from `/admin/settings/`. That page shows redacted configuration status, including whether the secret key is configured, secure cookies are enabled, HSTS is enabled, the database is reachable, media storage is writable, and the player content version.

## systemd

The repository includes a copy-pasteable unit at `deploy/systemd/macrosignage.service`. A typical host layout is:

```bash
sudo useradd --system --home /opt/macrosignage --shell /usr/sbin/nologin macrosignage
sudo mkdir -p /opt/macrosignage /etc/macrosignage /var/lib/macrosignage/media
sudo chown -R macrosignage:macrosignage /opt/macrosignage /var/lib/macrosignage
cd /opt/macrosignage
uv venv
uv pip install MacroSignage
```

Create `/etc/macrosignage/macrosignage.env`:

```dotenv
MACROSIGNAGE_SECRET_KEY=change-this-to-a-long-random-value
MACROSIGNAGE_DATABASE_URI=sqlite:////var/lib/macrosignage/macrosignage.sqlite3
MACROSIGNAGE_MEDIA_UPLOAD_FOLDER=/var/lib/macrosignage/media
MACROSIGNAGE_SESSION_COOKIE_SECURE=true
MACROSIGNAGE_ENABLE_HSTS=true
```

Install and start the service:

```bash
sudo cp deploy/systemd/macrosignage.service /etc/systemd/system/macrosignage.service
sudo systemctl daemon-reload
sudo systemctl enable --now macrosignage
sudo systemctl status macrosignage
sudo journalctl -u macrosignage -f
```

The service runs as the `macrosignage` user, reads `/etc/macrosignage/macrosignage.env`, starts `macrosignage-prod --host 127.0.0.1 --port 8080 --threads 4`, restarts on failure, and writes logs to journald.

## Docker

The repository includes `deploy/docker/Dockerfile` and `deploy/docker/docker-compose.yml`.

Create `deploy/docker/.env`:

```dotenv
MACROSIGNAGE_SECRET_KEY=change-this-to-a-long-random-value
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

## Upgrade order

MacroSignage currently applies additive runtime schema updates on startup for supported v0.x databases. Treat every package upgrade as a data change:

1. Stop MacroSignage.
2. Back up the database, uploaded media folder, and `.env` file.
3. Upgrade the package or deploy the new release.
4. Start MacroSignage once and watch the logs for startup errors.
5. Sign in to the admin dashboard and review Settings for database and production warnings.
6. Confirm at least one display player can load its active schedule.

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
