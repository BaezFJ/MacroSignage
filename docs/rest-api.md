# REST API

The REST API is mounted at `/api/v1` and uses JSON request and response bodies. Browser admin routes and file uploads are separate from this API.

## Authentication

Most endpoints require an API bearer token:

```http
Authorization: Bearer ms_PLACEHOLDER_TOKEN
```

Tokens inherit the role of their owner. See [API Tokens](api-tokens.md) for lifecycle and storage behavior.

Player endpoints can also authenticate with display-specific headers:

```http
X-Display-Token: DISPLAY_TOKEN_SHOWN_ONCE
X-Display-Access-Key: PAIRED_DISPLAY_ACCESS_KEY
```

Use `X-Display-Token` for first validation and `X-Display-Access-Key` for already paired clients.

## Roles

| Role | API access |
| --- | --- |
| `VIEWER` | Read displays, media, schedules, fonts, settings, and health. |
| `EDITOR` | Viewer access plus create, update, and delete displays, media, and schedules. |
| `ADMIN` | Editor access plus users and font creation. |

`GET /api/v1/health` does not require authentication.

## Response Shape

Single-resource responses use:

```json
{
  "data": {
    "id": 1
  }
}
```

List responses use:

```json
{
  "data": []
}
```

Delete responses return `204 No Content` with an empty body.

Error responses use:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid display data.",
    "details": {
      "name": "Display name is required."
    }
  }
}
```

## Error Examples

### `401 UNAUTHENTICATED`

```bash
curl http://localhost:5000/api/v1/displays
```

```json
{
  "error": {
    "code": "UNAUTHENTICATED",
    "message": "Valid bearer token required."
  }
}
```

### `403 FORBIDDEN`

```bash
curl -X POST http://localhost:5000/api/v1/displays \
  -H "Authorization: Bearer ms_PLACEHOLDER_VIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Denied"}'
```

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to perform this action."
  }
}
```

### `404 NOT_FOUND`

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found."
  }
}
```

### `405 METHOD_NOT_ALLOWED`

```json
{
  "error": {
    "code": "METHOD_NOT_ALLOWED",
    "message": "The method is not allowed for the requested URL."
  }
}
```

### `422 VALIDATION_ERROR`

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid schedule data.",
    "details": {
      "status": "Choose a valid schedule status."
    }
  }
}
```

### `500 INTERNAL_SERVER_ERROR`

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An internal server error occurred."
  }
}
```

The `500` response intentionally does not expose exception details.

## Field Schemas

### Display

```json
{
  "id": 1,
  "name": "Lobby",
  "location": "Main entrance",
  "status": "ONLINE",
  "orientation": "LANDSCAPE",
  "resolutionWidth": 1920,
  "resolutionHeight": 1080,
  "notes": null,
  "mediaIds": [],
  "scheduleIds": [],
  "createdAt": "2026-01-01T14:00:00+00:00",
  "updatedAt": "2026-01-01T14:00:00+00:00"
}
```

Valid `status` values are `ONLINE`, `OFFLINE`, and `MAINTENANCE`. Valid `orientation` values are `LANDSCAPE` and `PORTRAIT`.

### Media

```json
{
  "id": 1,
  "title": "Welcome",
  "mediaType": "TEXT",
  "fileUrl": null,
  "originalFilename": null,
  "mimeType": null,
  "body": "Hello",
  "sourceUrl": null,
  "neonTextColor": null,
  "neonFrameColor": null,
  "neonBackgroundColor": null,
  "vcardName": null,
  "vcardPhone": null,
  "vcardEmail": null,
  "vcardAddress": null,
  "vcardUrl": null,
  "vcardTopText": null,
  "vcardBottomText": null,
  "notes": null,
  "displayIds": [1],
  "scheduleIds": [],
  "sliderSlides": [],
  "createdAt": "2026-01-01T14:00:00+00:00",
  "updatedAt": "2026-01-01T14:00:00+00:00"
}
```

Valid `mediaType` values are `IMAGE`, `TEXT`, `VIDEO`, `HTML`, `YOUTUBE`, `SLIDER`, `NEON_SIGN`, and `VCARD`. The JSON API can create text, HTML, YouTube, neon sign, and vCard records. Image, video, and slider file uploads are managed through the admin UI.

Slider media responses include `sliderSlides` with:

```json
{
  "id": 1,
  "sortOrder": 0,
  "backgroundUrl": "/displays/uploads/background.png",
  "foregroundUrl": "/displays/uploads/foreground.png",
  "foregroundSize": 50,
  "foregroundPosition": "CENTER",
  "foregroundAnimation": "NONE",
  "text": "Welcome",
  "textPosition": "CENTER",
  "textFontFamily": "Inter",
  "textFontSize": 72,
  "textAnimation": "NONE",
  "durationSeconds": 10
}
```

### Schedule

```json
{
  "id": 1,
  "name": "Business Hours",
  "status": "ACTIVE",
  "startsAt": "2026-01-05T14:00:00+00:00",
  "endsAt": "2026-01-05T23:00:00+00:00",
  "weekdays": ["MON", "TUE", "WED", "THU", "FRI"],
  "defaultDurationSeconds": 30,
  "notes": null,
  "displayIds": [1],
  "mediaIds": [1],
  "createdAt": "2026-01-01T14:00:00+00:00",
  "updatedAt": "2026-01-01T14:00:00+00:00"
}
```

Valid `status` values are `DRAFT`, `ACTIVE`, and `PAUSED`. Valid weekday values are `MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`, and `SUN`.

### User

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.invalid",
  "role": "ADMIN",
  "active": true,
  "createdAt": "2026-01-01T14:00:00+00:00",
  "updatedAt": "2026-01-01T14:00:00+00:00"
}
```

