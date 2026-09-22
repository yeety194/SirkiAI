# SirkiAI Roadmap

## Done (kickstart)

- [x] PySide6 chat shell
- [x] Hermes-compatible HTTP client
- [x] Demo mode without credentials
- [x] Conversation history
- [x] Async chat worker
- [x] Permission-gated `/sysinfo`, `/open`, `/url`
- [x] Optional TTS hook
- [x] Unit smoke tests

## Next

- [ ] Persistent local memory (SQLite) with explicit opt-in
- [ ] Model tool-calling bridge with per-tool consent
- [ ] Speech recognition (push-to-talk)
- [ ] Screen capture + vision prompt helper
- [ ] Reminders / local scheduler
- [ ] Keyboard/mouse automation behind a hardened allowlist
- [ ] Windows installer packaging (PyInstaller / brief)

## Principles

- Prefer small modules over a monolith.
- Never grant silent desktop control.
- Keep Hermes swappable behind `HermesClient`.
- Ship demo mode so contributors can run the UI without API keys.
