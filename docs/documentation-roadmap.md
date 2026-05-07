# Complete Documentation Roadmap

This roadmap tracks the documentation work needed before MacroSignage can call the v1.0 documentation complete. It focuses on user-facing guides, operator runbooks, API reference quality, developer onboarding, and documentation verification.

## Goals

- Make first install, first admin setup, first display pairing, and first schedule playback easy to follow.
- Keep operator guidance aligned with the production hardening work.
- Document all supported media, schedule, auth, settings, API, and client workflows.
- Keep public docs free of stale roadmap claims and unsafe configuration examples.
- Add lightweight checks so docs stay linked and accurate as the project changes.

## Phase 1: Documentation Audit and Information Architecture

### Task 1: Audit Existing Documentation Against Current Features

**Description:** Compare current docs with the implemented app features and identify missing, stale, duplicated, or misleading content.

**Acceptance criteria:**
- [x] README current/planned feature lists match the implemented product.
- [x] Every existing guide has a clear owner topic and no major stale instructions.
- [x] Missing guide topics are listed in this roadmap or created as tasks.

**Verification:**
- [x] Run `rg -n "TODO|planned|pending|WebSocket|wsgi.py|comprehensive documentation" README.md docs --glob '!docs/documentation-roadmap.md'`.
- [x] Manually compare route/features inventory with docs index.

**Files likely touched:**
- `README.md`
- `docs/index.md`
- `docs/documentation-roadmap.md`

**Estimated scope:** Medium

### Task 2: Restructure Documentation Index for User Journeys

**Description:** Reorganize `docs/index.md` so readers can find docs by journey: new user, admin/operator, API integrator, deployment operator, and contributor.

**Acceptance criteria:**
- [x] Docs index groups guides by audience or workflow.
- [x] Every guide has a one-line purpose statement.
- [x] Roadmaps are separated from user guides.

**Verification:**
- [x] All links in `docs/index.md` resolve to existing files.
- [x] `git diff --check` passes.

**Files likely touched:**
- `docs/index.md`

**Estimated scope:** Small

### Phase 1 Audit Notes

Completed audit findings:

- README no longer lists implemented auth, API, admin, scheduling, and SSE behavior as future work.
- README no longer references a missing `wsgi.py`, missing `base.html`, WebSocket updates, or a pending build badge.
- Existing docs are grouped by reader journey in `docs/index.md`, and every linked guide has a one-line purpose statement.
- Missing user/admin guides are tracked in Tasks 3-6.
- Missing API/client integration docs are tracked in Tasks 7-9.
- Missing operator/developer/architecture quality work is tracked in Tasks 10-17.

## Phase 2: User and Admin Guides

### Task 3: Write First-Run and Admin Setup Guide

**Description:** Document the first admin account setup, sign-in/sign-out, password reset behavior, user roles, and safe recovery notes.

**Acceptance criteria:**
- [x] Guide covers `/auth/setup`, `/auth/login`, `/auth/password-reset`, and `/admin/users/`.
- [x] Role permissions are explained in terms of real admin actions.
- [x] Password reset limitations and deployment considerations are documented.

**Verification:**
- [x] Existing auth tests map to documented workflows.
- [x] No passwords or token examples look real.

**Files likely touched:**
- `docs/auth-rbac.md`
- optional `docs/admin-guide.md`

**Estimated scope:** Medium

### Task 4: Write Display Management and Player Pairing Guide

**Description:** Document display CRUD, statuses, player tokens, pairing by display URL or token-only flow, disabling access, and maintenance/offline behavior.

**Acceptance criteria:**
- [x] Guide covers display statuses: Online, Offline, Maintenance.
- [x] Guide explains token generation, reset/rotation, disable, and one-time visibility.
- [x] Guide explains player access through browser player and standalone client.

**Verification:**
- [x] Links to player routes and API token docs are correct.
- [x] No plaintext token values are reused as if they were permanent.

**Files likely touched:**
- `docs/displays.md`
- `docs/realtime-player.md`
- `client/README.md`

**Estimated scope:** Medium

### Task 5: Write Media Library Guide

