from __future__ import annotations

import argparse
import html
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlsplit


APP_NAME = "MacroSignage"
CONFIG_FILE_NAME = "client.json"


def config_dir() -> Path:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME


def config_path() -> Path:
    return config_dir() / CONFIG_FILE_NAME


def normalize_server_url(value: str) -> str:
    server_url = value.strip()
    if not server_url:
        return ""
    if "://" not in server_url:
        server_url = f"http://{server_url}"
    parsed = urlsplit(server_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return server_url.rstrip("/")


def load_config(path: Path | None = None) -> dict[str, str | bool]:
    path = path or config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}

    server_url = normalize_server_url(str(data.get("server_url", "")))
    display_token = str(data.get("display_token", "")).strip()
    return {
        "server_url": server_url,
        "display_token": display_token,
        "auto_pair": bool(data.get("auto_pair") and server_url and display_token),
    }


def save_config(data: dict[str, object], path: Path | None = None) -> dict[str, str | bool]:
    path = path or config_path()
    server_url = normalize_server_url(str(data.get("server_url", "")))
    display_token = str(data.get("display_token", "")).strip()
    auto_pair = bool(data.get("auto_pair") and server_url and display_token)
    config = {
        "server_url": server_url,
        "display_token": display_token if auto_pair else "",
        "auto_pair": auto_pair,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    if os.name != "nt":
        path.chmod(0o600)
    return config


def clear_config(path: Path | None = None) -> None:
    path = path or config_path()
    try:
        path.unlink()
    except FileNotFoundError:
        pass


class ClientApi:
    def get_config(self) -> dict[str, str | bool]:
        return load_config()

    def save_config(self, data: dict[str, object]) -> dict[str, str | bool]:
        return save_config(data)

    def clear_config(self) -> bool:
        clear_config()
        return True


def setup_html(*, force_setup: bool = False) -> str:
    config = load_config()
    server_url = html.escape(str(config.get("server_url", "")), quote=True)
    display_token = "" if force_setup else html.escape(str(config.get("display_token", "")), quote=True)
    auto_pair = "true" if config.get("auto_pair") and not force_setup else "false"
    auto_register = "true" if config.get("server_url") and not config.get("auto_pair") and not force_setup else "false"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MacroSignage Client Setup</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #0f172a;
      --panel: #111827;
      --border: #334155;
      --text: #f8fafc;
      --muted: #cbd5e1;
      --primary: #60a5fa;
      --primary-strong: #2563eb;
      --danger: #f87171;
      --success: #34d399;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: var(--bg);
    }}
    main {{
      width: min(100% - 2rem, 34rem);
      padding: 1.5rem;
      border: 1px solid var(--border);
      border-radius: 0.5rem;
      background: var(--panel);
    }}
    h1 {{
      margin: 0 0 0.5rem;
      font-size: 1.5rem;
      line-height: 1.2;
    }}
    p {{ color: var(--muted); }}
    form {{
      display: grid;
      gap: 1rem;
      margin-top: 1.25rem;
    }}
    label {{
      display: grid;
      gap: 0.375rem;
      font-weight: 700;
    }}
    input[type="text"],
    input[type="password"] {{
      width: 100%;
      min-height: 2.75rem;
      padding: 0.625rem 0.75rem;
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 0.375rem;
      background: #020617;
    }}
    .check-row {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: 500;
      color: var(--muted);
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
    }}
    .token-panel {{
      display: grid;
      gap: 0.75rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border);
    }}
    button {{
      min-height: 2.5rem;
      padding: 0.5rem 0.875rem;
      font-weight: 700;
      border: 1px solid transparent;
      border-radius: 0.375rem;
      cursor: pointer;
    }}
    .primary {{
      color: white;
      background: var(--primary-strong);
    }}
    .success {{
      color: #052e1d;
      background: var(--success);
    }}
    .secondary {{
      color: var(--text);
      border-color: var(--border);
      background: transparent;
    }}
    .status {{
      min-height: 1.5rem;
      color: var(--muted);
    }}
    .error {{ color: var(--danger); }}
  </style>
