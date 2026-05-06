# MacroSignage Client

Standalone pywebview client for display players.

The client is intentionally separate from the main Flask package so it can be
packaged into a small desktop executable for display setup.

## Run locally

```bash
cd client
uv sync
uv run macrosignage-client --setup --windowed
```

Enter the MacroSignage server URL and the display token generated from the
admin display detail page. The client posts the token to the server, pairs the
display, and opens the display player in the webview.

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

## Setup controls

- `--setup`: always show the setup form.
- `--reset`: clear saved setup before opening.
- `--windowed`: run in a normal window instead of fullscreen.
