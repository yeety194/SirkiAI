# SirkiAI

SirkiAI is a Windows-first desktop AI helper built with **Python** and **PySide6**, with a pluggable **Hermes Agent** integration.

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

## Feature flags

| Flag | Default | Purpose |
|---|---|---|
| `MEMORY_ENABLED` | false | Opt-in SQLite memory |
| `REMINDERS_ENABLED` | true | Local reminders |
| `SCREEN_ENABLED` | true | Screenshots / ask-screen |
| `SPEECH_ENABLED` | false | Push-to-talk |
| `AUTOMATION_ENABLED` | false | Keyboard/mouse allowlist |
| `TOOL_CALLING_ENABLED` | true | Hermes tool-calling bridge |
| `VOICE_ENABLED` | false | TTS replies |

## Commands

| Command | Action |
|---|---|
| `/help` | Show commands |
| `/sysinfo` | System info |
| `/open [path]` | Open file/folder |
| `/url [https://...]` | Open URL |
| `/remember key=value` | Store memory |
| `/recall [query]` | Search memories |
| `/forget <id>` | Delete memory |
| `/remind in 10m text` | Schedule reminder |
| `/reminders` | List reminders |
| `/cancel <id>` | Cancel reminder |
| `/capture` | Screenshot |
| `/ask-screen [q]` | Capture + ask Hermes |
| `/type [text]` | Type text (automation) |
| `/hotkey [ctrl+c]` | Hotkey (automation) |
| `/click x,y` | Click (automation) |
| `/clear` | Clear chat view |
| `/reset` | Reset conversation |

Use the **Talk** button for push-to-talk when `SPEECH_ENABLED=true`.

## Layout

```
app/           application modules
docs/          architecture, roadmap, packaging
packaging/     PyInstaller spec + Windows build script
tests/         unit smoke tests
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Packaging

See [docs/packaging.md](docs/packaging.md).
