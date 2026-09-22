from __future__ import annotations

import base64
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class CaptureResult:
    ok: bool
    message: str
    path: Path | None = None
    mime: str = "image/png"

    def as_data_url(self) -> str | None:
        if not self.ok or not self.path or not self.path.exists():
            return None
        encoded = base64.b64encode(self.path.read_bytes()).decode("ascii")
        return f"data:{self.mime};base64,{encoded}"


class ScreenCapture:
    """Screen capture helper for vision prompts. Requires SCREEN_ENABLED."""

    def __init__(self, *, enabled: bool, output_dir: Path | None = None) -> None:
        self.enabled = enabled
        self.output_dir = output_dir or Path(tempfile.gettempdir()) / "sirkiai-captures"
        if enabled:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, label: str = "screen") -> CaptureResult:
        if not self.enabled:
            return CaptureResult(False, "Screen capture disabled. Set SCREEN_ENABLED=true in .env.")

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self.output_dir / f"{label}-{stamp}.png"

        try:
            image = self._grab()
            image.save(path, format="PNG")
            return CaptureResult(True, f"Captured screen to {path}", path=path)
        except Exception as exc:  # noqa: BLE001
            return CaptureResult(False, f"Screen capture failed: {exc}")

    def vision_prompt(self, question: str, capture: CaptureResult) -> str:
        """Build a text prompt that references a local capture for Hermes/vision backends."""
        if not capture.ok or not capture.path:
            return f"{question}\n\n(No screenshot available: {capture.message})"
        data_url = capture.as_data_url() or ""
        # Keep prompt useful even for text-only models by including path + short metadata.
        return (
            f"{question}\n\n"
            f"[Screenshot attached]\n"
            f"path: {capture.path}\n"
            f"mime: {capture.mime}\n"
            f"data_url_prefix: {data_url[:64]}...(truncated)\n"
            "Describe what is visible and answer the question."
        )

    @staticmethod
    def _grab():
        try:
            import mss
            from PIL import Image

            with mss.mss() as sct:
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                shot = sct.grab(monitor)
                return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        except Exception:
            from PIL import ImageGrab

            image = ImageGrab.grab()
            if image is None:
                raise RuntimeError("ImageGrab returned no image")
            return image.convert("RGB")
