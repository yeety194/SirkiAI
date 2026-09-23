# SirkiAI

Windows-first desktop AI helper (Python + PySide6) with a **local Hermes brain** via Ollama, plus optional remote Hermes.

## Fast path (Windows exe)

1. Download the **Sirki-windows** artifact from GitHub Actions (or build with `.\packaging\build_windows.ps1`)
2. Run `start_local_brain.ps1` once
3. Launch `Sirki.exe`

Details: [docs/local-brain.md](docs/local-brain.md) · [docs/packaging.md](docs/packaging.md)

## Dev quick start

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
.\scripts\start_local_brain.ps1
python -m app
```

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
./scripts/start_local_brain.sh
python -m app
```

`.env` defaults to `BRAIN_MODE=local` → `http://127.0.0.1:11434/v1` + `hermes3:3b`.

## Feature flags

| Flag | Default | Purpose |
|---|---|---|
| `BRAIN_MODE` | local | `auto` / `local` / `remote` / `demo` |
| `LOCAL_BRAIN_MODEL` | hermes3:3b | Ollama model tag |
| `MEMORY_ENABLED` | false | Opt-in SQLite memory |
| `REMINDERS_ENABLED` | true | Local reminders |
| `SCREEN_ENABLED` | true | Screenshots / ask-screen |
| `SPEECH_ENABLED` | false | Push-to-talk |
| `AUTOMATION_ENABLED` | false | Keyboard/mouse allowlist |
| `TOOL_CALLING_ENABLED` | true | Tool-calling bridge |
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
| `/ask-screen [q]` | Capture + ask brain |
| `/type [text]` | Type text (automation) |
| `/hotkey [ctrl+c]` | Hotkey (automation) |
| `/click x,y` | Click (automation) |
| `/clear` | Clear chat view |
| `/reset` | Reset conversation |

## Layout

```
app/           application modules
docs/          architecture, local brain, packaging
packaging/     PyInstaller spec → Sirki.exe
scripts/       start local Ollama brain
tests/         unit smoke tests
```

## Tests

```bash
python -m unittest discover -s tests -v
```
