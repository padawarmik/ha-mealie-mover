from dataclasses import dataclass
from os import getenv


COOKIDOO_SHOPPING_LIST_ENTITY = "todo.cookidoo_shopping_list"
MEALIE_SHOPPING_LIST_NAME = "shopping"
REQUEST_TIMEOUT_SECONDS = 15


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class AppConfig:
    home_assistant_url: str
    mealie_url: str
    home_assistant_token: str
    mealie_token: str
    request_timeout: int = REQUEST_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> "AppConfig":
        required_env_vars = {
            "HA_URL": getenv("HA_URL") or "",
            "MEALIE_URL": getenv("MEALIE_URL") or "",
            "HA_TOKEN": getenv("HA_TOKEN") or "",
            "MEALIE_TOKEN": getenv("MEALIE_TOKEN") or "",
        }
        missing_env_vars = [name for name, value in required_env_vars.items() if not value]
        if missing_env_vars:
            raise ConfigError(f"Missing environment variables: {', '.join(missing_env_vars)}")

        return cls(
            home_assistant_url=required_env_vars["HA_URL"].rstrip("/"),
            mealie_url=required_env_vars["MEALIE_URL"].rstrip("/"),
            home_assistant_token=required_env_vars["HA_TOKEN"],
            mealie_token=required_env_vars["MEALIE_TOKEN"],
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
    def home_assistant_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.home_assistant_token}"}

    @property
    def mealie_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.mealie_token}"}
