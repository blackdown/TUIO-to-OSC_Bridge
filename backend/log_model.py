"""
log_model.py — QAbstractListModel for the scrolling OSC message log.

Throttles display to one entry per unique address per 100 ms to prevent
flooding. Caps list at 500 entries (drops oldest). Supports a text filter.
"""

import time
from collections import deque
from typing import Any

from PySide6.QtCore import (
    QAbstractListModel, QModelIndex, Qt, QByteArray, Slot, Property, Signal
)


class LogModel(QAbstractListModel):
    """
    Roles exposed to QML:
      address (str), value (str), timestamp (str)
    """

    ADDRESS   = Qt.UserRole + 1
    VALUE     = Qt.UserRole + 2
    TIMESTAMP = Qt.UserRole + 3

    _ROLE_NAMES = {
        ADDRESS:   b"address",
        VALUE:     b"value",
        TIMESTAMP: b"timestamp",
    }

    MAX_ENTRIES      = 500
    THROTTLE_SECONDS = 0.1   # one entry per address per 100 ms

    filterChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # All entries (possibly more than what's shown after filter)
        self._entries: deque[dict] = deque(maxlen=self.MAX_ENTRIES)
        # Visible entries (after filter applied)
        self._visible: list[dict] = []
        # Last-seen timestamps per address for throttling
        self._last_seen: dict[str, float] = {}
        self._filter: str = ""
        self._paused: bool = False

    # -----------------------------------------------------------------------
    # QAbstractListModel interface
    # -----------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._visible)

    def roleNames(self) -> dict[int, QByteArray]:
        return {k: QByteArray(v) for k, v in self._ROLE_NAMES.items()}

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._visible):
            return None
        entry = self._visible[index.row()]
        match role:
            case self.ADDRESS:   return entry["address"]
            case self.VALUE:     return entry["value"]
            case self.TIMESTAMP: return entry["timestamp"]
            case _:              return None

    # -----------------------------------------------------------------------
    # Public API (call from Qt main thread via queued signal)
    # -----------------------------------------------------------------------

    def add_entry(self, address: str, value: object) -> None:
        """Add a log entry with throttling. Call from Qt main thread."""
        if self._paused:
            return
        now = time.monotonic()
        last = self._last_seen.get(address, 0.0)
        if now - last < self.THROTTLE_SECONDS:
            return
        self._last_seen[address] = now

        entry = {
            "address":   address,
            "value":     self._format_value(value),
            "timestamp": time.strftime("%H:%M:%S"),
        }
        self._entries.append(entry)
        self._rebuild_visible()

    @Slot()
    def clear(self) -> None:
        self.beginResetModel()
        self._entries.clear()
        self._visible.clear()
        self._last_seen.clear()
        self.endResetModel()

    @Slot(bool)
    def setPaused(self, paused: bool) -> None:
        self._paused = paused

    @Slot(str)
    def setFilter(self, text: str) -> None:
        self._filter = text.strip().lower()
        self._rebuild_visible()
        self.filterChanged.emit()

    @Property(str, notify=filterChanged)
    def filter(self) -> str:
        return self._filter

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _rebuild_visible(self) -> None:
        """Refilter _entries → _visible and reset the model."""
        f = self._filter
        if f:
            new_visible = [e for e in self._entries if f in e["address"].lower()]
        else:
            new_visible = list(self._entries)

        self.beginResetModel()
        self._visible = new_visible
        self.endResetModel()

    @staticmethod
    def _format_value(value: object) -> str:
        if isinstance(value, float):
            return f"{value:.4f}"
        if isinstance(value, list):
            return ", ".join(
                f"{v:.4f}" if isinstance(v, float) else str(v) for v in value
            )
        return str(value)
