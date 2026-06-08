# ha-mealie-mover

## Local Development

Create a local environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
make install
```

The application optionally loads variables from `.env` if the file exists. Variables already present in the process environment are not overwritten.

Prepare local configuration:

```bash
cp .env.example .env
```

Run syntax checks:

```bash
make check
```

Run the app locally:

```bash
make run-dev
```

## Endpoints

- `GET|POST /move` - moves the Home Assistant Cookidoo todo list to Mealie.
- `GET|POST /move/cookidoo` - moves the Cookidoo shopping list directly to Mealie.
- `GET|POST /move/cookidoo/plan?date=YYYY-MM-DD` - adds a Mealie meal plan note for Cookidoo recipes planned on that date. If `date` is omitted, today's date is used.
- `GET|POST /move/cookidoo/plan/sync` - syncs Cookidoo planned recipes from 7 days ago through 7 days ahead into Mealie meal plan notes. Existing identical notes are skipped.

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

Required for `/move/cookidoo/plan/sync`:

- `COOKIDOO_EMAIL`
- `COOKIDOO_PASSWORD`

Optional for `/move/cookidoo`:

- `COOKIDOO_COUNTRY` - defaults to `pl`
- `COOKIDOO_LANGUAGE` - defaults to `pl`
- `COOKIDOO_COOKIES_FILE` - defaults to `/tmp/.cookidoo-cookies`
- `MEALIE_COOKIDOO_PLAN_ENTRY_TYPE` - defaults to `dinner`
- `MEALIE_COOKIDOO_PLAN_TITLE` - defaults to `Cookidoo`
