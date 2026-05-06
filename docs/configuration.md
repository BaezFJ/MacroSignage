# Configuration

MacroSignage loads environment variables from `.env` before the Flask app is configured.

## Environment variables

- `MACROSIGNAGE_SECRET_KEY`: Flask secret key. Set this in every non-development environment.
- `MACROSIGNAGE_DATABASE_URI`: SQLAlchemy database URI. Defaults to SQLite in the instance directory.
- `MACROSIGNAGE_MEDIA_UPLOAD_FOLDER`: directory for uploaded media assets.
- `MACROSIGNAGE_MAX_UPLOAD_BYTES`: maximum upload size in bytes. Defaults to 100 MB.
- `MACROSIGNAGE_SESSION_COOKIE_SECURE`: set to `true`, `1`, or `yes` when serving over HTTPS.

## First run

Open `/auth/setup` to create the first admin account. After setup, users sign in at `/auth/login`.
