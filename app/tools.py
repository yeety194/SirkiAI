from __future__ import annotations

import os
import platform
import subprocess
import webbrowser
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    message: str


class DesktopTools:
    """Permission-gated local desktop capabilities.

    Keep model-facing tool execution behind an allowlist and explicit user consent.
    """

    ALLOWED = frozenset({"system_info", "open_path", "open_url"})

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
        except Exception as exc:  # noqa: BLE001 — surface browser failures to UI
            return ToolResult(False, f"Could not open URL: {exc}")

    def run(self, name: str, argument: str = "") -> ToolResult:
        if name not in self.ALLOWED:
            return ToolResult(False, f"Tool not allowed: {name}")
        if name == "system_info":
            return self.system_info()
        if name == "open_path":
            return self.open_path(argument)
        if name == "open_url":
            return self.open_url(argument)
        return ToolResult(False, f"Unhandled tool: {name}")
