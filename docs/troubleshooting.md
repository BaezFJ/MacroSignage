# Troubleshooting

## Login redirects repeatedly

Check that the first admin account exists and that the user is active.

## API returns 401

Confirm the request has `Authorization: Bearer <token>`, the token is active, and the owner user is active.

## API returns 403

The token owner does not have the required role for that action.

## Player does not update

Refresh the player page once, then confirm `/displays/<display_id>/events` is reachable from the player browser.
