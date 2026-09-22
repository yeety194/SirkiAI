from __future__ import annotations

import json
import os
import platform
import subprocess
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .automation import DesktopAutomation
from .memory import MemoryStore
from .reminders import ReminderStore, parse_reminder
from .screen import ScreenCapture


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    message: str


ConsentCallback = Callable[[str, str], bool]


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "system_info",
            "description": "Read basic local system information.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_path",
            "description": "Open a local file or folder path.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open an http(s) URL in the default browser.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_remember",
            "description": "Store a key/value memory when the user opts into memory.",
            "parameters": {
                "type": "object",
                "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
                "required": ["key", "value"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_recall",
            "description": "Search stored memories.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "capture_screen",
            "description": "Capture the screen for a vision/context prompt.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": "Create a local reminder, e.g. 'in 10m stretch'.",
            "parameters": {
                "type": "object",
                "properties": {"spec": {"type": "string"}},
                "required": ["spec"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "automation_type_text",
            "description": "Type safe text via keyboard automation.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "automation_hotkey",
            "description": "Press an allowlisted hotkey like ctrl+c.",
            "parameters": {
                "type": "object",
                "properties": {"keys": {"type": "string"}},
                "required": ["keys"],
                "additionalProperties": False,
            },
        },
    },
]


class DesktopTools:
    """Permission-gated local desktop capabilities and model tool bridge target."""

    ALLOWED = frozenset(
        {
            "system_info",
            "open_path",
            "open_url",
            "memory_remember",
            "memory_recall",
            "capture_screen",
            "create_reminder",
            "automation_type_text",
            "automation_hotkey",
            "automation_click",
            "automation_move",
        }
    )

    def __init__(
        self,
        *,
        memory: MemoryStore | None = None,
        reminders: ReminderStore | None = None,
        screen: ScreenCapture | None = None,
        automation: DesktopAutomation | None = None,
        tools_enabled: bool = True,
    ) -> None:
        self.memory = memory
        self.reminders = reminders
        self.screen = screen
        self.automation = automation
        self.tools_enabled = tools_enabled

    @staticmethod
    def system_info() -> ToolResult:
        info = {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cwd": os.getcwd(),
        }
        formatted = "\n".join(f"{key}: {value}" for key, value in info.items())
        return ToolResult(True, formatted)

    @staticmethod
    def open_path(path: str) -> ToolResult:
        target = Path(path).expanduser()
        if not target.exists():
            return ToolResult(False, f"Path not found: {target}")
        try:
            if os.name == "nt":
                os.startfile(str(target))  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(target)])
            else:
                subprocess.Popen(["xdg-open", str(target)])
            return ToolResult(True, f"Opened: {target}")
        except OSError as exc:
            return ToolResult(False, f"Could not open {target}: {exc}")

    @staticmethod
    def open_url(url: str) -> ToolResult:
        if not url.startswith(("http://", "https://")):
            return ToolResult(False, "URL must start with http:// or https://")
        try:
            webbrowser.open(url)
            return ToolResult(True, f"Opened URL: {url}")
        except Exception as exc:  # noqa: BLE001
            return ToolResult(False, f"Could not open URL: {exc}")

    def run(self, name: str, argument: str = "", *, args: dict[str, Any] | None = None) -> ToolResult:
        if not self.tools_enabled:
            return ToolResult(False, "Tools are disabled. Set TOOLS_ENABLED=true in .env.")
        if name not in self.ALLOWED:
            return ToolResult(False, f"Tool not allowed: {name}")

        payload = args or {}
        if name == "system_info":
            return self.system_info()
        if name == "open_path":
            return self.open_path(str(payload.get("path") or argument))
        if name == "open_url":
            return self.open_url(str(payload.get("url") or argument))
        if name == "memory_remember":
            return self._memory_remember(str(payload.get("key") or ""), str(payload.get("value") or argument))
        if name == "memory_recall":
            return self._memory_recall(str(payload.get("query") or argument))
        if name == "capture_screen":
            return self._capture_screen()
        if name == "create_reminder":
            return self._create_reminder(str(payload.get("spec") or argument))
        if name == "automation_type_text":
            return self._automation("type_text", str(payload.get("text") or argument))
        if name == "automation_hotkey":
            return self._automation("hotkey", str(payload.get("keys") or argument))
        if name == "automation_click":
            return self._automation("click", argument or f"{payload.get('x')},{payload.get('y')}")
        if name == "automation_move":
            return self._automation("move", argument or f"{payload.get('x')},{payload.get('y')}")
        return ToolResult(False, f"Unhandled tool: {name}")

    def execute_with_consent(
        self,
        name: str,
        *,
        args: dict[str, Any] | None = None,
        argument: str = "",
        consent: ConsentCallback | None = None,
        summary: str | None = None,
    ) -> ToolResult:
        details = summary or f"Run tool `{name}` with {args or argument or '{}'}"
        if consent is not None and not consent(name, details):
            return ToolResult(False, f"User denied tool: {name}")
        return self.run(name, argument, args=args)

    def _memory_remember(self, key: str, value: str) -> ToolResult:
        if not self.memory or not self.memory.enabled:
            return ToolResult(False, "Memory disabled. Set MEMORY_ENABLED=true in .env.")
        if not key.strip() or not value.strip():
            return ToolResult(False, "memory_remember requires key and value")
        item = self.memory.remember(key, value)
        if not item:
            return ToolResult(False, "Could not store memory")
        return ToolResult(True, f"Remembered #{item.id} {item.key}={item.value}")

    def _memory_recall(self, query: str) -> ToolResult:
        if not self.memory or not self.memory.enabled:
            return ToolResult(False, "Memory disabled. Set MEMORY_ENABLED=true in .env.")
        items = self.memory.recall(query) if query else self.memory.list_recent()
        if not items:
            return ToolResult(True, "No memories found.")
        lines = [f"#{item.id} {item.key}: {item.value}" for item in items]
        return ToolResult(True, "\n".join(lines))

    def _capture_screen(self) -> ToolResult:
        if not self.screen:
            return ToolResult(False, "Screen capture unavailable")
        result = self.screen.capture()
        return ToolResult(result.ok, result.message)

    def _create_reminder(self, spec: str) -> ToolResult:
        if not self.reminders or not self.reminders.enabled:
            return ToolResult(False, "Reminders disabled. Set REMINDERS_ENABLED=true in .env.")
        parsed = parse_reminder(spec)
        if not parsed:
            return ToolResult(False, "Could not parse reminder. Try: in 10m stretch")
        due, message = parsed
        item = self.reminders.add(message, due)
        if not item:
            return ToolResult(False, "Could not create reminder")
        return ToolResult(True, f"Reminder #{item.id} at {item.due_at}: {item.message}")

    def _automation(self, action: str, argument: str) -> ToolResult:
        if not self.automation:
            return ToolResult(False, "Automation unavailable")
        result = self.automation.run(action, argument)
        return ToolResult(result.ok, result.message)


def tool_args_from_call(arguments: Any) -> dict[str, Any]:
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str) and arguments.strip():
        try:
            data = json.loads(arguments)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return {"value": arguments}
    return {}
