from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .config import settings
from .hermes import HermesClient
from .ui import MainWindow

SYSTEM_PROMPT = (
    "You are SirkiAI, a helpful Windows desktop assistant. "
    "Be concise, practical, and clear. Prefer short actionable answers."
)


def main() -> None:
    application = QApplication(sys.argv)
    application.setApplicationName(settings.app_name)
    application.setOrganizationName("SirkiAI")

    client = HermesClient(
        settings.hermes_base_url,
        settings.hermes_api_key,
        settings.hermes_model,
        settings.hermes_api_endpoint,
        timeout_seconds=settings.request_timeout_seconds,
        system_prompt=SYSTEM_PROMPT,
    )
    window = MainWindow(client, settings.app_name)
    window.show()
    sys.exit(application.exec())
