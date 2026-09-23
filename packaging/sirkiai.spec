# -*- mode: python ; coding: utf-8 -*-
"""One-file Windows build: dist/Sirki.exe"""

import os

from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None
root = os.path.abspath(os.path.join(SPECPATH, ".."))

datas = collect_data_files("dotenv")
datas += [(os.path.join(root, ".env.example"), ".")]

binaries = []
hiddenimports = [
    "PySide6",
    "dotenv",
    "requests",
    "pyttsx3",
    "speech_recognition",
    "mss",
    "PIL",
    "pyautogui",
    "app",
    "app.app",
    "app.brain",
    "app.config",
    "app.hermes",
    "app.tools",
    "app.ui",
    "app.worker",
    "app.memory",
    "app.reminders",
    "app.screen",
    "app.speech",
    "app.automation",
    "app.voice",
]

tmp_ret = collect_all("PySide6")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    [os.path.join(root, "app", "__main__.py")],
    pathex=[root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Sirki",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
