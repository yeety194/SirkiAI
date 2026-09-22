# SirkiAI Architecture

The kickstart stays small and modular on purpose:

| Module | Role |
|---|---|
| `app/ui.py` | PySide6 desktop chat window and command handling |
| `app/worker.py` | Moves Hermes chat onto a `QThread` so the UI does not freeze |
| `app/hermes.py` | Hermes-compatible HTTP adapter with local message history |
| `app/tools.py` | Local desktop capability boundary (allowlist + return values) |
| `app/voice.py` | Optional text-to-speech |
| `app/config.py` | Environment configuration via `.env` |

## Safety model

1. **Tools are allowlisted** in `DesktopTools.ALLOWED`.
2. **UI commands ask for permission** before running a tool (`QMessageBox`).
3. **Model-driven tool calling is not enabled yet.** Wire it only after consent prompts and a clear allowlist exist for every action.
4. **Credentials stay in `.env`** (gitignored). Demo mode works with empty Hermes settings.

## Request flow

```
User input
  ├─ /command  → permission prompt → DesktopTools
  └─ free text → ChatWorker (QThread) → HermesClient → UI + optional Voice
```

## Planned modules

Speech recognition, screen capture, keyboard/mouse automation, reminders, and persistent memory should each land as their own module behind the same permission + allowlist pattern.
