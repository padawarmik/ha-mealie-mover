import asyncio
from collections.abc import Mapping, Sequence
from datetime import date
import logging
from pathlib import Path
from typing import Any

import aiohttp
from cookidoo_api import Cookidoo
from cookidoo_api.const import RECIPES_IN_CALENDAR_WEEK_PATH
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
from mover import (
    ShoppingListMoverError,
    create_mealie_items,
    create_mealie_plan_note,
    get_mealie_shopping_list_id,
    mealie_plan_note_exists,
)


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


def add_cookidoo_plan_note_to_mealie(
    app_config: AppConfig,
    cookidoo_config: CookidooAppConfig,
    planned_date: date,
) -> int:
    planned_recipes = asyncio.run(
        get_cookidoo_planned_recipes_for_day(cookidoo_config, planned_date)
    )
    if not planned_recipes:
        raise ShoppingListMoverError(
            f"No Cookidoo recipes planned for {planned_date.isoformat()}"
        )

    note_text = build_cookidoo_plan_note(planned_recipes)

    with requests.Session() as session:
        if mealie_plan_note_exists(
            app_config,
            session,
            planned_date.isoformat(),
            note_text,
        ):
            logger.info("Cookidoo plan note already exists for %s", planned_date)
            return 200

        response = create_mealie_plan_note(
            app_config,
            session,
            planned_date.isoformat(),
            note_text,
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


async def get_cookidoo_planned_recipes_for_day(
    config: CookidooAppConfig,
    planned_date: date,
) -> list[str]:
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
            return await get_cookidoo_calendar_recipes_for_day(cookidoo, planned_date)
        except CookidooAuthException:
            if not loaded_cookies:
                raise

            logger.warning("Stored Cookidoo cookies expired, logging in again")
            await cookidoo.login()
            cookidoo.save_cookies(config.cookies_file)
            return await get_cookidoo_calendar_recipes_for_day(cookidoo, planned_date)


async def get_cookidoo_calendar_recipes_for_day(
    cookidoo: Cookidoo,
    planned_date: date,
) -> list[str]:
    url = cookidoo.api_endpoint / RECIPES_IN_CALENDAR_WEEK_PATH.format(
        **cookidoo.localization.__dict__,
        day=planned_date.isoformat(),
    )
    result = await cookidoo._request_json("get", url, "loading recipes in calendar week")
    if not isinstance(result, Mapping):
        raise ShoppingListMoverError("Unexpected Cookidoo calendar response")

    planned_day = next(
        (
            calendar_day
            for calendar_day in result.get("myDays", [])
            if isinstance(calendar_day, Mapping)
            and calendar_day.get("dayKey") == planned_date.isoformat()
        ),
        None,
    )
    if planned_day is None:
        return []

    recipes = [
        *planned_day.get("recipes", []),
        *planned_day.get("customerRecipes", []),
    ]
    return [
        format_cookidoo_calendar_recipe(recipe, cookidoo)
        for recipe in recipes
        if isinstance(recipe, Mapping)
    ]


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


def format_cookidoo_calendar_recipe(recipe: Mapping[str, Any], cookidoo: Cookidoo) -> str:
    title = str(recipe.get("title") or "").strip()
    recipe_id = str(recipe.get("id") or "").strip()
    if not title:
        return ""

    if not recipe_id:
        return title

    url = cookidoo.api_endpoint / "recipes" / "recipe" / cookidoo.localization.language / recipe_id
    return f"{title} ({url})"


def build_cookidoo_plan_note(planned_recipes: Sequence[str]) -> str:
    recipes = "\n".join(f"- {recipe}" for recipe in planned_recipes if recipe)
    return f"Zaplanowane w Cookidoo:\n{recipes}"