**Description:** Document media CRUD, supported media types, upload rules, slider media, YouTube URLs, HTML content behavior, logo overlay, and Google font management.

**Acceptance criteria:**
- [x] Supported media types are documented: image, text, neon sign, vCard, video, HTML, YouTube, slider.
- [x] Upload extensions and size limits are documented.
- [x] Slider options are documented: background, foreground, foreground size/position, text, font, animation, slide count, and duration.
- [x] Logo settings and global visibility are documented.

**Verification:**
- [x] Guide matches constants in media/admin forms.
- [x] Security notes explain HTML iframe sandboxing and external YouTube embeds.

**Files likely touched:**
- `docs/media.md`
- `docs/configuration.md`

**Estimated scope:** Large, split if needed

### Task 6: Write Scheduling and Playback Guide

**Description:** Document schedule CRUD, active/paused/draft behavior, start/end time handling, weekday rules, display/media assignments, default durations, and no-active-schedule behavior.

**Acceptance criteria:**
- [x] Guide explains when a schedule is playable.
- [x] Guide explains local timezone configuration with `MACROSIGNAGE_TIMEZONE`.
- [x] Guide explains schedule refresh/reload behavior for players.
- [x] Guide documents the default "No active schedules for display" page.

**Verification:**
- [x] Guide matches schedule selection tests.
- [x] Time examples use explicit dates and timezones.

**Files likely touched:**
- `docs/scheduling.md`
- `docs/realtime-player.md`
- `docs/configuration.md`

**Estimated scope:** Medium

### User Guide Checkpoint

- [x] First-run, auth, display pairing, media, and scheduling guides are linked from `docs/index.md`.
- [x] Phase 2 guides use placeholder tokens only and avoid real-looking secrets.
- [x] Phase 2 guides document the implemented no-active-schedules, offline, and maintenance player states.

## Phase 3: API and Integration Reference

### Task 7: Expand REST API Reference

**Description:** Replace the endpoint list with request/response examples, auth requirements, role requirements, validation errors, and stable response shapes.

**Acceptance criteria:**
- [x] Every documented endpoint includes method, path, auth requirement, role requirement, and response shape.
- [x] CRUD examples are provided for displays, media, schedules, users, fonts, settings, and player endpoints.
- [x] Error examples cover `401`, `403`, `404`, `405`, `422`, and `500`.

**Verification:**
- [x] API docs match `tests/test_api.py`.
- [x] Serializer fields match `src/macrosignage/features/api/serializers.py`.

**Files likely touched:**
- `docs/rest-api.md`
- optional `docs/api-examples/`

**Estimated scope:** Large, split by resource

### Task 8: Expand API Token Guide

**Description:** Document API token lifecycle, ownership, role inheritance, creation, reset, revoke, delete, storage model, and curl examples.

**Acceptance criteria:**
- [x] Guide explains tokens are shown once and stored hashed.
- [x] Guide explains reset invalidates the previous token.
- [x] Guide includes viewer/editor/admin examples.

**Verification:**
- [x] Guide matches token route tests.
- [x] Examples use placeholder tokens only.

**Files likely touched:**
- `docs/api-tokens.md`
- `docs/rest-api.md`

**Estimated scope:** Small

### Task 9: Document Standalone Client Setup

**Description:** Document the pywebview client from install through pairing, saved configuration, reset behavior, Linux GUI dependency notes, and GitHub release executables.

**Acceptance criteria:**
- [x] Guide covers `macrosignage-client --help`, `--setup`, `--reset`, `--windowed`, and `--debug`.
- [x] Guide explains server/host and display token input.
- [x] Guide links to GitHub release executable workflow.
- [x] Linux Qt/GTK troubleshooting is included or linked.

**Verification:**
- [x] Guide matches `client/macrosignage_client/app.py`.
- [x] Client docs do not imply the client is part of the main PyPI package.

**Files likely touched:**
- `client/README.md`
- optional `docs/client.md`
- `docs/troubleshooting.md`

**Estimated scope:** Medium

### API and Integration Checkpoint

