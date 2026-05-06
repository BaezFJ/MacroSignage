# Configuration

MacroSignage loads environment variables from `.env` before the Flask app is configured.

## Environment variables

- `MACROSIGNAGE_SECRET_KEY`: Flask secret key. Set this in every non-development environment.
- `MACROSIGNAGE_DATABASE_URI`: Flask-SQLAlchemy database URI. Defaults to SQLite in the instance directory.
- `MACROSIGNAGE_MEDIA_UPLOAD_FOLDER`: directory for uploaded media assets.
- `MACROSIGNAGE_MAX_UPLOAD_BYTES`: maximum upload size in bytes. Defaults to 100 MB.
- `MACROSIGNAGE_SESSION_COOKIE_SECURE`: set to `true`, `1`, or `yes` when serving over HTTPS.

## First run

Open `/auth/setup` to create the first admin account. After setup, users sign in at `/auth/login`.

## Database selection

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
```

Non-SQLite databases require the matching Python driver to be installed in the environment.

Common driver packages:

- PostgreSQL: `psycopg`
- MySQL or MariaDB: `pymysql`
- Microsoft SQL Server: `pyodbc` plus the Microsoft ODBC driver
- Oracle: `oracledb`
