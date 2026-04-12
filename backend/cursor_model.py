"""
cursor_model.py — QAbstractListModel for the live TUIO object monitor table.

Holds one entry per active session ID (cursor or object). Updated from the
Qt main thread via update() which is called by BridgeController via a Qt signal.
"""

import time
from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, QByteArray


class CursorModel(QAbstractListModel):
    """
    Roles exposed to QML:
      sessionId, objectType, x, y, xVel, yVel, accel, angle, classId, lifetime
    """

    # Custom role IDs
    SESSION_ID  = Qt.UserRole + 1
    OBJECT_TYPE = Qt.UserRole + 2
    X           = Qt.UserRole + 3
    Y           = Qt.UserRole + 4
    X_VEL       = Qt.UserRole + 5
    Y_VEL       = Qt.UserRole + 6
    ACCEL       = Qt.UserRole + 7
    ANGLE       = Qt.UserRole + 8
    CLASS_ID    = Qt.UserRole + 9
    LIFETIME    = Qt.UserRole + 10

    _ROLE_NAMES = {
        SESSION_ID:  b"sessionId",
        OBJECT_TYPE: b"objectType",
        X:           b"posX",
        Y:           b"posY",
        X_VEL:       b"xVel",
        Y_VEL:       b"yVel",
        ACCEL:       b"accel",
        ANGLE:       b"angle",
        CLASS_ID:    b"classId",
        LIFETIME:    b"lifetime",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Ordered list of session IDs for stable row indexing
        self._order: list[int] = []
        # Data store: sid → row dict
        self._rows: dict[int, dict[str, Any]] = {}
        # First-seen timestamps for lifetime calculation
        self._first_seen: dict[int, float] = {}

    # -----------------------------------------------------------------------
    # QAbstractListModel interface
    # -----------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._order)

    def roleNames(self) -> dict[int, QByteArray]:
        return {k: QByteArray(v) for k, v in self._ROLE_NAMES.items()}

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._order):
            return None
        sid = self._order[index.row()]
        row = self._rows.get(sid)
        if row is None:
            return None

        match role:
            case self.SESSION_ID:  return sid
            case self.OBJECT_TYPE: return row.get("type", "cursor")
            case self.X:           return round(row.get("x", 0.0), 4)
            case self.Y:           return round(row.get("y", 0.0), 4)
            case self.X_VEL:       return round(row.get("x_vel", 0.0), 4)
            case self.Y_VEL:       return round(row.get("y_vel", 0.0), 4)
            case self.ACCEL:       return round(row.get("accel", 0.0), 4)
            case self.ANGLE:       return round(row.get("angle", 0.0), 4)
            case self.CLASS_ID:    return row.get("class_id", -1)
            case self.LIFETIME:
                age = time.monotonic() - self._first_seen.get(sid, time.monotonic())
                return round(age, 1)
            case _:
                return None

    # -----------------------------------------------------------------------
    # Public update API (call from Qt main thread only)
    # -----------------------------------------------------------------------

    def update(self, frame: dict) -> None:
        """
        Process a TUIO frame dict (from BridgeController via queued signal).
        Adds new rows, updates existing rows, removes gone rows.
        """
        now = time.monotonic()

        # --- add / update cursors ---
        for sid, cur in frame.get("cursors", {}).items():
            self._upsert(sid, {
                "type": "cursor", "class_id": -1,
                "x": cur["x"], "y": cur["y"],
                "x_vel": cur["x_vel"], "y_vel": cur["y_vel"],
                "accel": cur["accel"], "angle": 0.0,
            }, now)

        # --- add / update objects ---
        for sid, obj in frame.get("objects", {}).items():
            self._upsert(sid, {
                "type": "object", "class_id": obj["class_id"],
                "x": obj["x"], "y": obj["y"],
                "x_vel": obj["x_vel"], "y_vel": obj["y_vel"],
                "accel": obj["accel"], "angle": obj["angle"],
            }, now)

        # --- add / update blobs ---
        for sid, blb in frame.get("blobs", {}).items():
            self._upsert(sid, {
                "type": "blob", "class_id": -1,
                "x": blb["x"], "y": blb["y"],
                "x_vel": blb["x_vel"], "y_vel": blb["y_vel"],
                "accel": blb["accel"], "angle": blb["angle"],
            }, now)

        # --- remove gone session IDs ---
        for sid in frame.get("removed", frozenset()):
            self._remove(sid)

    def clear(self) -> None:
        """Remove all rows."""
        if not self._order:
            return
        self.beginRemoveRows(QModelIndex(), 0, len(self._order) - 1)
        self._order.clear()
        self._rows.clear()
        self._first_seen.clear()
        self.endRemoveRows()

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _upsert(self, sid: int, row_data: dict, now: float) -> None:
        if sid in self._rows:
            self._rows[sid] = row_data
            row_idx = self._order.index(sid)
            idx = self.index(row_idx, 0)
            self.dataChanged.emit(idx, idx, list(self._ROLE_NAMES.keys()))
        else:
            insert_pos = len(self._order)
            self.beginInsertRows(QModelIndex(), insert_pos, insert_pos)
            self._order.append(sid)
            self._rows[sid] = row_data
            self._first_seen[sid] = now
            self.endInsertRows()

    def _remove(self, sid: int) -> None:
        if sid not in self._rows:
            return
        row_idx = self._order.index(sid)
        self.beginRemoveRows(QModelIndex(), row_idx, row_idx)
        self._order.pop(row_idx)
        del self._rows[sid]
        self._first_seen.pop(sid, None)
        self.endRemoveRows()
