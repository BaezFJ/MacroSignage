# Realtime and Player Behavior

Display players use server-sent events to detect content updates.

Pairing and token management are documented in [Display Management and Player Pairing](displays.md). Schedule selection is documented in [Scheduling and Playback](scheduling.md).

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

## Browser Player States

The browser player page is:

```text
/displays/<display_id>/play
```

The player can render one of these states:

- Access required: the browser or client has not paired with a valid display token.
- Offline: the display status is `Offline`.
- Maintenance: the display status is `Maintenance`.
- No active schedules: the display is online but no assigned schedule is currently playable.
- Playlist: the display is online and has playable scheduled media.

## Update Timing

Admin changes to displays, media, schedules, logo settings, fonts, and player access increment the content version. Paired browser players receive the `content.updated` server-sent event and reload the player page.

Schedules also provide a next refresh boundary for future active starts and ends. This lets an already-open player refresh when an active schedule becomes playable or stops being playable.
