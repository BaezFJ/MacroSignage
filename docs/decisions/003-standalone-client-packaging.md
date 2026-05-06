# ADR-003: Separate Standalone Client Package

## Status

Accepted

## Date

2026-05-06

## Context

MacroSignage needs a simple display-device client that opens the paired browser player in a desktop webview. pywebview and GUI/runtime packaging requirements are different from the Flask server package requirements.

The server package should remain installable on headless Linux hosts without Qt, GTK, or PyInstaller dependencies.

## Decision

Keep the pywebview client in `client/` as a separate package with its own `pyproject.toml`, `uv.lock`, CLI entry point, and GitHub Actions executable workflows.

The main server package remains under `src/macrosignage`. GitHub Actions build Windows, macOS, and Linux client executables and attach release assets to GitHub Releases.

## Alternatives Considered

### Include the client in the main server package

- Pros: one package to install.
- Cons: pulls GUI dependencies into server installs and complicates headless deployments.
- Rejected because server and display-client runtime needs are different.

### Tell users to open a browser manually

- Pros: no client package.
- Cons: harder display setup, less appliance-like behavior, and more manual device work.
- Rejected because executable display setup is a product goal.

## Consequences

- Client docs and release workflows must stay separate from server packaging docs.
- Operators can download prebuilt client executables from GitHub Releases.
- Developers must run client checks from `client/`.
- The server package avoids GUI dependencies.
