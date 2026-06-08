# ha-mealie-mover

## Endpoints

- `GET|POST /move` - moves the Home Assistant Cookidoo todo list to Mealie.
- `GET|POST /move/cookidoo` - moves the Cookidoo shopping list directly to Mealie.
- `GET|POST /move/cookidoo/plan?date=YYYY-MM-DD` - adds a Mealie meal plan note for Cookidoo recipes planned on that date. If `date` is omitted, today's date is used.

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

Required for `/move/cookidoo/plan`:

- `COOKIDOO_EMAIL`
- `COOKIDOO_PASSWORD`

Optional for `/move/cookidoo`:

- `COOKIDOO_COUNTRY` - defaults to `pl`
- `COOKIDOO_LANGUAGE` - defaults to `pl-PL`
- `COOKIDOO_COOKIES_FILE` - defaults to `.cookidoo-cookies`
- `MEALIE_COOKIDOO_PLAN_ENTRY_TYPE` - defaults to `dinner`
- `MEALIE_COOKIDOO_PLAN_TITLE` - defaults to `Cookidoo`
