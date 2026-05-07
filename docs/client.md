# Standalone Client

MacroSignage includes a separate pywebview display client in `client/`. It is not part of the main Flask package; it has its own `client/pyproject.toml`, lockfile, dependencies, and release executables.

Use the standalone client when a display device should boot into a packaged player instead of a manually opened browser.

Prebuilt client executables are published on the GitHub Releases page for easier setup:

```text
https://github.com/BaezFJ/MacroSignage/releases
```

Download the executable for the display device's operating system when you do not want to install the client from source.

## Quick Start

```bash
cd client
uv sync
uv run macrosignage-client --setup --windowed
```

The setup screen asks for:

- Server or host: the MacroSignage base URL, such as `https://signage.example.invalid` or `signage.local:5000`.
- Remember server on this device: saves the server URL so the client can reopen QR setup automatically.
- Display token: an optional fallback token generated from the admin display detail page.

If the host has no scheme, the client assumes `http://`.

The normal setup path is QR registration. After the server URL is entered, the client opens `/displays/register` in the webview. An authenticated admin scans the QR code from their phone, submits the display details form, and the client opens the paired display player.

For browser-only devices, open `/displays/register` directly on the display device.

## CLI Flags

```bash
uv run macrosignage-client --help
```

Supported flags:

- `--setup`: show setup even when saved settings exist.
- `--reset`: clear saved setup before starting.
- `--windowed`: open in a normal window instead of fullscreen.
- `--debug`: enable pywebview debug mode.

## Saved Configuration

The client saves configuration as `client.json` under the platform config directory:

- Windows: `%APPDATA%\MacroSignage\client.json`
- macOS: `~/Library/Application Support/MacroSignage/client.json`
- Linux: `${XDG_CONFIG_HOME}/MacroSignage/client.json`, or `~/.config/MacroSignage/client.json`

On non-Windows systems, the file is written with `0600` permissions.

The display token is saved only when token auto-pairing is enabled. Use `--reset` or the setup screen's clear action before reassigning a device.

## Pairing Flow

The client posts the display token to:

```text
POST /displays/pair
```

The server finds the matching display, stores a paired display access key in the client webview session, and redirects to the browser player.

If the display token is disabled or rotated from the admin display page, existing clients lose access and must be paired again.

See [Display Management and Player Pairing](displays.md) and [Realtime and Player Behavior](realtime-player.md).

## Linux GUI Dependencies

The client uses the pywebview Qt backend by default. On Ubuntu, reinstall the client environment if it was synced before Qt support was added:

```bash
cd client
uv sync --reinstall
uv run macrosignage-client --setup --windowed
```

Minimal Ubuntu systems may also need platform libraries:

```bash
sudo apt update
sudo apt install libegl1 libgl1 libxcb-cursor0 libxkbcommon-x11-0
```

GTK is supported by pywebview, but GTK Python bindings installed through apt often do not load inside uv's managed Python environment. Use Qt unless you intentionally build against system Python.

## Release Executables

Download packaged client builds from:

```text
https://github.com/BaezFJ/MacroSignage/releases
```

The `Build Client` GitHub Actions workflow builds Windows, macOS, and Linux artifacts for manual workflow runs and version tags.

The `Release Client` workflow runs on `v*` tags and attaches the platform executables to the matching GitHub Release.

See the full [client README](../client/README.md) for local packaging commands.
