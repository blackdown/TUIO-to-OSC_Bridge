# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for TUIO Bridge.
Build with:  .venv\\Scripts\\pyinstaller tuio_bridge.spec
Output:      dist\\TUIO Bridge\\TUIO Bridge.exe  (one-folder, instant launch)
"""

import os
from pathlib import Path
import PySide6

PYSIDE6_DIR = Path(PySide6.__file__).parent

# ── QML files bundled as data ──────────────────────────────────────────────
qml_datas = [
    ("qml", "qml"),          # entire qml/ tree → _MEIPASS/qml/
    ("assets", "assets"),    # icon.ico etc.   → _MEIPASS/assets/
]

# ── PySide6 QML plugin directories needed at runtime ──────────────────────
# Qt Quick, Controls (Material), Layouts, Window, etc.
pyside6_qml_imports = [
    "QtQuick",
    "QtQuick/Controls",
    "QtQuick/Controls/Material",
    "QtQuick/Controls/Material/impl",
    "QtQuick/Layouts",
    "QtQuick/Templates",
    "QtQuick/Window",
    # "QtQuick/LocalStorage" — not used (no SQLite storage)
]

qt_qml_datas = []
qml_base = PYSIDE6_DIR / "qml"
for imp in pyside6_qml_imports:
    src = qml_base / imp.replace("/", os.sep)
    if src.exists():
        qt_qml_datas.append((str(src), f"PySide6/qml/{imp}"))

# ── PySide6 platform / imageformat plugins ─────────────────────────────────
plugin_dirs = [
    "platforms",     # required — windows platform plugin
    "scenegraph",    # required — Qt Quick renderer
    # "imageformats" — not needed (no image files displayed)
    # "iconengines"  — not needed (no SVG icons)
    # "styles"       — not needed (QML, not Qt Widgets)
    # "tls"          — not needed (no HTTPS)
    # "networkinformation" — not needed
]
plugin_datas = []
plugins_base = PYSIDE6_DIR / "plugins"
for pd in plugin_dirs:
    src = plugins_base / pd
    if src.exists():
        plugin_datas.append((str(src), f"PySide6/plugins/{pd}"))

all_datas = qml_datas + qt_qml_datas + plugin_datas

# ── Hidden imports that PyInstaller misses ─────────────────────────────────
hidden = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickControls2",
    "PySide6.QtNetwork",
    "PySide6.QtOpenGL",
    "pythonosc",
    "pythonosc.dispatcher",
    "pythonosc.osc_server",
    "pythonosc.udp_client",
    "backend",
    "backend.bridge_controller",
    "backend.bridge_engine",
    "backend.config_manager",
    "backend.cursor_model",
    "backend.log_model",
    "backend.tuio_receiver",
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=all_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "matplotlib", "numpy", "scipy", "PIL",
        "PyQt5", "PyQt6", "wx",
        "xmlrpc", "email", "html", "http", "urllib",
        "unittest", "pdb", "doctest", "difflib",
        "ftplib", "imaplib", "poplib", "smtplib", "telnetlib",
        "curses", "readline",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TUIO Bridge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # UPX can break Qt DLLs
    console=False,       # no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="TUIO Bridge",
)
