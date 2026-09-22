from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpeechResult:
    ok: bool
    text: str
    message: str


class SpeechRecognizer:
    """Optional push-to-talk speech recognition.

    Uses the SpeechRecognition package when installed. Falls back gracefully otherwise.
    """

    def __init__(self, *, enabled: bool) -> None:
        self.enabled = enabled
        self._recognizer = None
        if enabled:
            try:
                import speech_recognition as sr

                self._recognizer = sr.Recognizer()
            except Exception:
                self._recognizer = None

    @property
    def available(self) -> bool:
        return self.enabled and self._recognizer is not None

    def listen_once(self, *, timeout: float = 5.0, phrase_time_limit: float = 12.0) -> SpeechResult:
        if not self.enabled:
            return SpeechResult(False, "", "Speech disabled. Set SPEECH_ENABLED=true in .env.")
        if self._recognizer is None:
            return SpeechResult(
                False,
                "",
                "SpeechRecognition is not installed. pip install SpeechRecognition and a mic backend.",
            )
        try:
            import speech_recognition as sr

            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = self._recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = self._recognizer.recognize_google(audio)
            return SpeechResult(True, text.strip(), "ok")
        except Exception as exc:  # noqa: BLE001
            return SpeechResult(False, "", f"Speech recognition failed: {exc}")
