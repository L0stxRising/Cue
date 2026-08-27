# -*- mode: python ; coding: utf-8 -*-
# Cue — PyInstaller spec file (single-file)
# Build with:  pyinstaller cue.spec

import sys
from PyInstaller.utils.hooks import collect_submodules

# Collect all pynput backends (they're loaded dynamically)
pynput_hidden = collect_submodules('pynput')

hidden = pynput_hidden + [
    'app', 'backend', 'gui_app', 'handler',
    'PIL', 'PIL.Image', 'PIL.ImageDraw',
    'mss', 'mss.linux', 'mss.windows', 'mss.darwin',
    'dotenv', 'tqdm', 'tqdm.auto',
    'evdev', 'evdev.ecodes',
    'tkinter', 'tkinter.simpledialog', 'tkinter.messagebox',
    'tkinter.scrolledtext',
    'concurrent', 'concurrent.futures',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    datas=[],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Cue',
    debug=False,
    strip=False,
    upx=True,
    console=True,  # Keep console for subprocess stdout piping
    onefile=True,
)
