# Display Management and Player Pairing

Displays represent the screens that play scheduled media. Admins and editors manage display records from `/admin/displays/`.

## Display Records

Create a display before pairing a browser player or standalone client, or use QR registration to create and pair the display in one step. A display includes:

- Name: human-readable label for the screen or location.
- Status: `Online`, `Offline`, or `Maintenance`.
- Orientation: landscape or portrait.
- Resolution width and height: used by operators to track the intended player size.

New displays start offline by default. Set a display online only when it should evaluate schedules and show media.

## QR Registration

Open this URL on a new display device:

```text
/displays/register
```

The page shows a one-time QR code. An authenticated admin scans the QR code, completes the display details form, and submits it. MacroSignage creates the display, generates player access, and the waiting display browser opens its player automatically.

QR registrations expire after 20 minutes. Refresh the registration page to create a new QR code.

Admins can scan from the Display Management page with **Scan QR code**. The in-browser scanner uses the phone camera and requires a supported mobile browser over HTTPS, except for localhost. If browser scanning is unavailable, use the phone's camera app to open the QR code URL.

## Status Behavior

| Status | Player behavior |
| --- | --- |
| `Online` | The player evaluates active schedules assigned to the display. If none are playable, it shows "No active schedules for display". |
| `Offline` | The player shows the offline page instead of media. |
| `Maintenance` | The player shows the maintenance page instead of media. |

Status changes trigger a player content update, so paired players reload and show the new state.

## Player Tokens

Display player access is separate from admin login and API bearer tokens. Each display can have one player token used to pair a browser or client.

Admins can manage player tokens from the display detail page:

- Generate or rotate token: creates a new plaintext token and shows it once.
- Enable token: allows pairing and player access when a token already exists.
- Disable token: blocks pairing and invalidates current paired sessions by changing the display access key.

MacroSignage stores only a hash of the player token. Copy the generated token when it is shown. If it is lost, rotate the token and pair the player again.

## Browser Player Pairing

A display player runs at:

```text
/displays/<display_id>/play
```

When the browser is not paired, the page shows a token form. Submit the display token to:

```text
POST /displays/<display_id>/pair
```

Successful pairing stores a display access key in the browser session and redirects back to the player page.

MacroSignage also supports token-only pairing:

```text
POST /displays/pair
```

This is useful when a setup tool only has the token and does not know the display ID. If the token is valid and enabled, MacroSignage finds the matching display and redirects to its player page.

Do not place the token in the `/play` URL query string. Player tokens are accepted through pairing posts and player API headers, not as permanent URLs.

## Standalone Client

The standalone pywebview client lives in `client/` and is packaged separately from the Flask app. It asks for the server URL and display token, pairs with the server, and opens the browser player in a desktop webview.

See [Realtime and Player Behavior](realtime-player.md) for the player update model and [the client README](../client/README.md) for setup, reset, Linux GUI dependency notes, and release executables.

## Disabling Access

Disable a display token when a player is retired, a token may have been exposed, or you need to stop a remote client immediately. Disabling blocks new pairing and changes the access key used by existing paired sessions.

To restore access, enable an existing token or rotate to create a new token, then pair the player again.
