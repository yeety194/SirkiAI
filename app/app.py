from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .automation import DesktopAutomation
from .brain import ollama_reachable, resolve_brain
from .config import settings
from .hermes import HermesClient
from .memory import MemoryStore
from .reminders import ReminderStore
from .screen import ScreenCapture
from .speech import SpeechRecognizer
from .tools import DesktopTools
from .ui import MainWindow
from .voice import Voice

SYSTEM_PROMPT = (
    "You are SirkiAI, a helpful Windows desktop assistant. "
    "Be concise, practical, and clear. Prefer short actionable answers. "
    "When tools are available, request them only for concrete user needs. "
    "Never assume silent permission for desktop actions."
)


def main() -> None:
    application = QApplication(sys.argv)
    application.setApplicationName(settings.app_name)
    application.setOrganizationName("SirkiAI")
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    memory = MemoryStore(settings.db_path, enabled=settings.memory_enabled)
    reminders = ReminderStore(settings.db_path, enabled=settings.reminders_enabled)
    screen = ScreenCapture(enabled=settings.screen_enabled, output_dir=settings.data_dir / "captures")
    automation = DesktopAutomation(enabled=settings.automation_enabled)
    speech = SpeechRecognizer(enabled=settings.speech_enabled)
    voice = Voice()
    tools = DesktopTools(
        memory=memory,
        reminders=reminders,
        screen=screen,
        automation=automation,
        tools_enabled=settings.tools_enabled,
    )

    brain = resolve_brain(settings)
    client = HermesClient(
        brain.base_url,
        brain.api_key,
        brain.model,
        brain.endpoint,
        timeout_seconds=settings.request_timeout_seconds,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        tool_calling_enabled=settings.tool_calling_enabled and settings.tools_enabled,
        max_tool_rounds=settings.max_tool_rounds,
    )
    if memory.enabled:
        context = memory.context_block()
        if context:
            client.inject_system_note(context)

    startup_note = None
    if brain.mode == "local" and not ollama_reachable(brain.base_url):
        startup_note = (
            "Local brain is selected but Ollama is not reachable at "
            f"{brain.base_url}. Run scripts/start_local_brain.ps1 (Windows) "
            "or scripts/start_local_brain.sh, then retry."
        )

    window = MainWindow(
        client=client,
        title=settings.app_name,
        tools=tools,
        memory=memory,
        reminders=reminders,
        screen=screen,
        speech=speech,
        voice=voice,
        brain_label=brain.label,
        startup_note=startup_note,
    )
    window.show()
    sys.exit(application.exec())
