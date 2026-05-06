# Realtime and Player Behavior

Display players use server-sent events to detect content updates.

The browser player connects to:

```text
/displays/<display_id>/events
```

When content changes, MacroSignage increments the content version. The player receives a `content.updated` event and reloads the playback page so schedules, media, logo settings, and status changes are reflected.

The JSON player endpoints expose the current status and playlist:

```text
/api/v1/player/displays/<display_id>/status
/api/v1/player/displays/<display_id>/playlist
```

Player API requests can use `X-Display-Token` for one-time token validation or `X-Display-Access-Key` for already paired clients.
