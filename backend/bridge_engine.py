"""
bridge_engine.py — Transform logic and OSC output dispatcher.

Runs on a daemon thread, consuming TUIOReceiver frame dicts from a queue and
dispatching individual OSC messages (never bundles) to each enabled target.

Emits Qt signals to update the GUI models — safe across threads via Qt's
queued connection mechanism.
"""

import logging
import queue
import threading
import time
from typing import Callable

from pythonosc.udp_client import SimpleUDPClient

logger = logging.getLogger(__name__)


class BridgeEngine:
    """
    Consumes TUIO frame dicts and dispatches OSC messages to configured targets.

    Callbacks (called from engine thread, must be thread-safe):
      on_state_updated(frame: dict)            — full frame for GUI table
      on_osc_sent(address: str, value)         — one entry per OSC message sent
      on_stats_updated(active: int, mps: float)— periodic stats
    """

    QUEUE_MAXSIZE = 512
    STATS_INTERVAL = 1.0   # seconds between stats updates

    def __init__(
        self,
        frame_queue: queue.Queue,
        on_state_updated: Callable[[dict], None] | None = None,
        on_osc_sent: Callable[[str, object], None] | None = None,
        on_stats_updated: Callable[[int, float], None] | None = None,
    ) -> None:
        self._frame_queue = frame_queue
        self._on_state_updated = on_state_updated or (lambda f: None)
        self._on_osc_sent = on_osc_sent or (lambda a, v: None)
        self._on_stats_updated = on_stats_updated or (lambda n, r: None)

        self._targets: list[dict] = []         # validated target configs
        self._clients: list[SimpleUDPClient | None] = []
        self._address_template: str = "/tuio/cursor/{id}"

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self._msg_count = 0
        self._last_stats_time = time.monotonic()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def configure(self, config: dict) -> None:
        """
        Apply a new config dict (from ConfigManager). Safe to call before start()
        or while running — swaps config atomically from the caller's thread.
        The engine thread reads _targets/_clients only at the start of each frame
        so a swap mid-frame is safe at the granularity of one frame.
        """
        targets = config.get("osc_output", {}).get("targets", [])
        template = config.get("osc_output", {}).get("address_template", "/tuio/cursor/{id}")

        new_clients: list[SimpleUDPClient | None] = []
        for t in targets:
            if t.get("enabled", False):
                try:
                    client = SimpleUDPClient(t["ip"], t["port"])
                    new_clients.append(client)
                    logger.info("OSC target ready: %s:%d", t["ip"], t["port"])
                except Exception as exc:
                    logger.error("Cannot create OSC client %s:%d: %s", t["ip"], t["port"], exc)
                    new_clients.append(None)
            else:
                new_clients.append(None)

        self._targets = targets
        self._clients = new_clients
        self._address_template = template

    def send_test_message(self, target_index: int) -> bool:
        """Send a single test OSC message to target[target_index]. Returns True on send."""
        if target_index < 0 or target_index >= len(self._clients):
            return False
        client = self._clients[target_index]
        if client is None:
            return False
        try:
            client.send_message("/tuio/bridge/test", [1])
            logger.info("Test message sent to target %d", target_index)
            return True
        except Exception as exc:
            logger.error("Test send failed: %s", exc)
            return False

    def start(self) -> None:
        """Start the dispatch thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="bridge-engine",
            daemon=True,
        )
        self._thread.start()
        logger.info("BridgeEngine started")

    def stop(self) -> None:
        """Stop the dispatch thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("BridgeEngine stopped")

    # -----------------------------------------------------------------------
    # Engine loop
    # -----------------------------------------------------------------------

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                frame = self._frame_queue.get(timeout=0.05)
            except queue.Empty:
                self._maybe_emit_stats(0)
                continue

            try:
                self._process_frame(frame)
            except Exception as exc:
                logger.error("Frame processing error: %s", exc, exc_info=True)
            finally:
                self._frame_queue.task_done()

    def _process_frame(self, frame: dict) -> None:
        # Snapshot targets/clients for this frame (atomic swap safety)
        targets = self._targets
        clients = self._clients
        template = self._address_template

        # Notify GUI
        self._on_state_updated(frame)

        active_count = (len(frame.get("cursors", {}))
                        + len(frame.get("objects", {}))
                        + len(frame.get("blobs", {})))

        # Dispatch OSC for each enabled target
        for idx, (target, client) in enumerate(zip(targets, clients)):
            if client is None:
                continue
            t_cfg = target

            self._send_cursors(frame, t_cfg, client, template)
            self._send_objects(frame, t_cfg, client, template)
            self._send_blobs(frame, t_cfg, client, template)
            self._send_removed(frame, t_cfg, client, template)

        self._maybe_emit_stats(active_count)

    # -----------------------------------------------------------------------
    # OSC sending
    # -----------------------------------------------------------------------

    def _apply_transform(self, x: float, y: float, t: dict) -> tuple[float, float]:
        """Apply flip, swap and scale/offset transforms."""
        if t.get("flip_x"):
            x = 1.0 - x
        if t.get("flip_y"):
            y = 1.0 - y
        if t.get("swap_axes"):
            x, y = y, x
        x = x * t.get("scale_x", 1.0) + t.get("offset_x", 0.0)
        y = y * t.get("scale_y", 1.0) + t.get("offset_y", 0.0)
        return x, y

    def _send(self, client: SimpleUDPClient, address: str, value: object) -> None:
        """Send one OSC message and notify the log callback."""
        try:
            client.send_message(address, value)
            self._msg_count += 1
            self._on_osc_sent(address, value)
        except Exception as exc:
            logger.debug("OSC send error: %s", exc)

    def _send_cursors(
        self,
        frame: dict,
        t: dict,
        client: SimpleUDPClient,
        template: str,
    ) -> None:
        for sid, cur in frame.get("cursors", {}).items():
            x, y = self._apply_transform(cur["x"], cur["y"], t)
            base = template.replace("{id}", str(sid))
            self._send(client, f"{base}/x",     float(x))
            self._send(client, f"{base}/y",     float(y))
            if cur.get("z", 0.0) != 0.0:
                self._send(client, f"{base}/z", float(cur["z"]))
            self._send(client, f"{base}/x_vel", float(cur["x_vel"]))
            self._send(client, f"{base}/y_vel", float(cur["y_vel"]))
            if cur.get("z_vel", 0.0) != 0.0:
                self._send(client, f"{base}/z_vel", float(cur["z_vel"]))
            self._send(client, f"{base}/accel", float(cur["accel"]))
            self._send(client, f"{base}/alive", 1)

    def _send_objects(
        self,
        frame: dict,
        t: dict,
        client: SimpleUDPClient,
        template: str,
    ) -> None:
        obj_template = template.replace("cursor", "object")
        for sid, obj in frame.get("objects", {}).items():
            x, y = self._apply_transform(obj["x"], obj["y"], t)
            base = obj_template.replace("{id}", str(sid))
            self._send(client, f"{base}/x",        float(x))
            self._send(client, f"{base}/y",        float(y))
            if obj.get("z", 0.0) != 0.0:
                self._send(client, f"{base}/z",    float(obj["z"]))
            self._send(client, f"{base}/angle",    float(obj["angle"]))
            self._send(client, f"{base}/x_vel",    float(obj["x_vel"]))
            self._send(client, f"{base}/y_vel",    float(obj["y_vel"]))
            if obj.get("z_vel", 0.0) != 0.0:
                self._send(client, f"{base}/z_vel", float(obj["z_vel"]))
            self._send(client, f"{base}/rot_vel",  float(obj["rot_vel"]))
            self._send(client, f"{base}/accel",    float(obj["accel"]))
            self._send(client, f"{base}/class_id", int(obj["class_id"]))
            self._send(client, f"{base}/alive",    1)

    def _send_blobs(
        self,
        frame: dict,
        t: dict,
        client: SimpleUDPClient,
        template: str,
    ) -> None:
        blb_template = template.replace("cursor", "blob")
        for sid, blb in frame.get("blobs", {}).items():
            x, y = self._apply_transform(blb["x"], blb["y"], t)
            base = blb_template.replace("{id}", str(sid))
            self._send(client, f"{base}/x",      float(x))
            self._send(client, f"{base}/y",      float(y))
            if blb.get("z", 0.0) != 0.0:
                self._send(client, f"{base}/z",  float(blb["z"]))
            self._send(client, f"{base}/angle",  float(blb["angle"]))
            self._send(client, f"{base}/width",  float(blb["width"]))
            self._send(client, f"{base}/height", float(blb["height"]))
            self._send(client, f"{base}/area",   float(blb["area"]))
            self._send(client, f"{base}/x_vel",  float(blb["x_vel"]))
            self._send(client, f"{base}/y_vel",  float(blb["y_vel"]))
            if blb.get("z_vel", 0.0) != 0.0:
                self._send(client, f"{base}/z_vel", float(blb["z_vel"]))
            self._send(client, f"{base}/accel",  float(blb["accel"]))
            self._send(client, f"{base}/alive",  1)

    def _send_removed(
        self,
        frame: dict,
        t: dict,
        client: SimpleUDPClient,
        template: str,
    ) -> None:
        for sid in frame.get("removed", frozenset()):
            for kind in ("cursor", "object", "blob"):
                base = template.replace("cursor", kind).replace("{id}", str(sid))
                self._send(client, f"{base}/alive", 0)

    # -----------------------------------------------------------------------
    # Stats
    # -----------------------------------------------------------------------

    def _maybe_emit_stats(self, active_count: int) -> None:
        now = time.monotonic()
        elapsed = now - self._last_stats_time
        if elapsed >= self.STATS_INTERVAL:
            mps = self._msg_count / elapsed
            self._msg_count = 0
            self._last_stats_time = now
            self._on_stats_updated(active_count, mps)
