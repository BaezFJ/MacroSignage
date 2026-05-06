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
