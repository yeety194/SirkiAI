# SirkiAI

SirkiAI is a Windows-first desktop AI helper built with **Python** and **PySide6**, with a pluggable **Hermes Agent** integration.

The kickstart gives you a working chat window, conversation history, demo mode without credentials, permission-gated local tools, and optional text-to-speech.

## Quick start (Windows)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m app
```

## Quick start (macOS / Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app
```

Configure `HERMES_BASE_URL`, `HERMES_API_KEY`, and `HERMES_MODEL` in `.env`. Without those values, the app runs in **demo mode**.

## What you get today

- Desktop chat UI with async Hermes requests (UI stays responsive)
- Conversation history + `/reset`
- Hermes-compatible HTTP client (`/chat/completions` style)
- Permission-gated starter tools: `/sysinfo`, `/open`, `/url`
- Optional text-to-speech via `VOICE_ENABLED=true`

## Starter commands

| Command | Action |
|---|---|
| `/help` | Show commands |
| `/sysinfo` | System info (asks permission) |
| `/open [path]` | Open a local file/folder (asks permission) |
| `/url [https://...]` | Open a URL (asks permission) |
| `/clear` | Clear the chat view |
| `/reset` | Reset conversation history |

## Project layout

```
app/
  app.py        # entrypoint
  ui.py         # PySide6 chat window
  hermes.py     # Hermes HTTP adapter + history
  tools.py      # permission-gated desktop tools
  voice.py      # optional TTS
  worker.py     # background chat worker
  config.py     # env settings
docs/
  architecture.md
  roadmap.md
tests/
  test_core.py
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Next up

Screen understanding, speech recognition, keyboard/mouse automation, reminders, and persistent memory. See [docs/roadmap.md](docs/roadmap.md). Tool execution should remain permission-gated and allowlisted before anything is exposed to the model.
