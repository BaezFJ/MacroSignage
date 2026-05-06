# Production Hardening and Test Completion Roadmap

This roadmap tracks the work required to move MacroSignage from pre-alpha toward a production-ready v1.0 release. Each task should leave the app in a releasable state and include tests or documented manual verification.

## Goals

- Make production defaults explicit and safe.
- Preserve existing user data during upgrades.
- Verify critical workflows with automated tests.
- Document deployment, rollback, backup, and operational procedures.

## Phase 1: Production Safety Baseline

### Task 1: Enforce Production Configuration Checks

**Description:** Add a startup/runtime configuration check that warns or fails clearly when production is started with unsafe defaults.

**Acceptance criteria:**
- [x] Production mode requires a non-default `MACROSIGNAGE_SECRET_KEY`.
- [x] Production mode documents `MACROSIGNAGE_SESSION_COOKIE_SECURE=true` for HTTPS deployments.
- [x] Configuration warnings are visible in CLI output or admin settings.

**Verification:**
- [x] Unit tests cover safe and unsafe production configuration.
- [x] `uv run macrosignage-prod --help` still works.

**Files likely touched:**
- `src/macrosignage/app.py`
- `src/macrosignage/cli.py`
- `tests/test_config.py`
- `docs/deployment.md`

**Estimated scope:** Medium

### Task 2: Add Security Headers

**Description:** Add conservative HTTP security headers for HTML/admin/player responses without breaking embedded player media.

**Acceptance criteria:**
- [x] Responses include `X-Content-Type-Options: nosniff`.
- [x] Responses include an appropriate `Referrer-Policy`.
- [x] Responses include frame policy or CSP rules that do not break display playback.
- [x] HTTPS deployments can enable HSTS.

**Verification:**
- [x] Tests assert headers on public, admin, auth, API, and player routes.
- [ ] Manual check: display player still renders image, video, HTML, YouTube, and slider media.

**Files likely touched:**
- `src/macrosignage/app.py`
- `tests/test_config.py`
- `tests/test_display_player.py`
- `docs/deployment.md`

**Estimated scope:** Medium

### Task 3: Normalize Error Handling

**Description:** Replace unhandled production errors with user-safe HTML and API error responses.

**Acceptance criteria:**
- [x] HTML routes show a generic error page for 500s.
- [x] API routes return JSON errors for 404/405/500.
- [x] Debug mode behavior remains developer-friendly.

**Verification:**
- [x] Tests cover HTML and API error responses.
- [x] Existing tests continue to pass.

**Files likely touched:**
- `src/macrosignage/app.py`
- `src/macrosignage/features/api/routes.py`
- `src/macrosignage/templates/`
- `tests/`

**Estimated scope:** Medium

## Phase 2: Data Safety and Upgrade Reliability

### Task 4: Formalize Database Migration Workflow

**Description:** Move runtime schema patching toward a documented migration workflow and add upgrade tests for existing databases.

**Acceptance criteria:**
- [x] Existing SQLite databases are upgraded without data loss.
- [x] New columns added by recent features are covered by upgrade tests.
- [x] Deployment docs explain backup and migration order.

**Verification:**
- [x] Tests create an older schema, start the app, and verify required columns/data remain valid.
- [x] `uv run python -m pytest tests/test_config.py` passes.

**Files likely touched:**
- `src/macrosignage/app.py`
- `tests/test_config.py`
- `docs/deployment.md`

**Estimated scope:** Large, split if needed

### Task 5: Add Backup and Restore Documentation

**Description:** Document operational backup procedures for the database, uploaded media, `.env`, and release rollback.

**Acceptance criteria:**
- [x] SQLite backup procedure is documented.
- [x] External database backup guidance is documented.
- [x] Media upload directory backup and restore is documented.
- [x] Rollback checklist is documented.

**Verification:**
- [x] Documentation review against current config keys.

**Files likely touched:**
- `docs/deployment.md`
- `docs/troubleshooting.md`

**Estimated scope:** Small

## Phase 3: Test Coverage Completion

### Task 6: Cover Critical Admin CRUD Workflows

**Description:** Add integration tests for displays, media, schedules, settings, logo, fonts, users, and API token CRUD paths.

**Acceptance criteria:**
- [x] Create/edit/delete flows are tested for each admin resource.
- [x] Permission failures are tested for viewer/editor roles.
- [x] Validation failures return expected status and messages.

**Verification:**
- [x] Full test suite passes.
- [x] Coverage gaps are documented when browser-only behavior cannot be tested directly.

