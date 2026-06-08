from datetime import date, datetime
import logging

import requests
from flask import Flask, jsonify, request

from config import AppConfig, ConfigError, CookidooAppConfig
from cookidoo_api.exceptions import CookidooException
from cookidoo_mover import (
    add_cookidoo_plan_note_to_mealie,
    move_cookidoo_shopping_list_to_mealie,
    sync_cookidoo_plan_notes_to_mealie,
)
from mover import ShoppingListMoverError, move_shopping_list


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def health_check():
        return "hello"

    @app.route("/move", methods=["GET", "POST"])
    def move():
        try:
            status_code = move_shopping_list(AppConfig.from_env())
        except ConfigError as error:
            logger.exception("Invalid application configuration")
            return str(error), 500
        except (ShoppingListMoverError, KeyError, requests.RequestException) as error:
            logger.exception("Shopping list move failed")
            return str(error), 500

        if status_code == 201:
            logger.info("Move completed")

        return "", status_code

    @app.route("/move/cookidoo", methods=["GET", "POST"])
    def move_cookidoo():
        try:
            status_code = move_cookidoo_shopping_list_to_mealie(
                AppConfig.from_env(require_home_assistant=False),
                CookidooAppConfig.from_env(),
            )
        except ConfigError as error:
            logger.exception("Invalid application configuration")
            return str(error), 500
        except (
            CookidooException,
            ShoppingListMoverError,
            KeyError,
            requests.RequestException,
        ) as error:
            logger.exception("Cookidoo shopping list move failed")
            return str(error), 500

        if status_code == 201:
            logger.info("Cookidoo move completed")

        return "", status_code

    @app.route("/move/cookidoo/plan", methods=["GET", "POST"])
    def move_cookidoo_plan():
        try:
            planned_date = parse_planned_date(request.args.get("date"))
            status_code = add_cookidoo_plan_note_to_mealie(
                AppConfig.from_env(require_home_assistant=False),
                CookidooAppConfig.from_env(),
                planned_date,
            )
        except ValueError as error:
            return str(error), 400
        except ConfigError as error:
            logger.exception("Invalid application configuration")
            return str(error), 500
        except (
            CookidooException,
            ShoppingListMoverError,
            KeyError,
            requests.RequestException,
        ) as error:
            logger.exception("Cookidoo plan note move failed")
            return str(error), 500

        if status_code == 201:
            logger.info("Cookidoo plan note added")

        return "", status_code

    @app.route("/move/cookidoo/plan/sync", methods=["GET", "POST"])
    def sync_cookidoo_plan():
        try:
            summary = sync_cookidoo_plan_notes_to_mealie(
                AppConfig.from_env(require_home_assistant=False),
                CookidooAppConfig.from_env(),
            )
        except ConfigError as error:
            logger.exception("Invalid application configuration")
            return str(error), 500
        except (
            CookidooException,
            ShoppingListMoverError,
            KeyError,
            requests.RequestException,
        ) as error:
            logger.exception("Cookidoo plan sync failed")
            return str(error), 500

        logger.info("Cookidoo plan sync completed: %s", summary)
        return jsonify(summary), 200

    return app


def parse_planned_date(date_value: str | None) -> date:
    if not date_value:
        return date.today()

    try:
        return datetime.strptime(date_value, "%Y-%m-%d").date()
    except ValueError as error:
        raise ValueError("date must use YYYY-MM-DD format") from error


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
