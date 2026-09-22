from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from .hermes import HermesClient


class ChatWorker(QObject):
    """Runs Hermes chat off the UI thread so the window stays responsive."""

    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, client: HermesClient) -> None:
        super().__init__()
        self.client = client
        self._prompt = ""

    def set_prompt(self, prompt: str) -> None:
        self._prompt = prompt

    @Slot()
    def run(self) -> None:
        try:
            reply = self.client.chat(self._prompt)
            self.finished.emit(reply)
        except Exception as exc:  # noqa: BLE001 — keep UI alive on unexpected errors
            self.failed.emit(str(exc))