Valid `role` values are `ADMIN`, `EDITOR`, and `VIEWER`.

### Font

```json
{
  "id": 1,
  "family": "Inter",
  "displayName": "Inter",
  "provider": "GOOGLE",
  "active": true,
  "createdAt": "2026-01-01T14:00:00+00:00",
  "updatedAt": "2026-01-01T14:00:00+00:00"
}
```

### Settings

```json
{
  "logoEnabled": true,
  "logoPosition": "TOP_RIGHT",
  "logoUrl": "/displays/uploads/logo.png",
  "logoOriginalFilename": "logo.png"
}
```

## Health

### `GET /api/v1/health`

Auth: none. Role: none.

Returns operational readiness data. Status is `200` when ready and `503` when not ready.

```bash
curl http://localhost:5000/api/v1/health
```

## Displays

### `GET /api/v1/displays`

Auth: bearer token. Role: `VIEWER`.

Returns `{"data": [Display]}`.

```bash
curl http://localhost:5000/api/v1/displays \
  -H "Authorization: Bearer ms_PLACEHOLDER_VIEWER_TOKEN"
```

### `POST /api/v1/displays`

Auth: bearer token. Role: `EDITOR`.

Request:

```json
{
  "name": "Lobby",
  "location": "Main entrance",
  "status": "ONLINE",
  "orientation": "LANDSCAPE",
  "resolutionWidth": 1920,
  "resolutionHeight": 1080,
  "notes": "Faces the front desk"
}
```

Response: `201 {"data": Display}`.

### `GET /api/v1/displays/<id>`

Auth: bearer token. Role: `VIEWER`.

Response: `200 {"data": Display}`.

### `PATCH /api/v1/displays/<id>`

Auth: bearer token. Role: `EDITOR`.

Request is partial. Only provided fields change.

```json
{
  "name": "Lobby Screen",
  "status": "MAINTENANCE"
}
```

Response: `200 {"data": Display}`.

### `DELETE /api/v1/displays/<id>`

Auth: bearer token. Role: `EDITOR`.

Response: `204 No Content`.

## Media

### `GET /api/v1/media`

Auth: bearer token. Role: `VIEWER`.

Returns `{"data": [Media]}`.

### `POST /api/v1/media`

Auth: bearer token. Role: `EDITOR`.

Text request:

```json
{
  "title": "Welcome",
  "mediaType": "TEXT",
  "body": "Hello",
  "displayIds": [1],
  "notes": "API-created text"
}
```

YouTube request:

```json
{
  "title": "Intro Video",
  "mediaType": "YOUTUBE",
  "sourceUrl": "https://youtu.be/VIDEO_ID"
}
```

Neon sign request:

```json
{
  "title": "Open Sign",
  "mediaType": "NEON_SIGN",
  "body": "Open",
  "neonTextColor": "#ff33cc",
  "neonFrameColor": "#33ff77",
  "neonBackgroundColor": "#201514"
}
```

vCard request:

```json
{
  "title": "Sales Contact",
  "mediaType": "VCARD",
  "vcardName": "Javier Baez",
  "vcardPhone": "+1 555 0100",
  "vcardEmail": "sales@example.com",
  "vcardAddress": "123 Main Street, Chicago, IL",
  "vcardUrl": "https://example.com",
  "vcardTopText": "Scan to save our contact",
  "vcardBottomText": "We will follow up today"
}
```

