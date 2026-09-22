# Packaging SirkiAI for Windows

This brief covers a PyInstaller one-folder (recommended) or one-file build.

## Prerequisites

- Windows 10/11
- Python 3.11+
- `pip install -r requirements.txt pyinstaller`

## One-folder build (easier to debug)

From the repo root:

```powershell
py -3.11 -m PyInstaller packaging/sirkiai.spec
```

Output:

```
dist/SirkiAI/SirkiAI.exe
```

Copy `.env.example` to the same folder as `SirkiAI.exe` and rename to `.env`.

## One-file build

```powershell
py -3.11 -m PyInstaller --noconfirm --windowed --name SirkiAI --collect-all PySide6 app/__main__.py
```

## Notes

- Keep `TOOLS_ENABLED`, `AUTOMATION_ENABLED`, `MEMORY_ENABLED`, and `SPEECH_ENABLED` explicit in `.env`.
- Antivirus tools may flag automation/PyInstaller binaries; code-sign when you distribute.
- Speech and TTS need OS audio devices and optional native backends.
- Do not bake API keys into the binary; always load `.env` at runtime.

## Smoke check after build

1. Launch `SirkiAI.exe`
2. Confirm demo mode without Hermes keys
3. Run `/help`, `/sysinfo`, `/remind in 1m test`
4. Enable Hermes credentials and send one chat turn
