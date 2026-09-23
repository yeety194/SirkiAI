# SirkiAI Architecture

Modular desktop assistant with explicit permission gates.

| Module | Role |
|---|---|
| `app/ui.py` | PySide6 chat window, commands, consent dialogs, reminder popup |
| `app/worker.py` | Background Hermes chat + consent bridge to UI thread |
| `app/hermes.py` | HTTP adapter, history, tool-calling loop |
| `app/tools.py` | Allowlisted tool surface + OpenAI-style tool schemas |
| `app/memory.py` | Opt-in SQLite memories |
| `app/reminders.py` | Local reminder store + duration parser |
| `app/screen.py` | Screenshot capture + vision prompt helper |
| `app/speech.py` | Push-to-talk speech recognition wrapper |
| `app/automation.py` | Hardened keyboard/mouse allowlist |
| `app/voice.py` | Optional TTS |
| `app/config.py` | `.env` feature flags |

## Safety model

1. Feature flags default to safe values (`MEMORY_ENABLED=false`, `AUTOMATION_ENABLED=false`, `SPEECH_ENABLED=false`).
2. Tools are allowlisted in `DesktopTools.ALLOWED` / `DesktopAutomation.ALLOWED`.
3. Every desktop action asks for consent (`QMessageBox`) before running.
4. Model tool calls go through the same consent path via `ChatWorker.consent_requested`.
5. Credentials stay in `.env` (gitignored). Demo mode works without Hermes.

## Request flow

```
User input / Talk / Capture
  ├─ /command → permission prompt → DesktopTools / Memory / Reminders / Automation
  └─ free text → ChatWorker
        → HermesClient (+ tools schemas)
        → optional tool_calls → UI consent → tool result → continue rounds
        → final assistant text → UI (+ optional Voice)
```

## Local brain

Sirki resolves a brain target via `app/brain.py`:

1. `BRAIN_MODE=local` → Ollama at `LOCAL_BRAIN_URL` (default `http://127.0.0.1:11434/v1`)
2. `remote` → `HERMES_BASE_URL` + API key
3. `demo` → no model calls

The Windows one-file build is `packaging/sirkiai.spec` → `Sirki.exe`, produced by GitHub Actions or `packaging/build_windows.ps1`.