Response: `201 {"data": Media}`.

The JSON API does not upload binary files. Use the admin media UI for image, video, and slider uploads.

### `GET /api/v1/media/<id>`

Auth: bearer token. Role: `VIEWER`.

Response: `200 {"data": Media}`.

### `PATCH /api/v1/media/<id>`

Auth: bearer token. Role: `EDITOR`.

Request is partial:

```json
{
  "title": "Welcome HTML",
  "mediaType": "HTML",
  "body": "<p>Hello</p>"
}
```

Response: `200 {"data": Media}`.

### `DELETE /api/v1/media/<id>`

Auth: bearer token. Role: `EDITOR`.

Response: `204 No Content`.

## Schedules

### `GET /api/v1/schedules`

Auth: bearer token. Role: `VIEWER`.

Returns `{"data": [Schedule]}`.

### `POST /api/v1/schedules`

Auth: bearer token. Role: `EDITOR`.

Request:

```json
{
  "name": "Business Hours",
  "status": "ACTIVE",
  "startsAt": "2026-01-05T08:00:00",
  "endsAt": "2026-01-05T17:00:00",
  "weekdays": ["MON", "TUE", "WED", "THU", "FRI"],
  "defaultDurationSeconds": 30,
  "displayIds": [1],
  "mediaIds": [1],
  "notes": "Weekday playback"
}
```

Response: `201 {"data": Schedule}`.

`startsAt` and `endsAt` are ISO 8601 strings interpreted in the configured `MACROSIGNAGE_TIMEZONE` and stored in UTC.

### `GET /api/v1/schedules/<id>`

Auth: bearer token. Role: `VIEWER`.

Response: `200 {"data": Schedule}`.

### `PATCH /api/v1/schedules/<id>`

Auth: bearer token. Role: `EDITOR`.

Request is partial:

```json
{
  "status": "PAUSED"
}
```

Response: `200 {"data": Schedule}`.

### `DELETE /api/v1/schedules/<id>`

Auth: bearer token. Role: `EDITOR`.

Response: `204 No Content`.

## Users

### `GET /api/v1/users`

Auth: bearer token. Role: `ADMIN`.

Returns `{"data": [User]}`.

### `POST /api/v1/users`

Auth: bearer token. Role: `ADMIN`.

Request:

```json
{
  "username": "operator",
  "email": "operator@example.invalid",
  "password": "replace-with-a-long-password",
  "role": "EDITOR",
  "active": true
}
```

Response: `201 {"data": User}`.

### `GET /api/v1/users/<id>`

Auth: bearer token. Role: `ADMIN`.

Response: `200 {"data": User}`.

User update and delete actions are currently available through `/admin/users/`, not the JSON API.

## Fonts

### `GET /api/v1/fonts`

Auth: bearer token. Role: `VIEWER`.

Returns `{"data": [Font]}`.

### `POST /api/v1/fonts`

Auth: bearer token. Role: `ADMIN`.

Request:

```json
{
  "family": "Roboto Condensed",
  "displayName": "Roboto Condensed",
  "active": true
}
```

Response: `201 {"data": Font}`.

Duplicate font families return `409 CONFLICT`.

Font update and delete actions are currently available through `/admin/settings/fonts/`, not the JSON API.

## Settings

### `GET /api/v1/settings`

Auth: bearer token. Role: `VIEWER`.

Response: `200 {"data": Settings}`.

Settings changes are currently managed through admin settings pages, not the JSON API.

## Player Endpoints

Player endpoints are intended for display clients. They accept a display token or paired display access key instead of a bearer API token.

### `GET /api/v1/player/displays/<id>/status`

Auth: `X-Display-Token` or `X-Display-Access-Key`. Role: display player access.

Response:

```json
{
  "data": {
    "display": {
      "id": 1,
      "name": "Lobby"
    },
    "contentVersion": 2
  }
}
```

### `GET /api/v1/player/displays/<id>/playlist`

Auth: `X-Display-Token` or `X-Display-Access-Key`. Role: display player access.

Response:

```json
{
  "data": {
    "display": {
      "id": 1,
      "name": "Lobby"
    },
    "status": "ONLINE",
    "defaultDurationSeconds": 30,
    "contentVersion": 2,
    "logo": {
      "logoEnabled": false,
      "logoPosition": "TOP_RIGHT",
      "logoUrl": null,
      "logoOriginalFilename": null
    },
    "media": []
  }
}
```

When the display status is not `ONLINE`, `media` is empty.
