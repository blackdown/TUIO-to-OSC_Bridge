"""
bridge_controller.py — Root QML-exposed object that wires all backend components.

Exposed to QML as 'Bridge' via engine.rootContext().setContextProperty().
Owns the ConfigManager, TUIOReceiver, BridgeEngine, CursorModel and LogModel.

Qt signals are used for all cross-thread communication:
  - BridgeEngine callbacks emit signals → Qt queues them → main thread handles
"""

import logging
import queue

from PySide6.QtCore import (
    QObject, Signal, Slot, Property, QTimer, Qt
)

from .config_manager import ConfigManager
from .tuio_receiver import TUIOReceiver
from .bridge_engine import BridgeEngine
from .cursor_model import CursorModel
from .log_model import LogModel

logger = logging.getLogger(__name__)


class BridgeController(QObject):
    """
    Exposed to QML as 'Bridge'.

    Properties (read from QML):
      cursorModel   — CursorModel
      logModel      — LogModel
      status        — str: "Listening" | "Stopped" | "Error: ..."
      activeCount   — int
      msgPerSec     — float
      errorCount    — int
      isRunning     — bool
      config        — dict (full config snapshot for QML bindings)

    Signals (QML-visible):
      statusChanged(str)
      statsChanged(int activeCount, float msgPerSec)
      errorCountChanged(int)
      configChanged()
      isRunningChanged(bool)

    Slots (callable from QML):
      startBridge()
      stopBridge()
      saveConfig()
      loadConfig()
      sendTestMessage(int targetIndex)
      setTuioPort(int)
      setTuioAddress(str)
      setTuioProfile(str)
      setTuioMaxObjects(int)
      setAddressTemplate(str)
      setTargetIp(int index, str ip)
      setTargetPort(int index, int port)
      setTargetEnabled(int index, bool enabled)
      setTargetFlipX(int index, bool v)
      setTargetFlipY(int index, bool v)
      setTargetSwapAxes(int index, bool v)
      setTargetScaleX(int index, float v)
      setTargetScaleY(int index, float v)
      setTargetOffsetX(int index, float v)
      setTargetOffsetY(int index, float v)
    """

    # Signals
    statusChanged      = Signal(str)
    statsChanged       = Signal(int, float)   # activeCount, msgPerSec
    errorCountChanged  = Signal(int)
    configChanged      = Signal()
    isRunningChanged   = Signal(bool)

    # Internal signals for thread-safe cross-thread callbacks
    _stateUpdatedSignal = Signal(object)       # frame dict
    _oscSentSignal      = Signal(str, object)  # address, value
    _statsUpdatedSignal = Signal(int, float)   # active, mps
    _errorSignal        = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self._config_mgr = ConfigManager()
        self._config_mgr.load()

        self._frame_queue: queue.Queue = queue.Queue(maxsize=512)
        self._cursor_model = CursorModel(self)
        self._log_model = LogModel(self)

        self._receiver = TUIOReceiver(
            frame_queue=self._frame_queue,
            profile=self._config_mgr.get("tuio_input", "profile", default="both"),
            max_objects=self._config_mgr.get("tuio_input", "max_objects", default=20),
            on_error=self._on_receiver_error,
        )

        self._engine = BridgeEngine(
            frame_queue=self._frame_queue,
            on_state_updated=self._on_state_updated,
            on_osc_sent=self._on_osc_sent,
            on_stats_updated=self._on_stats_updated,
        )
        self._engine.configure(self._config_mgr.config)

        self._status: str = "Stopped"
        self._active_count: int = 0
        self._msg_per_sec: float = 0.0
        self._error_count: int = 0
        self._is_running: bool = False

        # Periodic GUI refresh timer (50 ms → 20 fps for lifetime column)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(50)
        self._refresh_timer.timeout.connect(self._refresh_lifetimes)

        # Wire internal cross-thread signals → main thread slots
        self._stateUpdatedSignal.connect(self._handle_state_update, Qt.QueuedConnection)
        self._oscSentSignal.connect(self._handle_osc_sent, Qt.QueuedConnection)
        self._statsUpdatedSignal.connect(self._handle_stats_update, Qt.QueuedConnection)
        self._errorSignal.connect(self._handle_error, Qt.QueuedConnection)

    # -----------------------------------------------------------------------
    # Properties exposed to QML
    # -----------------------------------------------------------------------

    @Property(QObject, constant=True)
    def cursorModel(self) -> CursorModel:
        return self._cursor_model

    @Property(QObject, constant=True)
    def logModel(self) -> LogModel:
        return self._log_model

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(int, notify=statsChanged)
    def activeCount(self) -> int:
        return self._active_count

    @Property(float, notify=statsChanged)
    def msgPerSec(self) -> float:
        return self._msg_per_sec

    @Property(int, notify=errorCountChanged)
    def errorCount(self) -> int:
        return self._error_count

    @Property(bool, notify=isRunningChanged)
    def isRunning(self) -> bool:
        return self._is_running

    @Property("QVariant", notify=configChanged)
    def config(self) -> dict:
        return self._config_mgr.config

    # -----------------------------------------------------------------------
    # Slots callable from QML
    # -----------------------------------------------------------------------

    @Slot()
    def startBridge(self) -> None:
        if self._is_running:
            return
        cfg = self._config_mgr.config
        host = cfg["tuio_input"]["address"]
        port = cfg["tuio_input"]["port"]

        # Recreate receiver with current profile/max_objects settings
        self._receiver = TUIOReceiver(
            frame_queue=self._frame_queue,
            profile=cfg["tuio_input"]["profile"],
            max_objects=cfg["tuio_input"]["max_objects"],
            on_error=self._on_receiver_error,
        )

        ok = self._receiver.start(host, port)
        if not ok:
            return

        self._engine.configure(cfg)
        self._engine.start()
        self._refresh_timer.start()

        self._is_running = True
        self._set_status(f"Listening on {host}:{port}")
        self.isRunningChanged.emit(True)

    @Slot()
    def stopBridge(self) -> None:
        if not self._is_running:
            return
        self._engine.stop()
        self._receiver.stop()
        self._refresh_timer.stop()
        self._cursor_model.clear()

        self._is_running = False
        self._set_status("Stopped")
        self.isRunningChanged.emit(False)

    @Slot()
    def saveConfig(self) -> None:
        self._config_mgr.save()

    @Slot()
    def loadConfig(self) -> None:
        self._config_mgr.load()
        self.configChanged.emit()

    @Slot(int, result=bool)
    def sendTestMessage(self, target_index: int) -> bool:
        return self._engine.send_test_message(target_index)

    # -- TUIO input settings --

    @Slot(int)
    def setTuioPort(self, port: int) -> None:
        self._config_mgr.set(["tuio_input", "port"], max(1, min(65535, port)))
        self.configChanged.emit()

    @Slot(str)
    def setTuioAddress(self, address: str) -> None:
        self._config_mgr.set(["tuio_input", "address"], address)
        self.configChanged.emit()

    @Slot(str)
    def setTuioProfile(self, profile: str) -> None:
        if profile in ("2Dcur", "2Dobj", "both"):
            self._config_mgr.set(["tuio_input", "profile"], profile)
            self.configChanged.emit()

    @Slot(int)
    def setTuioMaxObjects(self, n: int) -> None:
        self._config_mgr.set(["tuio_input", "max_objects"], max(1, min(100, n)))
        self.configChanged.emit()

    # -- OSC output settings --

    @Slot(str)
    def setAddressTemplate(self, template: str) -> None:
        if "{id}" in template:
            self._config_mgr.set(["osc_output", "address_template"], template)
            self.configChanged.emit()

    @Slot(int, str)
    def setTargetIp(self, index: int, ip: str) -> None:
        self._config_mgr.set_target(index, "ip", ip)
        self.configChanged.emit()

    @Slot(int, int)
    def setTargetPort(self, index: int, port: int) -> None:
        self._config_mgr.set_target(index, "port", max(1, min(65535, port)))
        self.configChanged.emit()

    @Slot(int, bool)
    def setTargetEnabled(self, index: int, enabled: bool) -> None:
        self._config_mgr.set_target(index, "enabled", enabled)
        if self._is_running:
            self._engine.configure(self._config_mgr.config)
        self.configChanged.emit()

    @Slot(int, bool)
    def setTargetFlipX(self, index: int, v: bool) -> None:
        self._config_mgr.set_target(index, "flip_x", v)
        self.configChanged.emit()

    @Slot(int, bool)
    def setTargetFlipY(self, index: int, v: bool) -> None:
        self._config_mgr.set_target(index, "flip_y", v)
        self.configChanged.emit()

    @Slot(int, bool)
    def setTargetSwapAxes(self, index: int, v: bool) -> None:
        self._config_mgr.set_target(index, "swap_axes", v)
        self.configChanged.emit()

    @Slot(int, float)
    def setTargetScaleX(self, index: int, v: float) -> None:
        self._config_mgr.set_target(index, "scale_x", v)
        self.configChanged.emit()

    @Slot(int, float)
    def setTargetScaleY(self, index: int, v: float) -> None:
        self._config_mgr.set_target(index, "scale_y", v)
        self.configChanged.emit()

    @Slot(int, float)
    def setTargetOffsetX(self, index: int, v: float) -> None:
        self._config_mgr.set_target(index, "offset_x", v)
        self.configChanged.emit()

    @Slot(int, float)
    def setTargetOffsetY(self, index: int, v: float) -> None:
        self._config_mgr.set_target(index, "offset_y", v)
        self.configChanged.emit()

    # -----------------------------------------------------------------------
    # Cross-thread callbacks → emit internal signals
    # (Called from engine/receiver threads — must not touch Qt objects directly)
    # -----------------------------------------------------------------------

    def _on_state_updated(self, frame: dict) -> None:
        self._stateUpdatedSignal.emit(frame)

    def _on_osc_sent(self, address: str, value: object) -> None:
        self._oscSentSignal.emit(address, value)

    def _on_stats_updated(self, active: int, mps: float) -> None:
        self._statsUpdatedSignal.emit(active, mps)

    def _on_receiver_error(self, msg: str) -> None:
        self._errorSignal.emit(msg)

    # -----------------------------------------------------------------------
    # Main-thread slots (connected via QueuedConnection)
    # -----------------------------------------------------------------------

    def _handle_state_update(self, frame: object) -> None:
        self._cursor_model.update(frame)  # type: ignore[arg-type]

    def _handle_osc_sent(self, address: str, value: object) -> None:
        self._log_model.add_entry(address, value)

    def _handle_stats_update(self, active: int, mps: float) -> None:
        self._active_count = active
        self._msg_per_sec = mps
        self.statsChanged.emit(active, mps)

    def _handle_error(self, msg: str) -> None:
        self._error_count += 1
        self.errorCountChanged.emit(self._error_count)
        self._set_status(f"Error: {msg}")
        if self._is_running:
            self._is_running = False
            self.isRunningChanged.emit(False)

    def _refresh_lifetimes(self) -> None:
        """Nudge the cursor model to refresh lifetime values in the table."""
        if self._cursor_model.rowCount() > 0:
            top = self._cursor_model.index(0, 0)
            bottom = self._cursor_model.index(self._cursor_model.rowCount() - 1, 0)
            self._cursor_model.dataChanged.emit(top, bottom, [CursorModel.LIFETIME])

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _set_status(self, msg: str) -> None:
        if self._status != msg:
            self._status = msg
            self.statusChanged.emit(msg)
