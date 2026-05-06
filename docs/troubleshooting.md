# Troubleshooting

## Login redirects repeatedly

Check that the first admin account exists and that the user is active.

## API returns 401

Confirm the request has `Authorization: Bearer <token>`, the token is active, and the owner user is active.

## API returns 403

The token owner does not have the required role for that action.

## Player does not update

Refresh the player page once, then confirm `/displays/<display_id>/events` is reachable from the player browser.

## Upgrade fails on startup

Stop MacroSignage and keep the failed database unchanged for inspection. Restore the pre-upgrade database and media backups if the app must return to service quickly, then check the startup log for the first schema or driver error.

Common checks:

- Confirm `MACROSIGNAGE_DATABASE_URI` points to the expected database.
- Confirm the selected database driver is installed.
- Confirm the app process can write to the SQLite database file or connect to the external database.
- Review `docs/deployment.md` for the backup, upgrade, restore, and rollback order.
