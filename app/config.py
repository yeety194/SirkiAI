from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}


def _default_data_dir() -> Path:
    override = os.getenv("SIRKIAI_DATA_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".sirkiai"


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "SirkiAI")
    hermes_base_url: str = os.getenv("HERMES_BASE_URL", "")
    hermes_api_key: str = os.getenv("HERMES_API_KEY", "")
    hermes_model: str = os.getenv("HERMES_MODEL", "hermes-3")
    hermes_api_endpoint: str = os.getenv("HERMES_API_ENDPOINT", "/chat/completions")
    voice_enabled: bool = _env_bool("VOICE_ENABLED")
    tools_enabled: bool = _env_bool("TOOLS_ENABLED", "true")
    memory_enabled: bool = _env_bool("MEMORY_ENABLED")
    tool_calling_enabled: bool = _env_bool("TOOL_CALLING_ENABLED", "true")
    automation_enabled: bool = _env_bool("AUTOMATION_ENABLED")
    speech_enabled: bool = _env_bool("SPEECH_ENABLED")
    screen_enabled: bool = _env_bool("SCREEN_ENABLED", "true")
    reminders_enabled: bool = _env_bool("REMINDERS_ENABLED", "true")
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    max_tool_rounds: int = int(os.getenv("MAX_TOOL_ROUNDS", "3"))
    data_dir: Path = _default_data_dir()

    @property
    def hermes_configured(self) -> bool:
        return bool(self.hermes_base_url and self.hermes_api_key)

    @property
    def db_path(self) -> Path:
        return self.data_dir / "sirkiai.sqlite3"


settings = Settings()
