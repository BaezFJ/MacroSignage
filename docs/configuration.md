# Configuration

MacroSignage loads environment variables from `.env` before the Flask app is configured. The default env file is the `.env` file in the current working directory.

The admin Settings page shows the loaded env file path, redacted database status, production warnings, and operational diagnostics.

## Environment Variables

| Variable | Default | Restart required | Production guidance |
| --- | --- | --- | --- |
| `MACROSIGNAGE_ENV` | unset | yes | Set to `production` or `prod` when running production deployments. The `macrosignage-prod` CLI also enables production mode internally. |
| `MACROSIGNAGE_SECRET_KEY` | development default | yes | Required in production. Use a long random value from a secret manager. The production CLI refuses the development default. |
| `MACROSIGNAGE_DATABASE_URI` | SQLite in the Flask instance directory | yes | Use persistent storage. Install the matching database driver for non-SQLite engines. |
| `MACROSIGNAGE_MEDIA_UPLOAD_FOLDER` | `media` under the Flask instance directory | yes | Use persistent storage and include it in backups. |
| `MACROSIGNAGE_MAX_UPLOAD_BYTES` | `104857600` | yes | Default is 100 MB. Increase only when the reverse proxy and storage limits are also configured. |
| `MACROSIGNAGE_TIMEZONE` | server local timezone | yes | Set an IANA timezone, such as `America/Chicago`, before creating production schedules. |
| `MACROSIGNAGE_SESSION_COOKIE_SECURE` | `false` | yes | Set to `true` when MacroSignage is served over HTTPS. |
| `MACROSIGNAGE_ENABLE_HSTS` | `false` | yes | Set to `true` only after HTTPS is stable for the production domain. |

Boolean variables accept `true`, `1`, or `yes` for enabled values.

Internal app config keys such as `MACROSIGNAGE_ENV_FILE`, `MACROSIGNAGE_PRODUCTION`, and `MACROSIGNAGE_CONFIG_WARNINGS` are derived by the app. Do not set them directly in `.env`.

## Example `.env`

```dotenv
MACROSIGNAGE_ENV=production
MACROSIGNAGE_SECRET_KEY=replace-with-a-long-random-secret
MACROSIGNAGE_DATABASE_URI=sqlite:////var/lib/macrosignage/macrosignage.sqlite3
MACROSIGNAGE_MEDIA_UPLOAD_FOLDER=/var/lib/macrosignage/media
MACROSIGNAGE_MAX_UPLOAD_BYTES=104857600
MACROSIGNAGE_TIMEZONE=America/Chicago
MACROSIGNAGE_SESSION_COOKIE_SECURE=true
MACROSIGNAGE_ENABLE_HSTS=true
```

Keep `.env` out of version control and restrict file permissions on shared hosts.

## First Run

Open `/auth/setup` to create the first admin account. After setup, users sign in at `/auth/login`.

See [Auth and RBAC](auth-rbac.md) for role behavior, password reset limitations, and user management.

## Database Selection

SQLite is the default:

```text
sqlite:///instance/macrosignage.sqlite3
```

Admins can review the current database from `/admin/settings/` and open the dedicated database page from the Manage database button. The database form includes presets for SQLite, PostgreSQL, MySQL, MariaDB, Microsoft SQL Server, and Oracle. SQLite asks for a file location; server databases ask for host, port, username, password, database name, and optional query parameters. Advanced users can enter a raw SQLAlchemy URI.

The settings page shows the required Python driver for each database and includes a copy button for the matching `uv add ...` install command. MacroSignage does not run package installation from the web UI; run the copied command in the deployment environment and restart the app.

MacroSignage writes the final database value to `.env` as `MACROSIGNAGE_DATABASE_URI`; restart the app for the new database to take effect.

Any SQLAlchemy URI accepted by Flask-SQLAlchemy can be saved, such as:

```text
sqlite:////absolute/path/macrosignage.sqlite3
postgresql+psycopg://user:password@localhost/macrosignage
mysql+pymysql://user:password@localhost/macrosignage
mariadb+pymysql://user:password@localhost/macrosignage
mssql+pyodbc://user:password@localhost:1433/macrosignage?driver=ODBC+Driver+18+for+SQL+Server
oracle+oracledb://user:password@localhost:1521/service_name
```

Common driver packages:

| Database | Driver package | Install command |
| --- | --- | --- |
| SQLite | built in | none |
| PostgreSQL | `psycopg` | `uv add psycopg` |
| MySQL | `pymysql` | `uv add pymysql` |
| MariaDB | `pymysql` | `uv add pymysql` |
| Microsoft SQL Server | `pyodbc` plus Microsoft ODBC driver | `uv add pyodbc` |
| Oracle | `oracledb` | `uv add oracledb` |
| Advanced SQLAlchemy URI | matching dialect driver | depends on the URI |

Do not switch database providers during an application upgrade. Upgrade first, verify the app, then change the database URI in a separate maintenance window.

## Upload Storage

`MACROSIGNAGE_MEDIA_UPLOAD_FOLDER` stores uploaded image, video, slider, and logo files. This directory must exist or be creatable by the app process and must be included in backups with the database.

`MACROSIGNAGE_MAX_UPLOAD_BYTES` sets Flask's maximum request size. If uploads fail behind a reverse proxy, check both MacroSignage and proxy upload limits.

Supported upload extensions are documented in [Media Library](media.md).

## Schedule Timezone

Set `MACROSIGNAGE_TIMEZONE` to an IANA timezone name before creating production schedules:

```text
MACROSIGNAGE_TIMEZONE=America/Chicago
```

Schedule start/end inputs are interpreted in this timezone, stored in UTC, and displayed back in the configured local timezone. See [Scheduling and Playback](scheduling.md) for examples.

## Security Settings

`MACROSIGNAGE_SECRET_KEY` signs browser sessions. Changing it signs out existing browser sessions. Set it once during deployment and rotate only as a planned security action.

`MACROSIGNAGE_SESSION_COOKIE_SECURE=true` makes browsers send the session cookie only over HTTPS. Enable it after HTTPS is working through the reverse proxy.

`MACROSIGNAGE_ENABLE_HSTS=true` sends Strict Transport Security headers. Enable HSTS only after the production domain is permanently available over HTTPS.

See [Deployment](deployment.md) for production startup, reverse proxy, backup, and rollback guidance.
