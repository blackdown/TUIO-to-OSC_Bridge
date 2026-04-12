"""
tuio_receiver.py — TUIO 1.1 UDP listener and parser.

Runs a ThreadingOSCUDPServer in a daemon thread. Accumulates alive/set/fseq
messages per frame and pushes parsed state dicts onto a queue.Queue for the
BridgeEngine to consume.

Supported profiles:
  2D:   /tuio/2Dcur  /tuio/2Dobj  /tuio/2Dblb
  2.5D: /tuio/25Dcur /tuio/25Dobj /tuio/25Dblb
  3D:   /tuio/3Dcur  /tuio/3Dobj  /tuio/3Dblb
"""

import logging
import queue
import threading
import time
from typing import Any, Callable

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

logger = logging.getLogger(__name__)


class TUIOReceiver:
    """
    Listens for TUIO 1.1 OSC bundles and converts them to state dicts.

    Each item pushed to frame_queue is a dict:
    {
        "cursors": { session_id: {"x","y","z","x_vel","y_vel","z_vel","accel"} },
        "objects": { session_id: {"x","y","z","angle","x_vel","y_vel","z_vel",
                                  "rot_vel","accel","rot_accel","class_id"} },
        "blobs":   { session_id: {"x","y","z","angle","width","height","area",
                                  "x_vel","y_vel","z_vel","rot_vel","accel","rot_accel"} },
        "added":    frozenset of session_ids newly appeared this frame,
        "removed":  frozenset of session_ids that left this frame,
        "frame_id": int,
    }
    z / z_vel are 0.0 for 2D profiles.
    """

    def __init__(
        self,
        frame_queue: queue.Queue,
        profile: str = "both",
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

        # Per-frame alive sets (one per profile type)
        self._cur_alive: set[int] = set()
        self._obj_alive: set[int] = set()
        self._blb_alive: set[int] = set()

        # Per-frame data stores
        self._cursors: dict[int, dict] = {}
        self._objects: dict[int, dict] = {}
        self._blobs:   dict[int, dict] = {}

        self._prev_alive: set[int] = set()

        # For deriving velocity when the simulator sends 0: {sid: (x, y, t)}
        self._prev_pos: dict[int, tuple[float, float, float]] = {}

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
        # Register all nine TUIO profiles unconditionally
        dispatcher.map("/tuio/2Dcur",  self._handle_2Dcur)
        dispatcher.map("/tuio/2Dobj",  self._handle_2Dobj)
        dispatcher.map("/tuio/2Dblb",  self._handle_2Dblb)
        dispatcher.map("/tuio/25Dcur", self._handle_25Dcur)
        dispatcher.map("/tuio/25Dobj", self._handle_25Dobj)
        dispatcher.map("/tuio/25Dblb", self._handle_25Dblb)
        dispatcher.map("/tuio/3Dcur",  self._handle_3Dcur)
        dispatcher.map("/tuio/3Dobj",  self._handle_3Dobj)
        dispatcher.map("/tuio/3Dblb",  self._handle_3Dblb)

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
        logger.info("TUIO receiver listening on %s:%d", host, port)
        return True

    def stop(self) -> None:
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

    def _fits(self, store: dict, sid: int) -> bool:
        return len(store) < self._max_objects or sid in store

    def _derive_vel(self, sid: int, x: float, y: float) -> tuple[float, float]:
        """Compute velocity from position delta when simulator sends zero."""
        now = time.monotonic()
        prev = self._prev_pos.get(sid)
        self._prev_pos[sid] = (x, y, now)
        if prev is None:
            return 0.0, 0.0
        px, py, pt = prev
        dt = now - pt
        if dt <= 0 or dt > 0.5:
            return 0.0, 0.0
        return (x - px) / dt, (y - py) / dt

    # ---- 2D cursor: set s_id x y X Y m_acc --------------------------------

    def _handle_2Dcur(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            match args[0]:
                case "alive":
                    self._cur_alive = {int(a) for a in args[1:]}
                    for sid in list(self._cursors):
                        if sid not in self._cur_alive:
                            del self._cursors[sid]
                case "set":
                    if len(args) >= 7:
                        sid = int(args[1])
                        if self._fits(self._cursors, sid):
                            x, y = float(args[2]), float(args[3])
                            xv, yv = float(args[4]), float(args[5])
                            if xv == 0.0 and yv == 0.0:
                                xv, yv = self._derive_vel(sid, x, y)
                            else:
                                self._prev_pos[sid] = (x, y, __import__('time').monotonic())
                            self._cursors[sid] = {
                                "x": x, "y": y, "z": 0.0,
                                "x_vel": xv, "y_vel": yv, "z_vel": 0.0,
                                "accel": float(args[6]),
                            }
                case "fseq":
                    self._maybe_emit(int(args[1]) if len(args) >= 2 else -1)
        except Exception as exc:
            self._error_count += 1
            logger.debug("2Dcur error: %s", exc)

    # ---- 2D object: set s_id i_id x y a X Y A m_acc r_acc -----------------

    def _handle_2Dobj(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            match args[0]:
                case "alive":
                    self._obj_alive = {int(a) for a in args[1:]}
                    for sid in list(self._objects):
                        if sid not in self._obj_alive:
                            del self._objects[sid]
                case "set":
                    if len(args) >= 11:
                        sid = int(args[1])
                        if self._fits(self._objects, sid):
                            x, y = float(args[3]), float(args[4])
                            xv, yv = float(args[6]), float(args[7])
                            if xv == 0.0 and yv == 0.0:
                                xv, yv = self._derive_vel(sid, x, y)
                            else:
                                self._prev_pos[sid] = (x, y, time.monotonic())
                            self._objects[sid] = {
                                "class_id": int(args[2]),
                                "x": x, "y": y, "z": 0.0,
                                "angle": float(args[5]),
                                "x_vel": xv, "y_vel": yv, "z_vel": 0.0,
                                "rot_vel": float(args[8]),
                                "accel": float(args[9]), "rot_accel": float(args[10]),
                            }
                case "fseq":
                    self._maybe_emit(int(args[1]) if len(args) >= 2 else -1)
        except Exception as exc:
            self._error_count += 1
            logger.debug("2Dobj error: %s", exc)

    # ---- 2D blob: set s_id x y a w h f X Y A m_acc r_acc ------------------

    def _handle_2Dblb(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            match args[0]:
                case "alive":
                    self._blb_alive = {int(a) for a in args[1:]}
                    for sid in list(self._blobs):
                        if sid not in self._blb_alive:
                            del self._blobs[sid]
                case "set":
                    if len(args) >= 13:
                        sid = int(args[1])
                        if self._fits(self._blobs, sid):
                            x, y = float(args[2]), float(args[3])
                            xv, yv = float(args[8]), float(args[9])
                            if xv == 0.0 and yv == 0.0:
                                xv, yv = self._derive_vel(sid, x, y)
                            else:
                                self._prev_pos[sid] = (x, y, time.monotonic())
                            self._blobs[sid] = {
                                "x": x, "y": y, "z": 0.0,
                                "angle": float(args[4]),
                                "width": float(args[5]), "height": float(args[6]), "area": float(args[7]),
                                "x_vel": xv, "y_vel": yv, "z_vel": 0.0,
                                "rot_vel": float(args[10]),
                                "accel": float(args[11]), "rot_accel": float(args[12]),
                            }
                case "fseq":
                    self._maybe_emit(int(args[1]) if len(args) >= 2 else -1)
        except Exception as exc:
            self._error_count += 1
            logger.debug("2Dblb error: %s", exc)

    # ---- 2.5D cursor: set s_id x y z X Y Z m_acc --------------------------

    def _handle_25Dcur(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            match args[0]:
                case "alive":
                    self._cur_alive = {int(a) for a in args[1:]}
                    for sid in list(self._cursors):
                        if sid not in self._cur_alive:
                            del self._cursors[sid]
                case "set":
                    if len(args) >= 9:
                        sid = int(args[1])
                        if self._fits(self._cursors, sid):
                            self._cursors[sid] = {
                                "x": float(args[2]), "y": float(args[3]), "z": float(args[4]),
                                "x_vel": float(args[5]), "y_vel": float(args[6]), "z_vel": float(args[7]),
                                "accel": float(args[8]),
                            }
                case "fseq":
                    self._maybe_emit(int(args[1]) if len(args) >= 2 else -1)
        except Exception as exc:
            self._error_count += 1
            logger.debug("25Dcur error: %s", exc)

    # ---- 2.5D object: set s_id i_id x y z a X Y Z A m_acc r_acc -----------

    def _handle_25Dobj(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            match args[0]:
                case "alive":
                    self._obj_alive = {int(a) for a in args[1:]}
                    for sid in list(self._objects):
                        if sid not in self._obj_alive:
                            del self._objects[sid]
                case "set":
                    if len(args) >= 13:
                        sid = int(args[1])
                        if self._fits(self._objects, sid):
                            self._objects[sid] = {
                                "class_id": int(args[2]),
                                "x": float(args[3]), "y": float(args[4]), "z": float(args[5]),
                                "angle": float(args[6]),
                                "x_vel": float(args[7]), "y_vel": float(args[8]), "z_vel": float(args[9]),
                                "rot_vel": float(args[10]),
                                "accel": float(args[11]), "rot_accel": float(args[12]),
                            }
                case "fseq":
                    self._maybe_emit(int(args[1]) if len(args) >= 2 else -1)
        except Exception as exc:
            self._error_count += 1
            logger.debug("25Dobj error: %s", exc)

    # ---- 2.5D blob: set s_id x y z a w h f X Y Z A m_acc r_acc ------------

    def _handle_25Dblb(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            match args[0]:
                case "alive":
                    self._blb_alive = {int(a) for a in args[1:]}
                    for sid in list(self._blobs):
                        if sid not in self._blb_alive:
                            del self._blobs[sid]
                case "set":
                    if len(args) >= 15:
                        sid = int(args[1])
                        if self._fits(self._blobs, sid):
                            self._blobs[sid] = {
                                "x": float(args[2]), "y": float(args[3]), "z": float(args[4]),
                                "angle": float(args[5]),
                                "width": float(args[6]), "height": float(args[7]), "area": float(args[8]),
                                "x_vel": float(args[9]), "y_vel": float(args[10]), "z_vel": float(args[11]),
                                "rot_vel": float(args[12]),
                                "accel": float(args[13]), "rot_accel": float(args[14]),
                            }
                case "fseq":
                    self._maybe_emit(int(args[1]) if len(args) >= 2 else -1)
        except Exception as exc:
            self._error_count += 1
            logger.debug("25Dblb error: %s", exc)

    # ---- 3D cursor: set s_id x y z X Y Z m_acc (same layout as 25Dcur) ----

    def _handle_3Dcur(self, address: str, *args: Any) -> None:
        self._handle_25Dcur(address, *args)

    # ---- 3D object: set s_id i_id x y z a b c X Y Z A B C m_acc r_acc ----
    # a/b/c = Euler angles (phi/theta/psi); A/B/C = angular velocities

    def _handle_3Dobj(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            match args[0]:
                case "alive":
                    self._obj_alive = {int(a) for a in args[1:]}
                    for sid in list(self._objects):
                        if sid not in self._obj_alive:
                            del self._objects[sid]
                case "set":
                    if len(args) >= 17:
                        sid = int(args[1])
                        if self._fits(self._objects, sid):
                            self._objects[sid] = {
                                "class_id": int(args[2]),
                                "x": float(args[3]), "y": float(args[4]), "z": float(args[5]),
                                # Store first Euler angle as "angle" for display
                                "angle": float(args[6]),
                                "x_vel": float(args[9]), "y_vel": float(args[10]), "z_vel": float(args[11]),
                                "rot_vel": float(args[12]),
                                "accel": float(args[15]), "rot_accel": float(args[16]),
                            }
                case "fseq":
                    self._maybe_emit(int(args[1]) if len(args) >= 2 else -1)
        except Exception as exc:
            self._error_count += 1
            logger.debug("3Dobj error: %s", exc)

    # ---- 3D blob: set s_id x y z a b c w h d f X Y Z A B C m_acc r_acc ---

    def _handle_3Dblb(self, address: str, *args: Any) -> None:
        if not args:
            return
        try:
            match args[0]:
                case "alive":
                    self._blb_alive = {int(a) for a in args[1:]}
                    for sid in list(self._blobs):
                        if sid not in self._blb_alive:
                            del self._blobs[sid]
                case "set":
                    if len(args) >= 19:
                        sid = int(args[1])
                        if self._fits(self._blobs, sid):
                            self._blobs[sid] = {
                                "x": float(args[2]), "y": float(args[3]), "z": float(args[4]),
                                "angle": float(args[5]),
                                "width": float(args[8]), "height": float(args[9]), "area": float(args[10]),
                                "x_vel": float(args[11]), "y_vel": float(args[12]), "z_vel": float(args[13]),
                                "rot_vel": float(args[14]),
                                "accel": float(args[17]), "rot_accel": float(args[18]),
                            }
                case "fseq":
                    self._maybe_emit(int(args[1]) if len(args) >= 2 else -1)
        except Exception as exc:
            self._error_count += 1
            logger.debug("3Dblb error: %s", exc)

    # ---- Frame assembly ----------------------------------------------------

    def _maybe_emit(self, frame_id: int) -> None:
        current_alive = self._cur_alive | self._obj_alive | self._blb_alive
        added   = current_alive - self._prev_alive
        removed = self._prev_alive - current_alive
        self._prev_alive = current_alive

        frame = {
            "cursors":  dict(self._cursors),
            "objects":  dict(self._objects),
            "blobs":    dict(self._blobs),
            "added":    frozenset(added),
            "removed":  frozenset(removed),
            "frame_id": frame_id,
        }
        try:
            self._frame_queue.put_nowait(frame)
        except queue.Full:
            logger.debug("Frame queue full — dropping frame %d", frame_id)
