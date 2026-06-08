from dataclasses import dataclass
from os import getenv


try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv(override=False)


COOKIDOO_SHOPPING_LIST_ENTITY = "todo.cookidoo_shopping_list"
MEALIE_SHOPPING_LIST_NAME = "shopping"
MEALIE_COOKIDOO_PLAN_ENTRY_TYPE = "dinner"
MEALIE_COOKIDOO_PLAN_TITLE = "Cookidoo"
REQUEST_TIMEOUT_SECONDS = 15
DEFAULT_COOKIDOO_COUNTRY = "pl"
DEFAULT_COOKIDOO_LANGUAGE = "pl"
DEFAULT_COOKIDOO_COOKIES_FILE = "/tmp/.cookidoo-cookies"


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class AppConfig:
    home_assistant_url: str
    mealie_url: str
    home_assistant_token: str
    mealie_token: str
    mealie_cookidoo_plan_entry_type: str = MEALIE_COOKIDOO_PLAN_ENTRY_TYPE
    mealie_cookidoo_plan_title: str = MEALIE_COOKIDOO_PLAN_TITLE
    request_timeout: int = REQUEST_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls, require_home_assistant: bool = True) -> "AppConfig":
        required_env_vars = {
            "MEALIE_URL": getenv("MEALIE_URL") or "",
            "MEALIE_TOKEN": getenv("MEALIE_TOKEN") or "",
        }
        if require_home_assistant:
            required_env_vars.update(
                {
                    "HA_URL": getenv("HA_URL") or "",
                    "HA_TOKEN": getenv("HA_TOKEN") or "",
                }
            )

        missing_env_vars = [name for name, value in required_env_vars.items() if not value]
        if missing_env_vars:
            raise ConfigError(f"Missing environment variables: {', '.join(missing_env_vars)}")

        return cls(
            home_assistant_url=required_env_vars.get("HA_URL", "").rstrip("/"),
            mealie_url=required_env_vars["MEALIE_URL"].rstrip("/"),
            home_assistant_token=required_env_vars.get("HA_TOKEN", ""),
            mealie_token=required_env_vars["MEALIE_TOKEN"],
            mealie_cookidoo_plan_entry_type=getenv("MEALIE_COOKIDOO_PLAN_ENTRY_TYPE") or MEALIE_COOKIDOO_PLAN_ENTRY_TYPE,
            mealie_cookidoo_plan_title=getenv("MEALIE_COOKIDOO_PLAN_TITLE") or MEALIE_COOKIDOO_PLAN_TITLE,
        )

    @property
    def home_assistant_get_items_url(self) -> str:
        return f"{self.home_assistant_url}/api/services/todo/get_items?return_response"

    @property
    def mealie_shopping_lists_url(self) -> str:
        return f"{self.mealie_url}/api/households/shopping/lists"

    @property
    def mealie_create_items_url(self) -> str:
        return f"{self.mealie_url}/api/households/shopping/items/create-bulk"

    @property
    def mealie_mealplans_url(self) -> str:
        return f"{self.mealie_url}/api/households/mealplans"

    @property
    def home_assistant_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.home_assistant_token}"}

    @property
    def mealie_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.mealie_token}"}


@dataclass(frozen=True)
class CookidooAppConfig:
    email: str
    password: str
    country: str = DEFAULT_COOKIDOO_COUNTRY
    language: str = DEFAULT_COOKIDOO_LANGUAGE
    cookies_file: str = DEFAULT_COOKIDOO_COOKIES_FILE

    @classmethod
    def from_env(cls) -> "CookidooAppConfig":
        required_env_vars = {
            "COOKIDOO_EMAIL": getenv("COOKIDOO_EMAIL") or "",
            "COOKIDOO_PASSWORD": getenv("COOKIDOO_PASSWORD") or "",
        }
        missing_env_vars = [name for name, value in required_env_vars.items() if not value]
        if missing_env_vars:
            raise ConfigError(f"Missing environment variables: {', '.join(missing_env_vars)}")

        return cls(
            email=required_env_vars["COOKIDOO_EMAIL"],
            password=required_env_vars["COOKIDOO_PASSWORD"],
            country=getenv("COOKIDOO_COUNTRY") or DEFAULT_COOKIDOO_COUNTRY,
            language=getenv("COOKIDOO_LANGUAGE") or DEFAULT_COOKIDOO_LANGUAGE,
            cookies_file=getenv("COOKIDOO_COOKIES_FILE") or DEFAULT_COOKIDOO_COOKIES_FILE,
        )
