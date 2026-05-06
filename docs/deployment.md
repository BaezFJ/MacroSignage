# Deployment

## Production checklist

- Set `MACROSIGNAGE_SECRET_KEY`.
- Use a persistent `MACROSIGNAGE_DATABASE_URI`.
- Use a persistent `MACROSIGNAGE_MEDIA_UPLOAD_FOLDER`.
- Serve over HTTPS and set `MACROSIGNAGE_SESSION_COOKIE_SECURE=true`.
- Run behind a production WSGI server such as Waitress.

## Example

```bash
MACROSIGNAGE_SESSION_COOKIE_SECURE=true uv run macrosignage prod
```
