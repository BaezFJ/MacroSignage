# Scheduling and Playback

Schedules decide which media plays on which displays. Admins and editors manage schedules from `/admin/schedules/`.

## Schedule Records

A schedule includes:

- Name and optional notes.
- Status: `Draft`, `Active`, or `Paused`.
- Optional start time.
- Optional end time.
- Optional weekdays.
- Default media duration in seconds.
- Assigned displays.
- Assigned media.

Displays require an active playable schedule before they show media. An online display with no playable schedules shows "No active schedules for display".

## Status Behavior

| Status | Playback behavior |
| --- | --- |
| `Draft` | Saved for editing, never playable. |
| `Active` | Eligible for playback when time and weekday rules match. |
| `Paused` | Kept in the admin UI, never playable until set active again. |

## When a Schedule Is Playable

A schedule is playable for a display only when all of these are true:

- The schedule is assigned to the display.
- The schedule status is `Active`.
- The start time is empty or has passed.
- The end time is empty or is still in the future.
- No weekdays are selected, or today's local weekday is selected.
- The schedule has media assigned.

Start time is inclusive. End time is exclusive. A schedule ending at `17:00` stops being playable at exactly `17:00`.

## Timezone Handling

MacroSignage evaluates schedule times in the configured local timezone. Set it with:

```text
MACROSIGNAGE_TIMEZONE=America/Chicago
```

Use an IANA timezone name such as `America/Chicago`, `America/New_York`, or `UTC`. If the variable is not set, MacroSignage uses the server's local timezone. If an invalid timezone is configured, schedule evaluation falls back to UTC.

Example: with `MACROSIGNAGE_TIMEZONE=America/Chicago`, an active schedule that starts on `2026-01-05 08:00`, ends on `2026-01-05 17:00`, and has Monday selected plays on Monday, January 5, 2026 from 8:00 AM through 4:59 PM Central time. At 5:00 PM Central time, it is no longer playable.

## Weekday Rules

Weekdays are evaluated against the configured local timezone, not UTC. If no weekdays are selected, the schedule can play on any day while its date/time window is valid.

Use weekdays for repeating weekly windows, such as business hours on Monday through Friday. Use start and end times to bound a campaign to exact dates.

## Media Order and Duration

The player builds a display playlist from all playable schedules assigned to that display. Media is added once even if multiple playable schedules reference the same media record.

The schedule default duration controls regular image, text, neon sign, HTML, YouTube, and video slide timing in the player. Slider media uses each slide's own duration.

If multiple playable schedules are assigned to a display, MacroSignage uses the default duration from the schedules as it builds the playlist in start-time order.

## Player Refresh

Schedule changes increment the content version. Paired players listen for server-sent events and reload when content changes.

The player also tracks the next future active schedule boundary. When an active schedule is about to start or end, the player reloads around that boundary so playback can change without a manual refresh.

See [Realtime and Player Behavior](realtime-player.md) for player endpoints and update behavior.
