"""
serial_writer.py — JSON-lines serial output for TUIO Bridge.

Each OSC message is written as a compact JSON line:
    {"a":"/tuio/cursor/0/x","v":0.42}\n

The writer owns a daemon thread that drains a queue so that callers
(engine thread) never block on serial I/O.
"""

import json
import logging
import queue
import threading

logger = logging.getLogger(__name__)

try:
    import serial
    import serial.tools.list_ports
    _SERIAL_AVAILABLE = True
except ImportError:
    _SERIAL_AVAILABLE = False
    logger.warning("pyserial not installed — serial output unavailable")


class SerialWriter:
    """Thread-safe serial JSON-lines writer."""

    QUEUE_MAXSIZE = 1024

    def __init__(self) -> None:
        self._port: str = ""
        self._baud: int = 115200
        self._ser = None
        self._thread: threading.Thread | None = None
        self._queue: queue.Queue = queue.Queue(maxsize=self.QUEUE_MAXSIZE)
        self._stop_event = threading.Event()
        self._lock = threading.Lock()  # guards _ser open/close vs send

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def configure(self, config: dict) -> None:
        """Apply serial_output section from config. Opens or closes port as needed."""
        sc = config.get("serial_output", {})
        enabled = sc.get("enabled", False)
        port = sc.get("port", "")
        baud = int(sc.get("baud_rate", 115200))

        if not enabled or not port:
            self._close()
            return

        if port != self._port or baud != self._baud or self._ser is None:
            self._close()
            self._port = port
            self._baud = baud
            self._open()

    def send(self, address: str, value: object) -> None:
        """Enqueue one message. Non-blocking; drops silently if queue is full or port not open."""
        if self._ser is None:
            return
        try:
            self._queue.put_nowait({"a": address, "v": value})
        except queue.Full:
            pass

    def stop(self) -> None:
        self._close()

    @staticmethod
    def list_ports() -> list[str]:
        """Return a list of available serial port device names."""
        if not _SERIAL_AVAILABLE:
            return []
        return sorted(p.device for p in serial.tools.list_ports.comports())

    # -----------------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------------

    def _open(self) -> None:
        if not _SERIAL_AVAILABLE:
            logger.error("Cannot open serial port — pyserial is not installed")
            return
        try:
            ser = serial.Serial(self._port, self._baud, timeout=1)
        except serial.SerialException as exc:
            logger.error("Serial: cannot open %s at %d baud: %s", self._port, self._baud, exc)
            return

        with self._lock:
            self._ser = ser

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="serial-writer",
            daemon=True,
        )
        self._thread.start()
        logger.info("Serial output open: %s at %d baud", self._port, self._baud)

    def _close(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        with self._lock:
            if self._ser is not None:
                try:
                    self._ser.close()
                except Exception:
                    pass
                self._ser = None
        logger.info("Serial output closed")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                msg = self._queue.get(timeout=0.05)
            except queue.Empty:
                continue

            line = json.dumps(msg, separators=(",", ":")) + "\n"
            encoded = line.encode()

            with self._lock:
                ser = self._ser

            if ser is None:
                break

            try:
                ser.write(encoded)
            except Exception as exc:
                logger.error("Serial write error: %s", exc)
                # Port lost — close and stop the thread
                with self._lock:
                    try:
                        ser.close()
                    except Exception:
                        pass
                    self._ser = None
                break
