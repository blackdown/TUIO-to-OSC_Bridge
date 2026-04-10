"""
tuio_receiver.py — TUIO 1.1 UDP listener and parser.

Runs a ThreadingOSCUDPServer in a daemon thread. Accumulates alive/set/fseq
messages per frame and pushes parsed state dicts onto a queue.Queue for the
BridgeEngine to consume.

Supported profiles: /tuio/2Dcur (cursors) and /tuio/2Dobj (fiducial objects).
"""

import logging
import queue
import threading
from typing import Any, Callable

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

logger = logging.getLogger(__name__)


class TUIOReceiver:
    """
    Listens for TUIO 1.1 OSC bundles and converts them to state dicts.

    Each item pushed to frame_queue is a dict:
    {
        "cursors": {
            session_id (int): {
                "x": float, "y": float,
                "x_vel": float, "y_vel": float, "accel": float
            }, ...
        },
        "objects": {
            session_id (int): {
                "x": float, "y": float, "angle": float,
                "x_vel": float, "y_vel": float, "rot_vel": float,
                "accel": float, "rot_accel": float, "class_id": int
            }, ...
        },
        "added":   frozenset of session_ids newly appeared this frame,
        "removed": frozenset of session_ids that left this frame,
        "frame_id": int,
    }
    """

    def __init__(
        self,
        frame_queue: queue.Queue,
        profile: str = "both",          # "2Dcur" | "2Dobj" | "both"
        max_objects: int = 20,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._frame_queue = frame_queue
        self._profile = profile
        self._max_objects = max_objects
        self._on_error = on_error or (lambda msg: None)

        self._server: ThreadingOSCUDPServer | None = None
        self._server_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Per-frame accumulation buffers (only touched from server thread)
        self._cur_alive: set[int] = set()
        self._obj_alive: set[int] = set()
        self._cursors: dict[int, dict] = {}
        self._objects: dict[int, dict] = {}
        self._prev_alive: set[int] = set()   # combined, for add/remove diff

        self._error_count = 0

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def start(self, host: str = "0.0.0.0", port: int = 3333) -> bool:
        """Start the UDP server in a daemon thread. Returns True on success."""
        if self._server is not None:
            logger.warning("TUIOReceiver already running")
            return True

        dispatcher = Dispatcher()

        if self._profile in ("2Dcur", "both"):
            dispatcher.map("/tuio/2Dcur", self._handle_2Dcur)
        if self._profile in ("2Dobj", "both"):
            dispatcher.map("/tuio/2Dobj", self._handle_2Dobj)

        try:
            self._server = ThreadingOSCUDPServer((host, port), dispatcher)
        except OSError as exc:
            msg = f"Cannot bind TUIO port {port}: {exc}"
            logger.error(msg)
            self._on_error(msg)
            return False

        self._stop_event.clear()
        self._server_thread = threading.Thread(
            target=self._serve_forever,
            name="tuio-receiver",
            daemon=True,
        )
        self._server_thread.start()
        logger.info("TUIO receiver listening on %s:%d (profile: %s)", host, port, self._profile)
        return True

    def stop(self) -> None:
        """Stop the UDP server and join the thread."""
        self._stop_event.set()
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._server_thread is not None:
            self._server_thread.join(timeout=2.0)
            self._server_thread = None
        logger.info("TUIO receiver stopped")

    @property
    def error_count(self) -> int:
        return self._error_count

    # -----------------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------------

    def _serve_forever(self) -> None:
        assert self._server is not None
        self._server.serve_forever()

    # ---- /tuio/2Dcur handler -----------------------------------------------

    def _handle_2Dcur(self, address: str, *args: Any) -> None:
        if not args:
            return
        msg_type = args[0]
        try:
            match msg_type:
                case "alive":
                    # alive  s_id0 s_id1 ...
                    self._cur_alive = set(int(a) for a in args[1:])
                    # Purge entries that left
                    for sid in list(self._cursors):
                        if sid not in self._cur_alive:
                            del self._cursors[sid]

                case "set":
                    # set  s_id  x  y  x_vel  y_vel  m_acc
                    if len(args) >= 7:
                        sid = int(args[1])
                        if len(self._cursors) < self._max_objects or sid in self._cursors:
                            self._cursors[sid] = {
                                "x":     float(args[2]),
                                "y":     float(args[3]),
                                "x_vel": float(args[4]),
                                "y_vel": float(args[5]),
                                "accel": float(args[6]),
                            }

                case "fseq":
                    # fseq  frame_id  — marks end of bundle; emit frame
                    frame_id = int(args[1]) if len(args) >= 2 else -1
                    self._maybe_emit(frame_id)

                case "source":
                    pass  # informational; ignore
        except Exception as exc:
            self._error_count += 1
            logger.debug("2Dcur parse error: %s", exc)

    # ---- /tuio/2Dobj handler -----------------------------------------------

    def _handle_2Dobj(self, address: str, *args: Any) -> None:
        if not args:
            return
        msg_type = args[0]
        try:
            match msg_type:
                case "alive":
                    self._obj_alive = set(int(a) for a in args[1:])
                    for sid in list(self._objects):
                        if sid not in self._obj_alive:
                            del self._objects[sid]

                case "set":
                    # set  s_id  class_id  x  y  angle  x_vel  y_vel  rot_vel  m_acc  rot_acc
                    if len(args) >= 11:
                        sid = int(args[1])
                        if len(self._objects) < self._max_objects or sid in self._objects:
                            self._objects[sid] = {
                                "class_id": int(args[2]),
                                "x":        float(args[3]),
                                "y":        float(args[4]),
                                "angle":    float(args[5]),
                                "x_vel":    float(args[6]),
                                "y_vel":    float(args[7]),
                                "rot_vel":  float(args[8]),
                                "accel":    float(args[9]),
                                "rot_accel": float(args[10]),
                            }

                case "fseq":
                    frame_id = int(args[1]) if len(args) >= 2 else -1
                    self._maybe_emit(frame_id)

                case "source":
                    pass
        except Exception as exc:
            self._error_count += 1
            logger.debug("2Dobj parse error: %s", exc)

    # ---- Frame assembly ----------------------------------------------------

    def _maybe_emit(self, frame_id: int) -> None:
        """Build and push a state frame onto the queue."""
        current_alive = self._cur_alive | self._obj_alive
        added   = current_alive - self._prev_alive
        removed = self._prev_alive - current_alive
        self._prev_alive = current_alive

        frame = {
            "cursors":  dict(self._cursors),   # shallow copy is fine — values are replaced each set
            "objects":  dict(self._objects),
            "added":    frozenset(added),
            "removed":  frozenset(removed),
            "frame_id": frame_id,
        }
        try:
            self._frame_queue.put_nowait(frame)
        except queue.Full:
            logger.debug("Frame queue full — dropping frame %d", frame_id)
