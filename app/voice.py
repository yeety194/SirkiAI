from __future__ import annotations

from .config import settings


class Voice:
    """Optional text-to-speech wrapper. Disabled unless VOICE_ENABLED=true."""

    def __init__(self) -> None:
        self._engine = None
        if settings.voice_enabled:
            try:
                import pyttsx3

                self._engine = pyttsx3.init()
            except Exception:
                self._engine = None

    @property
    def available(self) -> bool:
        return self._engine is not None

    def speak(self, text: str) -> None:
        if not self._engine or not text.strip():
            return
        self._engine.say(text)
        self._engine.runAndWait()
