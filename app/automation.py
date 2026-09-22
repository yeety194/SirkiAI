from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AutomationResult:
    ok: bool
    message: str


class DesktopAutomation:
    """Hardened keyboard/mouse automation behind an explicit allowlist.

    Dangerous actions (drag, mouse down, OS shell injection) are intentionally omitted.
    pyautogui FAILSAFE remains on: move mouse to a corner to abort.
    """

    ALLOWED = frozenset({"type_text", "hotkey", "click", "move"})

    _HOTKEY_RE = re.compile(r"^[a-z0-9+]+$", re.IGNORECASE)
    _SAFE_TEXT_RE = re.compile(r"^[\w\s.,;:!?@#%&'\"()\[\]{}/\-+*=<>\\$]+$", re.UNICODE)
    _ALLOWED_KEYS = frozenset(
        {
            "ctrl",
            "alt",
            "shift",
            "win",
            "cmd",
            "enter",
            "tab",
            "esc",
            "space",
            "up",
            "down",
            "left",
            "right",
            *list("abcdefghijklmnopqrstuvwxyz0123456789"),
            "f1",
            "f2",
            "f3",
            "f4",
            "f5",
        }
    )

    def __init__(self, *, enabled: bool) -> None:
        self.enabled = enabled

    def run(self, name: str, argument: str = "") -> AutomationResult:
        if not self.enabled:
            return AutomationResult(False, "Automation disabled. Set AUTOMATION_ENABLED=true in .env.")
        if name not in self.ALLOWED:
            return AutomationResult(False, f"Automation action not allowed: {name}")

        # Validate before importing pyautogui so CI/Linux without tkinter still tests the allowlist.
        if name == "type_text":
            check = self._validate_type_text(argument)
            if check is not None:
                return check
        elif name == "hotkey":
            check = self._validate_hotkey(argument)
            if check is not None:
                return check
        elif name in {"click", "move"}:
            check = self._validate_point(argument, name)
            if check is not None:
                return check

        try:
            import pyautogui

            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.05
        except BaseException as exc:  # includes SystemExit from mouseinfo on some Linux setups
            return AutomationResult(False, f"pyautogui unavailable: {exc}")

        if name == "type_text":
            pyautogui.typewrite(argument, interval=0.02)
            return AutomationResult(True, f"Typed {len(argument)} characters")
        if name == "hotkey":
            keys = [part.strip().lower() for part in argument.split("+") if part.strip()]
            pyautogui.hotkey(*keys)
            return AutomationResult(True, f"Pressed hotkey: {'+'.join(keys)}")
        if name == "click":
            x, y = self._parse_point(argument)
            assert x is not None and y is not None
            pyautogui.click(x, y)
            return AutomationResult(True, f"Clicked at {x},{y}")
        if name == "move":
            x, y = self._parse_point(argument)
            assert x is not None and y is not None
            pyautogui.moveTo(x, y, duration=0.2)
            return AutomationResult(True, f"Moved pointer to {x},{y}")
        return AutomationResult(False, f"Unhandled automation action: {name}")

    def _validate_type_text(self, text: str) -> AutomationResult | None:
        if not text or len(text) > 500:
            return AutomationResult(False, "type_text requires 1–500 characters")
        if not self._SAFE_TEXT_RE.match(text):
            return AutomationResult(False, "type_text rejected unsafe characters")
        return None

    def _validate_hotkey(self, spec: str) -> AutomationResult | None:
        keys = [part.strip().lower() for part in spec.split("+") if part.strip()]
        if not keys or len(keys) > 3:
            return AutomationResult(False, "hotkey requires 1–3 keys joined by '+', e.g. ctrl+c")
        if any(key not in self._ALLOWED_KEYS for key in keys):
            return AutomationResult(False, f"hotkey contains disallowed keys: {spec}")
        if not self._HOTKEY_RE.match(spec.replace(" ", "")):
            return AutomationResult(False, "hotkey format invalid")
        return None

    def _validate_point(self, argument: str, action: str) -> AutomationResult | None:
        x, y = self._parse_point(argument)
        if x is None or y is None:
            return AutomationResult(False, f"{action} requires 'x,y' coordinates")
        if not (0 <= x <= 10000 and 0 <= y <= 10000):
            return AutomationResult(False, f"{action} coordinates out of bounds")
        return None

    @staticmethod
    def _parse_point(raw: str) -> tuple[int | None, int | None]:
        parts = [p.strip() for p in raw.replace(" ", "").split(",")]
        if len(parts) != 2:
            return None, None
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            return None, None
