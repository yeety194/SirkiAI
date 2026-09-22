from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .config import settings
from .hermes import HermesClient
from .ui import MainWindow


def main() -> None:
    application = QApplication(sys.argv)
    client = HermesClient(settings.hermes_base_url, settings.hermes_api_key, settings.hermes_model, settings.hermes_api_endpoint)
    window = MainWindow(client, settings.app_name)
    window.show()
    sys.exit(application.exec())
