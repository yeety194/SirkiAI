# Local brain (Ollama + Hermes)

SirkiAI defaults to a **local brain** through [Ollama](https://ollama.com) using the OpenAI-compatible API:

```
http://127.0.0.1:11434/v1/chat/completions
```

Default model: `hermes3:3b` (Nous Hermes 3).

## Windows quick start

1. Build or download `Sirki.exe`
2. Run `scripts/start_local_brain.ps1` (or `start_local_brain.ps1` next to the exe)
3. Launch `Sirki.exe`
4. Chat

## macOS / Linux

```bash
chmod +x scripts/start_local_brain.sh
./scripts/start_local_brain.sh
cp .env.example .env   # BRAIN_MODE=local
python -m app
```

## `.env` knobs

```env
BRAIN_MODE=local
LOCAL_BRAIN_URL=http://127.0.0.1:11434/v1
LOCAL_BRAIN_MODEL=hermes3:3b
LOCAL_BRAIN_API_KEY=ollama
```

`BRAIN_MODE` options:

| Value | Behavior |
|---|---|
| `auto` | Prefer reachable Ollama, else remote Hermes, else local defaults |
| `local` | Always use Ollama URL/model |
| `remote` | Use `HERMES_BASE_URL` + `HERMES_API_KEY` |
| `demo` | No model calls |

## Notes

- Ollama ignores the API key; Sirki still sends `ollama` as a placeholder.
- First model pull downloads a few GB; keep the machine online for that step.
- For a stronger local brain later: `LOCAL_BRAIN_MODEL=hermes3` (8B) or `hermes3:70b`.
