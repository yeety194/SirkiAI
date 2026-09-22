from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "SirkiAI")
    hermes_base_url: str = os.getenv("HERMES_BASE_URL", "")
    hermes_api_key: str = os.getenv("HERMES_API_KEY", "")
    hermes_model: str = os.getenv("HERMES_MODEL", "hermes-3")
    hermes_api_endpoint: str = os.getenv("HERMES_API_ENDPOINT", "/chat/completions")
    voice_enabled: bool = _env_bool("VOICE_ENABLED")
    tools_enabled: bool = _env_bool("TOOLS_ENABLED", "true")
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

    @property
    def hermes_configured(self) -> bool:
        return bool(self.hermes_base_url and self.hermes_api_key)


settings = Settings()
