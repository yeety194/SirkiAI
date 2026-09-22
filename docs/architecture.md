# SirkiAI Architecture

The starter is intentionally small and modular:

- `app/ui.py` — PySide6 desktop chat window
- `app/hermes.py` — Hermes Agent HTTP adapter
- `app/tools.py` — local desktop capability boundary
- `app/config.py` — environment configuration

Planned modules include speech recognition, screen capture, keyboard/mouse automation, reminders, and persistent memory. These should be added behind explicit permission prompts and a tool allowlist rather than being enabled implicitly.
