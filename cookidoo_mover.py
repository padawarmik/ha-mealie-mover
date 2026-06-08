import asyncio
import logging
from pathlib import Path

import aiohttp
from cookidoo_api import Cookidoo
from cookidoo_api.exceptions import CookidooAuthException, CookidooException
from cookidoo_api.helpers import get_localization_options
from cookidoo_api.types import (
    CookidooAdditionalItem,
    CookidooConfig as CookidooLibraryConfig,
    CookidooIngredientItem,
    CookidooLocalizationConfig,
)
import requests

from config import AppConfig, CookidooAppConfig, MEALIE_SHOPPING_LIST_NAME
from mover import ShoppingListMoverError, create_mealie_items, get_mealie_shopping_list_id


logger = logging.getLogger(__name__)


def move_cookidoo_shopping_list_to_mealie(
    app_config: AppConfig,
    cookidoo_config: CookidooAppConfig,
) -> int:
    cookidoo_items = asyncio.run(get_cookidoo_api_shopping_list(cookidoo_config))
    if not cookidoo_items:
        raise ShoppingListMoverError("Nothing to move from Cookidoo")

    logger.info("Collected %d shopping list items from Cookidoo", len(cookidoo_items))

    with requests.Session() as session:
        mealie_shopping_list_id = get_mealie_shopping_list_id(app_config, session)
        if mealie_shopping_list_id is None:
            raise ShoppingListMoverError(
                f"Mealie list named '{MEALIE_SHOPPING_LIST_NAME}' was not found"
            )

        response = create_mealie_items(
            app_config,
            session,
            cookidoo_items,
            mealie_shopping_list_id,
        )
        return response.status_code


async def get_cookidoo_api_shopping_list(config: CookidooAppConfig) -> list[str]:
    cookie_jar = aiohttp.CookieJar(unsafe=True)
    async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
        localization = await get_cookidoo_localization(config)
        cookidoo = Cookidoo(
            session,
            cfg=CookidooLibraryConfig(
                email=config.email,
                password=config.password,
                localization=localization,
            ),
        )
        loaded_cookies = await login_to_cookidoo(cookidoo, config.cookies_file)

        try:
            ingredient_items, additional_items = await get_cookidoo_items(cookidoo)
        except CookidooAuthException:
            if not loaded_cookies:
                raise

            logger.warning("Stored Cookidoo cookies expired, logging in again")
            await cookidoo.login()
            cookidoo.save_cookies(config.cookies_file)
            ingredient_items, additional_items = await get_cookidoo_items(cookidoo)

    shopping_list = [
        format_cookidoo_ingredient_item(item)
        for item in ingredient_items
        if not item.is_owned
    ]
    shopping_list.extend(item.name for item in additional_items if not item.is_owned)

    return [item for item in shopping_list if item]


async def get_cookidoo_localization(
    config: CookidooAppConfig,
) -> CookidooLocalizationConfig:
    localizations = await get_localization_options(
        country=config.country,
        language=config.language,
    )
    if not localizations:
        raise ShoppingListMoverError(
            f"Cookidoo localization not found for country={config.country}, language={config.language}"
        )

    return localizations[0]


async def login_to_cookidoo(cookidoo: Cookidoo, cookies_file: str) -> bool:
    cookies_path = Path(cookies_file)
    if cookies_path.exists():
        try:
            cookidoo.load_cookies(cookies_path)
            return True
        except CookidooException:
            logger.warning("Stored Cookidoo cookies are invalid, logging in again")

    await cookidoo.login()
    cookidoo.save_cookies(cookies_path)
    return False


async def get_cookidoo_items(
    cookidoo: Cookidoo,
) -> tuple[list[CookidooIngredientItem], list[CookidooAdditionalItem]]:
    ingredient_items = await cookidoo.get_ingredient_items()
    additional_items = await cookidoo.get_additional_items()
    return ingredient_items, additional_items


def format_cookidoo_ingredient_item(item: CookidooIngredientItem) -> str:
    if item.description:
        return f"{item.description} {item.name}".strip()

    return item.name.strip()