- [x] REST API, API token, and standalone client guides are linked from `docs/index.md`.
- [x] REST examples use placeholder tokens, placeholder domains, and documented response fields.
- [x] Player API authentication is documented separately from bearer API tokens.

## Phase 4: Operator and Deployment Documentation

### Task 10: Harden Configuration Reference

**Description:** Expand configuration docs with every supported environment variable, defaults, safe production values, examples, and restart requirements.

**Acceptance criteria:**
- [x] All `MACROSIGNAGE_*` settings used in code are documented.
- [x] Database driver requirements are complete.
- [x] Secret, cookie, HSTS, upload, media, and timezone settings are covered.

**Verification:**
- [x] `rg -n "MACROSIGNAGE_" src/macrosignage docs` shows no undocumented app setting.
- [x] Docs avoid exposing real secret values.

**Files likely touched:**
- `docs/configuration.md`
- `docs/deployment.md`

**Estimated scope:** Medium

### Task 11: Expand Deployment Runbooks

**Description:** Make deployment docs operator-ready with systemd, Docker, reverse proxy, health checks, backups, restore, rollback, and upgrade examples.

**Acceptance criteria:**
- [x] systemd and Docker examples are linked and explained.
- [x] Reverse proxy notes include HTTPS and forwarded headers.
- [x] Backup, restore, upgrade, and rollback steps are easy to follow.
- [x] Health check response fields are documented.

**Verification:**
- [x] Commands match `macrosignage-prod` and current config names.
- [x] `tests/test_operational_readiness.py` passes.

**Files likely touched:**
- `docs/deployment.md`
- `docs/installation.md`
- `deploy/`

**Estimated scope:** Medium

### Task 12: Expand Troubleshooting Guide

**Description:** Add symptom-based troubleshooting for login, API auth, display pairing, offline/maintenance pages, no active schedules, media uploads, database drivers, client GUI dependencies, and health check failures.

**Acceptance criteria:**
- [x] Troubleshooting entries are organized by symptom.
- [x] Each entry includes likely causes and verification commands or UI checks.
- [x] Entries avoid telling users to expose secrets or tokens.

**Verification:**
- [x] Troubleshooting links to relevant guides.
- [x] Commands use current CLI names.

**Files likely touched:**
- `docs/troubleshooting.md`

**Estimated scope:** Medium

### Operator Documentation Checkpoint

- [x] Configuration, deployment, installation, and troubleshooting docs are linked and use current CLI names.
- [x] Health check fields, backup/restore order, reverse proxy requirements, and database driver requirements are documented.
- [x] Troubleshooting covers login, API auth, player pairing, offline/maintenance states, no active schedules, uploads, database drivers, client GUI dependencies, health checks, and upgrades.

## Phase 5: Developer and Maintainer Documentation

### Task 13: Expand Developer Guide

**Description:** Document local setup, tests, packaging, project structure, blueprints, forms/services/models pattern, static assets, frontend vendor assets, and release automation.

**Acceptance criteria:**
- [x] Developer guide explains where feature code, templates, tests, and client code live.
- [x] Test commands and packaging commands match CI.
- [x] Blueprint conventions are documented.

**Verification:**
- [x] CI workflow and docs command list stay aligned.
- [x] New contributor can locate where to add a feature.

**Files likely touched:**
- `docs/development.md`
- `README.md`

**Estimated scope:** Medium

### Task 14: Add Architecture Overview and ADRs

**Description:** Document core architecture decisions and create ADRs for key durable choices.

**Acceptance criteria:**
- [x] Architecture overview explains Flask app factory, feature blueprints, SQLAlchemy models, runtime schema patching, player tokens, SSE updates, and static vendoring.
- [x] ADRs exist for at least database/runtime schema strategy, token-secured displays, and standalone client packaging.

**Verification:**
- [x] ADRs follow a consistent template.
- [x] Architecture docs link to source modules and related guides.

**Files likely touched:**
- `docs/architecture.md`
- `docs/decisions/`

**Estimated scope:** Large, split by ADR

### Task 15: Update README for v1.0 Accuracy

