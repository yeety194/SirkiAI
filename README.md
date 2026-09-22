# SirkiAI

SirkiAI is a Windows desktop AI helper built with Python and PySide6, with a pluggable Hermes Agent integration.

## Quick start

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m app
```

Configure `HERMES_BASE_URL`, `HERMES_API_KEY`, and `HERMES_MODEL` in `.env`. Without those values, the app runs in demo mode.

## Initial capabilities

- Desktop chat UI
- Hermes-compatible HTTP client
- Safe starter hooks for launching apps and opening files
- Optional Windows text-to-speech

Screen understanding, speech recognition, keyboard/mouse automation, reminders, and persistent memory are planned next. Tool execution should remain permission-gated before being exposed to the model.
