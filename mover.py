import logging
from typing import Any

import requests

from config import AppConfig, COOKIDOO_SHOPPING_LIST_ENTITY, MEALIE_SHOPPING_LIST_NAME


logger = logging.getLogger(__name__)


class ShoppingListMoverError(Exception):
    pass


def move_shopping_list(config: AppConfig, session: requests.Session | None = None) -> int:
    if session is None:
        with requests.Session() as http_session:
            return _move_shopping_list(config, http_session)

    return _move_shopping_list(config, session)


def _move_shopping_list(config: AppConfig, http_session: requests.Session) -> int:
    cookidoo_items = get_cookidoo_shopping_list(config, http_session)

    if not cookidoo_items:
        raise ShoppingListMoverError("Nothing to move from Home Assistant")

    logger.info("Collected %d Cookidoo shopping list items from Home Assistant", len(cookidoo_items))

    mealie_shopping_list_id = get_mealie_shopping_list_id(config, http_session)
    if mealie_shopping_list_id is None:
        raise ShoppingListMoverError(f"Mealie list named '{MEALIE_SHOPPING_LIST_NAME}' was not found")

    logger.info("Found Mealie shopping list ID: %s", mealie_shopping_list_id)

    response = create_mealie_items(config, http_session, cookidoo_items, mealie_shopping_list_id)
    return response.status_code


def create_mealie_items(
    config: AppConfig,
    session: requests.Session,
    shopping_list: list[str],
    shopping_list_id: str,
) -> requests.Response:
    payload = build_mealie_items(shopping_list, shopping_list_id)
    return session.post(
        config.mealie_create_items_url,
        headers=config.mealie_headers,
        json=payload,
        timeout=config.request_timeout,
    )


def get_cookidoo_shopping_list(config: AppConfig, session: requests.Session) -> list[str]:
    response = session.post(
        config.home_assistant_get_items_url,
        json={"entity_id": COOKIDOO_SHOPPING_LIST_ENTITY},
        headers=config.home_assistant_headers,
        timeout=config.request_timeout,
    )
    response.raise_for_status()

    items = response.json()["service_response"][COOKIDOO_SHOPPING_LIST_ENTITY]["items"]
    shopping_list = [format_cookidoo_item(item) for item in items]
    return [item for item in shopping_list if item]


def get_mealie_shopping_list_id(config: AppConfig, session: requests.Session) -> str | None:
    response = session.get(
        config.mealie_shopping_lists_url,
        headers=config.mealie_headers,
        timeout=config.request_timeout,
    )
    response.raise_for_status()

    items = response.json()["items"]
    shopping_list = next(
        (item for item in items if item["name"] == MEALIE_SHOPPING_LIST_NAME),
        None,
    )
    if shopping_list is None:
        return None

    return shopping_list["id"]


def format_cookidoo_item(item: dict[str, Any]) -> str:
    description = item.get("description", "")
    summary = item.get("summary", "")
    return f"{description} {summary}".strip()


def build_mealie_items(shopping_list: list[str], shopping_list_id: str) -> list[dict[str, Any]]:
    return [
        {
            "quantity": 0,
            "note": item,
            "display": item,
            "shoppingListId": shopping_list_id,
        }
        for item in shopping_list
    ]
