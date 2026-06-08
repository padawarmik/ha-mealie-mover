# ha-mealie-mover

## Endpoints

- `GET|POST /move` - moves the Home Assistant Cookidoo todo list to Mealie.
- `GET|POST /move/cookidoo` - moves the Cookidoo shopping list directly to Mealie.

## Environment Variables

Required for Mealie:

- `MEALIE_URL`
- `MEALIE_TOKEN`

Required for `/move`:

- `HA_URL`
- `HA_TOKEN`

Required for `/move/cookidoo`:

- `COOKIDOO_EMAIL`
- `COOKIDOO_PASSWORD`

Optional for `/move/cookidoo`:

- `COOKIDOO_COUNTRY` - defaults to `pl`
- `COOKIDOO_LANGUAGE` - defaults to `pl-PL`
- `COOKIDOO_COOKIES_FILE` - defaults to `.cookidoo-cookies`
