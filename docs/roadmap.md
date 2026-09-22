# SirkiAI Roadmap

## Done

- [x] PySide6 chat shell
- [x] Hermes-compatible HTTP client
- [x] Demo mode without credentials
- [x] Conversation history
- [x] Async chat worker
- [x] Permission-gated `/sysinfo`, `/open`, `/url`
- [x] Optional TTS hook
- [x] Unit smoke tests
- [x] Persistent local memory (SQLite) with explicit opt-in (`MEMORY_ENABLED`)
- [x] Model tool-calling bridge with per-tool consent
- [x] Speech recognition push-to-talk (`SPEECH_ENABLED` + Talk button)
- [x] Screen capture + vision prompt helper (`/capture`, `/ask-screen`)
- [x] Reminders / local scheduler (`/remind`, timer poll)
- [x] Keyboard/mouse automation behind a hardened allowlist (`AUTOMATION_ENABLED`)
- [x] Windows installer packaging brief + PyInstaller spec (`docs/packaging.md`)

## Principles

- Prefer small modules over a monolith.
- Never grant silent desktop control.
- Keep Hermes swappable behind `HermesClient`.
- Ship demo mode so contributors can run the UI without API keys.
