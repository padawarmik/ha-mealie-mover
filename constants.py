from os import getenv

HA_URL = getenv("HA_URL")
MEALIE_URL = getenv("MEALIE_URL")
HA_TOKEN = getenv("HA_TOKEN")
MEALIE_TOKEN = getenv("MEALIE_TOKEN")

ENDPOINT_HA = f'{HA_URL}/api/services/todo/get_items?return_response'
DATA_HA = '{"entity_id": "todo.cookidoo_shopping_list"}'

HEADERS_HA = {"Authorization": f"Bearer {HA_TOKEN}"}
HEADERS_MEALIE = {"Authorization": f"Bearer {MEALIE_TOKEN}"}

ENDPOINT_MEALIE_LISTS = f"{MEALIE_URL}/api/households/shopping/lists"
ENDPOINT_MEALIE_ITEMS = f"{MEALIE_URL}/api/households/shopping/items/create-bulk"
