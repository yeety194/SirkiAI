from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "SirkiAI")
    hermes_base_url: str = os.getenv("HERMES_BASE_URL", "")
    hermes_api_key: str = os.getenv("HERMES_API_KEY", "")
    hermes_model: str = os.getenv("HERMES_MODEL", "hermes-3")
    hermes_api_endpoint: str = os.getenv("HERMES_API_ENDPOINT", "/chat/completions")
    voice_enabled: bool = os.getenv("VOICE_ENABLED", "false").lower() == "true"


settings = Settings()
