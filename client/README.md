# MacroSignage Client

Standalone pywebview client for display players.

The client is intentionally separate from the main Flask package so it can be
packaged into a small desktop executable for display setup.

Prebuilt client executables are available from the GitHub Releases page:

```text
https://github.com/BaezFJ/MacroSignage/releases
```

Download the build for the display device's operating system when you want the
easiest setup path.

## Run locally

```bash
cd client
uv sync
uv run macrosignage-client --setup --windowed
```

Enter the MacroSignage server URL and choose "Show QR setup". The client opens
the server registration page with a QR code. An authenticated admin scans the
QR code, submits the display details form from their phone, and the client
opens the paired display player in the webview.

Display token pairing is still available as a fallback from the setup screen.
The display token is shown once in the admin UI. If it is lost, rotate the
display player token and run setup again. If a display token is disabled from
the server, existing clients lose access and must be paired again after access
is restored.

Use `--help` to see every supported option:

```bash
uv run macrosignage-client --help
```

The client accepts a full server URL, such as `https://signage.example.invalid`,
or a host such as `signage.local:5000`. Hosts without a scheme are treated as
`http://`.

## Saved setup

When "Remember server on this device" is enabled, the client saves
`client.json` in the platform config directory:

- Windows: `%APPDATA%\MacroSignage\client.json`
- macOS: `~/Library/Application Support/MacroSignage/client.json`
- Linux: `${XDG_CONFIG_HOME}/MacroSignage/client.json`, or `~/.config/MacroSignage/client.json`

On non-Windows systems the config file is written with `0600` permissions. The
display token is saved only when token auto-pairing is enabled.

## Ubuntu

The client uses the pywebview Qt backend by default. If you previously synced
the client before Qt support was added, run:

```bash
cd client
uv sync --reinstall
uv run macrosignage-client --setup --windowed
```

On a minimal Ubuntu install, Qt may still need platform libraries from apt:

```bash
sudo apt update
sudo apt install libegl1 libgl1 libxcb-cursor0 libxkbcommon-x11-0
```

GTK is also supported by pywebview, but GTK Python bindings installed through
apt usually do not load inside uv's managed Python environment. Use Qt for the
standalone client unless you are intentionally building against the system
Python runtime.

## Package

```bash
cd client
uv sync --extra build
uv run pyinstaller --onefile --windowed --name MacroSignageClient macrosignage_client/app.py
```

Platform webview runtimes still need to be available on the target system.
Linux builds usually require GTK/WebKitGTK packages from the OS.

## GitHub Actions builds

The repository includes a `Build Client` workflow that compiles the client on
Windows, macOS, and Linux. Run it manually from the GitHub Actions tab, or push
a version tag such as `v0.2.1`. The workflow uploads each platform build as a
downloadable artifact.

The `Release Client` workflow runs when a `v*` tag is pushed. It builds the
same platform executables and attaches them to the matching GitHub Release.
Users can download those executables from
`https://github.com/BaezFJ/MacroSignage/releases`.

## Setup controls

- `--help`: show CLI usage.
- `--setup`: always show the setup form instead of opening saved QR registration or token pairing.
- `--reset`: clear saved setup before opening.
- `--windowed`: run in a normal window instead of fullscreen.
- `--debug`: print client diagnostic details while running.

See the main docs for [standalone client setup](../docs/client.md), [display pairing](../docs/displays.md), and [player behavior](../docs/realtime-player.md).
