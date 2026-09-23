# Packaging Sirki.exe (Windows)

## One-file exe (recommended)

On a Windows machine:

```powershell
.\packaging\build_windows.ps1
```

Output:

```
dist\Sirki.exe
```

Or rely on GitHub Actions: workflow **Build Sirki.exe** uploads a `Sirki-windows` artifact containing:

- `Sirki.exe`
- `.env` (local brain defaults)
- `start_local_brain.ps1`
- `HOW_TO_RUN.txt`

## Local brain + exe

1. Run `start_local_brain.ps1` once
2. Launch `Sirki.exe`
3. Confirm the subtitle shows `Local brain (hermes3:3b)`

## Notes

- The exe is the desktop shell. The brain runs separately in Ollama.
- Do not bake secrets into the binary; load `.env` beside `Sirki.exe`.
- Antivirus may flag PyInstaller + automation deps; code-sign for distribution.
