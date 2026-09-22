from __future__ import annotations

import os
import platform
import subprocess


class DesktopTools:
    @staticmethod
    def system_info() -> dict[str, str]:
        return {"system": platform.system(), "release": platform.release()}

    @staticmethod
    def launch(path: str) -> str:
        try:
            if os.name == "nt":
                os.startfile(path)
            else:
                subprocess.Popen([path])
            return f"Launched: {path}"
        except OSError as exc:
            return f"Could not launch {path}: {exc}"
