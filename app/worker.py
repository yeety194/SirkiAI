from __future__ import annotations

import threading
from typing import Callable

from PySide6.QtCore import QObject, Signal, Slot

from .hermes import HermesClient


class ChatWorker(QObject):
    """Runs Hermes chat off the UI thread; requests tool consent via signals."""

    finished = Signal(str, list)
    failed = Signal(str)
    consent_requested = Signal(str, str)

    def __init__(self, client: HermesClient) -> None:
        super().__init__()
        self.client = client
        self._prompt = ""
        self._consent_event = threading.Event()
        self._consent_result = False

    def set_prompt(self, prompt: str) -> None:
        self._prompt = prompt

    def provide_consent(self, allowed: bool) -> None:
        self._consent_result = allowed
        self._consent_event.set()

    def _consent(self, name: str, details: str) -> bool:
        self._consent_event.clear()
        self.consent_requested.emit(name, details)
        # Block worker thread until UI answers.
        self._consent_event.wait(timeout=120)
        return self._consent_result

    @Slot()
    def run(self) -> None:
        try:
            outcome = self.client.chat_detailed(self._prompt, consent=self._consent)
            self.finished.emit(outcome.text, outcome.tool_trace)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


ConsentProvider = Callable[[str, str], bool]
