"""
main.py — TUIO Bridge entry point.

Creates the QML application engine and exposes the BridgeController as 'Bridge'
in the QML context. Cleans up on exit (saves config, stops threads).
"""

import logging
import os
import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl

# Configure logging before importing backend so module-level loggers work
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

from backend.bridge_controller import BridgeController  # noqa: E402


def main() -> int:
    # High-DPI support (default in Qt6, but explicit for clarity)
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")

    app = QGuiApplication(sys.argv)
    app.setApplicationName("TUIO Bridge")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("TUIO Bridge")

    # Create backend controller
    controller = BridgeController()

    # Set up QML engine
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("Bridge", controller)

    # Load QML — works both from source and when packaged with PyInstaller
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    qml_path = os.path.join(base, "qml", "Main.qml")
    engine.load(QUrl.fromLocalFile(qml_path))

    if not engine.rootObjects():
        logging.critical("Failed to load QML — check qml/Main.qml")
        return 1

    # Auto-start bridge on launch
    controller.startBridge()

    result = app.exec()

    # Graceful shutdown: save config, stop threads
    controller.saveConfig()
    controller.stopBridge()

    return result


if __name__ == "__main__":
    sys.exit(main())