</head>
<body>
  <main>
    <h1>MacroSignage Client</h1>
    <p>Enter the MacroSignage server URL. The client will show a QR code an admin can scan to add and pair this display.</p>
    <form id="setup-form">
      <label>
        Server or host
        <input id="server-url" name="server_url" type="text" value="{server_url}" placeholder="http://signage.local:5000" required>
      </label>
      <label class="check-row">
        <input id="remember-setup" type="checkbox" checked>
        Remember server on this device
      </label>
      <div class="actions">
        <button class="success" type="submit">Show QR setup</button>
        <button class="secondary" id="clear-setup" type="button">Clear saved setup</button>
      </div>
      <div class="token-panel">
        <label>
          Display token
          <input id="display-token" name="token" type="password" value="{display_token}" autocomplete="off" placeholder="Optional fallback token">
        </label>
        <div class="actions">
          <button class="primary" id="token-pair" type="button">Pair with token</button>
        </div>
      </div>
      <div class="status" id="status" role="status"></div>
    </form>
  </main>
  <script>
    const autoPair = {auto_pair};
    const autoRegister = {auto_register};
    const form = document.getElementById("setup-form");
    const serverInput = document.getElementById("server-url");
    const tokenInput = document.getElementById("display-token");
    const rememberInput = document.getElementById("remember-setup");
    const clearButton = document.getElementById("clear-setup");
    const tokenPairButton = document.getElementById("token-pair");
    const statusBox = document.getElementById("status");

    function normalizeServer(value) {{
      let server = value.trim();
      if (!server) return "";
      if (!server.includes("://")) server = `http://${{server}}`;
      try {{
        const url = new URL(server);
        if (url.protocol !== "http:" && url.protocol !== "https:") return "";
        return url.toString().replace(/\\/$/, "");
      }} catch {{
        return "";
      }}
    }}

    async function openQrSetup() {{
      const server = normalizeServer(serverInput.value);
      if (!server) {{
        statusBox.textContent = "Enter a valid server URL.";
        statusBox.classList.add("error");
        return;
      }}

      statusBox.classList.remove("error");
      statusBox.textContent = "Opening QR setup...";
      if (window.pywebview?.api) {{
        if (rememberInput.checked) {{
          await window.pywebview.api.save_config({{
            server_url: server,
            display_token: "",
            auto_pair: false,
          }});
        }} else {{
          await window.pywebview.api.clear_config();
        }}
      }}
      window.location.assign(`${{server}}/displays/register`);
    }}

    async function pairDisplay() {{
      const server = normalizeServer(serverInput.value);
      const token = tokenInput.value.trim();
      if (!server || !token) {{
        statusBox.textContent = "Enter a valid server URL and display token.";
        statusBox.classList.add("error");
        return;
      }}

      statusBox.classList.remove("error");
      statusBox.textContent = "Pairing display...";
      if (window.pywebview?.api) {{
        if (rememberInput.checked) {{
          await window.pywebview.api.save_config({{
            server_url: server,
            display_token: token,
            auto_pair: true,
          }});
        }} else {{
          await window.pywebview.api.clear_config();
        }}
      }}

      const postForm = document.createElement("form");
      postForm.method = "post";
      postForm.action = `${{server}}/displays/pair`;
      const tokenField = document.createElement("input");
      tokenField.type = "hidden";
      tokenField.name = "token";
      tokenField.value = token;
      postForm.appendChild(tokenField);
      document.body.appendChild(postForm);
      postForm.submit();
    }}

    form.addEventListener("submit", (event) => {{
      event.preventDefault();
      openQrSetup();
    }});

    tokenPairButton.addEventListener("click", () => {{
      pairDisplay();
    }});

    clearButton.addEventListener("click", async () => {{
      if (window.pywebview?.api) await window.pywebview.api.clear_config();
      serverInput.value = "";
      tokenInput.value = "";
      statusBox.classList.remove("error");
      statusBox.textContent = "Saved setup cleared.";
    }});

    if (autoPair && serverInput.value && tokenInput.value) {{
      statusBox.textContent = "Using saved setup. Pairing display...";
      window.setTimeout(pairDisplay, 700);
    }} else if (autoRegister && serverInput.value) {{
      statusBox.textContent = "Using saved server. Opening QR setup...";
      window.setTimeout(openQrSetup, 700);
    }}
  </script>
</body>
</html>"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the standalone MacroSignage display client.")
    parser.add_argument("--setup", action="store_true", help="Show setup even when saved settings exist.")
    parser.add_argument("--reset", action="store_true", help="Clear saved setup before starting.")
    parser.add_argument("--windowed", action="store_true", help="Open in a normal window instead of fullscreen.")
    parser.add_argument("--debug", action="store_true", help="Enable pywebview debug mode.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.reset:
        clear_config()

    try:
        import webview
    except ImportError:
        parser.error("pywebview is not installed. Run `uv sync` from the client directory.")

    webview.create_window(
        "MacroSignage Client",
        html=setup_html(force_setup=args.setup),
        js_api=ClientApi(),
        width=1280,
        height=720,
        fullscreen=not args.windowed,
    )
    webview.start(debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
