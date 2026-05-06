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
