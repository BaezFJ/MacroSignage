# REST API

The API is mounted at `/api/v1` and uses JSON request and response bodies.

## Authentication

Send API tokens in the `Authorization` header:

```http
Authorization: Bearer ms_your_token
```

## Error shape

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid display data.",
    "details": {}
  }
}
```

## Resources

- `GET /api/v1/health`
- `GET /api/v1/displays`
- `POST /api/v1/displays`
- `GET /api/v1/displays/<id>`
- `PATCH /api/v1/displays/<id>`
- `DELETE /api/v1/displays/<id>`
- `GET /api/v1/media`
- `POST /api/v1/media`
- `GET /api/v1/media/<id>`
- `PATCH /api/v1/media/<id>`
- `DELETE /api/v1/media/<id>`
- `GET /api/v1/schedules`
- `POST /api/v1/schedules`
- `GET /api/v1/schedules/<id>`
- `PATCH /api/v1/schedules/<id>`
- `DELETE /api/v1/schedules/<id>`
- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/users/<id>`
- `GET /api/v1/fonts`
- `POST /api/v1/fonts`
- `GET /api/v1/settings`
- `GET /api/v1/player/displays/<id>/status`
- `GET /api/v1/player/displays/<id>/playlist`