**Description:** Refresh README so it is a concise landing page with accurate current features, quick start, docs links, commands, support status, and roadmap links.

**Acceptance criteria:**
- [x] README no longer lists implemented features as planned.
- [x] README links to core docs instead of duplicating long guide content.
- [x] Badges and commands reflect current CI and PyPI usage.
- [x] v1.0 roadmap links include production hardening and documentation roadmaps.

**Verification:**
- [x] README links resolve.
- [x] `rg -n "TODO|planned|pending|wsgi.py|WebSocket" README.md` has no stale content.

**Files likely touched:**
- `README.md`

**Estimated scope:** Medium

### Maintainer Documentation Checkpoint

- [x] Developer guide, architecture overview, ADRs, and README are linked from `docs/index.md`.
- [x] README is a concise landing page and points to detailed docs.
- [x] Architecture docs capture runtime schema strategy, display player auth, SSE updates, static vendoring, and client packaging.

## Phase 6: Documentation Quality Gates

### Task 16: Add Documentation Link Checks

**Description:** Add automated checks for internal Markdown links and required docs references.

**Acceptance criteria:**
- [x] Tests verify all local Markdown links point to existing files or anchors where practical.
- [x] Docs index links are covered.
- [x] README roadmap links are covered.

**Verification:**
- [x] `uv run python -m pytest tests/test_docs.py` passes.
- [x] Full test suite passes.

**Files likely touched:**
- `tests/test_docs.py`
- `docs/`
- `README.md`

**Estimated scope:** Medium

### Task 17: Add Documentation Review Checklist

**Description:** Add a checklist for release documentation review so manual browser/player checks and operator docs are confirmed before tagging.

**Acceptance criteria:**
- [x] Checklist covers README, install, admin workflows, API docs, deployment, troubleshooting, and client docs.
- [x] Checklist includes manual media playback and admin settings readability checks.
- [x] Checklist is linked from development or deployment docs.

**Verification:**
- [x] Checklist exists and is linked.
- [x] Release docs mention it.

**Files likely touched:**
- `docs/release-documentation-checklist.md`
- `docs/development.md`

**Estimated scope:** Small

## Checkpoints

### Documentation Foundation Checkpoint

- [x] Tasks 1-2 complete.
- [x] Docs index is organized by reader journey.
- [x] README points to the documentation roadmap.

### User Guide Checkpoint

- [x] Tasks 3-6 complete.
- [x] First admin, display pairing, media setup, and scheduling workflows are documented end to end.
- [x] Browser-only/manual verification gaps are listed.

### API and Integration Checkpoint

- [x] Tasks 7-9 complete.
- [x] REST API, API tokens, and standalone client docs match tests and current code.

### Operator Readiness Checkpoint

- [x] Tasks 10-12 complete.
- [x] Configuration, deployment, health checks, backups, rollback, and troubleshooting are documented.

### Maintainer Checkpoint

- [x] Tasks 13-15 complete.
- [x] Developer guide, architecture docs, ADRs, and README are accurate.

### v1.0 Documentation Complete Checkpoint

- [x] Tasks 16-17 complete.
- [x] Documentation link checks pass.
- [x] Full test suite passes.
- [x] Manual documentation review checklist is complete.
- [x] README v1.0 "Complete documentation" item can be marked complete.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Docs drift from routes and serializers | High | Add docs link/reference tests and map API docs to `tests/test_api.py`. |
| README overpromises pre-alpha features | Medium | Refresh README as a concise landing page and link detailed guides. |
| Operator docs include unsafe examples | High | Use placeholder secrets, document HTTPS cookie requirements, and avoid real token values. |
| Browser/player behavior is hard to prove in static docs | Medium | Keep manual playback checks in the release documentation checklist. |
| Docs become too large for new users | Medium | Organize docs by reader journey and keep README short. |

## Open Questions

- Should the final v1.0 docs include screenshots, or remain text-only until the UI stabilizes?
- Should REST API documentation be hand-written Markdown, generated OpenAPI, or both?
- Should Docker examples install from PyPI only, or also support local source builds for contributors?