**Files likely touched:**
- `tests/test_admin_dashboard.py`
- `tests/test_auth.py`
- `tests/test_config.py`
- `tests/test_display_player.py`
- new `tests/test_admin_crud.py`

**Estimated scope:** Large, split by feature

### Task 7: Add API Contract Tests

**Description:** Expand REST API tests to cover list/get/create/update/delete, validation errors, auth failures, and player-token access.

**Acceptance criteria:**
- [x] API CRUD endpoints return stable JSON shapes.
- [x] Invalid input returns `422` with details.
- [x] Missing/invalid credentials return `401`.
- [x] Insufficient roles return `403`.

**Verification:**
- [x] API tests pass independently.
- [x] Serializer output remains backward compatible unless intentionally changed.

**Files likely touched:**
- `tests/test_api.py`
- `src/macrosignage/features/api/routes.py`
- `src/macrosignage/features/api/serializers.py`

**Estimated scope:** Medium

### Task 8: Add Production CLI and Packaging Tests

**Description:** Ensure installed commands, package data, static assets, templates, and client packaging stay valid.

**Acceptance criteria:**
- [x] `macrosignage`, `macrosignage-prod`, and `macrosignage-client` entry points are tested.
- [x] Built wheel contains required templates/static assets.
- [x] Release workflows are documented and linked.

**Verification:**
- [x] `uv build`
- [x] `uv run twine check dist/*`
- [x] Package smoke test from built wheel in a temporary environment.

**Files likely touched:**
- `tests/test_cli.py`
- `.github/workflows/ci.yml`
- `docs/development.md`
- `docs/deployment.md`

**Estimated scope:** Medium

## Phase 4: Operational Readiness

### Task 9: Add Health and Diagnostics Checks

**Description:** Expand health and diagnostics endpoints/pages so operators can verify database, media storage, version, and player update state.

**Acceptance criteria:**
- [x] Health endpoint confirms app and database readiness.
- [x] Admin settings page shows key production configuration status without exposing secrets.
- [x] Diagnostics avoid leaking tokens, passwords, database passwords, or full secret values.

**Verification:**
- [x] Tests cover health output and redaction.
- [ ] Manual check: admin settings remains readable.

**Files likely touched:**
- `src/macrosignage/features/api/routes.py`
- `src/macrosignage/features/admin/routes.py`
- `src/macrosignage/features/admin/templates/admin/settings.html`
- `tests/test_config.py`

**Estimated scope:** Medium

### Task 10: Add Deployment Guides for systemd and Docker

**Description:** Provide copy-pasteable production deployment examples for common self-hosted setups.

**Acceptance criteria:**
- [x] systemd service example covers env file, working directory, user, restart policy, and logs.
- [x] Docker guide covers persistent database/media volumes.
- [x] Reverse proxy HTTPS notes are included.

**Verification:**
- [x] Commands match current CLI and config names.

**Files likely touched:**
- `docs/deployment.md`
- `docs/installation.md`
- optional `deploy/` examples

**Estimated scope:** Medium

## Checkpoints

### Baseline Checkpoint

- [x] Tasks 1-3 complete.
- [x] Full test suite passes.
- [x] Production deployment doc updated.

### Data Safety Checkpoint

- [x] Tasks 4-5 complete.
- [x] Upgrade tests pass against representative old schemas.
- [x] Backup and rollback procedure reviewed.

### Test Completion Checkpoint

- [x] Tasks 6-8 complete.
- [x] CI runs all required checks.
- [x] Critical user workflows have automated coverage.

### v1.0 Readiness Checkpoint

- [x] Tasks 9-10 complete.
- [ ] Release process tested on a version tag.
- [ ] README v1.0 roadmap item can be marked complete.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Runtime schema patching diverges from real migrations | High | Add upgrade tests first, then formalize migration commands. |
| Security headers break display playback or embedded media | Medium | Test player page and document required CSP exceptions. |
| Production defaults are too strict for local users | Medium | Enforce only in production command/mode; keep `dev` ergonomic. |
| Test suite grows slow | Medium | Keep most tests Flask integration/unit level; reserve browser checks for critical UI behavior. |
| Existing installs have schedule times saved as local wall-clock values | Medium | Keep compatibility flags and upgrade tests around schedule timing. |

## Open Questions

- Should production startup fail hard on unsafe config, or warn unless `MACROSIGNAGE_STRICT_PRODUCTION=true` is set? = hard
- Which deployment target should be first-class for v1.0: systemd, Docker, or both? = both
- Should database migrations stay automatic on startup, or become an explicit admin/CLI operation before v1.0? = automatic
