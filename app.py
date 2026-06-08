import logging

import requests
from flask import Flask

from config import AppConfig, ConfigError
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

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
