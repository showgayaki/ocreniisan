from typing import Optional
from .config_loader import load_config, Config


class ConfigManager:
    _instance = None
    _config: Optional[Config] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = load_config()
        return cls._instance

    @property
    def config(self) -> Config:
        if self._config is None:
            raise ValueError("Config has not been initialized")
        return self._config
