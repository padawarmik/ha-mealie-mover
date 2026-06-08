import logging

import requests
from flask import Flask

from config import AppConfig, ConfigError, CookidooAppConfig
from cookidoo_api.exceptions import CookidooException
from cookidoo_mover import move_cookidoo_shopping_list_to_mealie
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
                AppConfig.from_env(),
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

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
