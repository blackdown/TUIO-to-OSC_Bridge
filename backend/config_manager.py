"""
config_manager.py — JSON config persistence for TUIO Bridge.

Loads/saves tuio_bridge_config.json next to the running script (or executable
when packaged with PyInstaller). Writes defaults on first run and validates
types on load, falling back to defaults for any bad value.
"""

import json
import logging
import os
import sys
from copy import deepcopy
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

DEFAULT_TARGET = {
    "ip": "127.0.0.1",
    "port": 7000,
    "enabled": False,
    "flip_x": False,
    "flip_y": False,
    "swap_axes": False,
    "scale_x": 1.0,
    "scale_y": 1.0,
    "offset_x": 0.0,
    "offset_y": 0.0,
}

DEFAULT_CONFIG: dict[str, Any] = {
    "tuio_input": {
        "port": 3333,
        "address": "0.0.0.0",
        "profile": "all",
        "max_objects": 20,
    },
    "osc_output": {
        "address_template": "/tuio/cursor/{id}",
        "targets": [
            {**DEFAULT_TARGET, "port": 7000, "enabled": True},
        ],
    },
    "serial_output": {
        "enabled": False,
        "port": "",
        "baud_rate": 115200,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config_path() -> str:
    """Return the path to the config file, next to the script or executable."""
    if getattr(sys, "frozen", False):
        # PyInstaller: sys.executable is the packaged binary
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
        # Go one level up (config lives at project root)
        base = os.path.dirname(base)
    return os.path.join(base, "tuio_bridge_config.json")


def _coerce(value: Any, expected_type: type, default: Any) -> Any:
    """Try to cast value to expected_type; return default on failure."""
    try:
        if expected_type is bool:
            if isinstance(value, bool):
                return value
            raise TypeError
        return expected_type(value)
    except (TypeError, ValueError):
        logger.warning("Config: expected %s, got %r — using default %r",
                       expected_type.__name__, value, default)
        return default


def _validate_target(raw: Any, idx: int) -> dict:
    """Return a validated target dict; bad fields replaced with defaults."""
    d = deepcopy(DEFAULT_TARGET)
    if not isinstance(raw, dict):
        logger.warning("Config: target[%d] is not a dict — using defaults", idx)
        return d

    d["ip"]        = _coerce(raw.get("ip",        d["ip"]),        str,   d["ip"])
    d["port"]      = _coerce(raw.get("port",      d["port"]),      int,   d["port"])
    d["enabled"]   = _coerce(raw.get("enabled",   d["enabled"]),   bool,  d["enabled"])
    d["flip_x"]    = _coerce(raw.get("flip_x",    d["flip_x"]),    bool,  d["flip_x"])
    d["flip_y"]    = _coerce(raw.get("flip_y",    d["flip_y"]),    bool,  d["flip_y"])
    d["swap_axes"] = _coerce(raw.get("swap_axes", d["swap_axes"]), bool,  d["swap_axes"])
    d["scale_x"]   = _coerce(raw.get("scale_x",  d["scale_x"]),   float, d["scale_x"])
    d["scale_y"]   = _coerce(raw.get("scale_y",  d["scale_y"]),   float, d["scale_y"])
    d["offset_x"]  = _coerce(raw.get("offset_x", d["offset_x"]),  float, d["offset_x"])
    d["offset_y"]  = _coerce(raw.get("offset_y", d["offset_y"]),  float, d["offset_y"])

    # Clamp port to valid range
    d["port"] = max(1, min(65535, d["port"]))
    return d


def _validate_config(raw: Any) -> dict:
    """Return a fully validated config dict."""
    cfg = deepcopy(DEFAULT_CONFIG)
    if not isinstance(raw, dict):
        logger.warning("Config: root is not a dict — using defaults")
        return cfg

    # tuio_input
    ti_raw = raw.get("tuio_input", {})
    if isinstance(ti_raw, dict):
        ti = cfg["tuio_input"]
        ti["port"]        = _coerce(ti_raw.get("port",        ti["port"]),        int, ti["port"])
        ti["address"]     = _coerce(ti_raw.get("address",     ti["address"]),     str, ti["address"])
        ti["max_objects"] = _coerce(ti_raw.get("max_objects", ti["max_objects"]), int, ti["max_objects"])
        _valid_profiles = {
            "all", "both",
            "2Dcur", "2Dobj", "2Dblb",
            "25Dcur", "25Dobj", "25Dblb",
            "3Dcur", "3Dobj", "3Dblb",
        }
        profile = ti_raw.get("profile", ti["profile"])
        if profile in _valid_profiles:
            ti["profile"] = profile
        else:
            logger.warning("Config: invalid profile %r — using 'all'", profile)
            ti["profile"] = "all"
        ti["port"] = max(1, min(65535, ti["port"]))
        ti["max_objects"] = max(1, min(100, ti["max_objects"]))

    # osc_output
    oo_raw = raw.get("osc_output", {})
    if isinstance(oo_raw, dict):
        oo = cfg["osc_output"]
        template = oo_raw.get("address_template", oo["address_template"])
        if isinstance(template, str) and "{id}" in template:
            oo["address_template"] = template
        else:
            logger.warning("Config: address_template must be a string containing {id}")

        targets_raw = oo_raw.get("targets", [])
        if isinstance(targets_raw, list) and targets_raw:
            oo["targets"] = [
                _validate_target(t, i)
                for i, t in enumerate(targets_raw[:4])  # max 4
            ]

    # serial_output
    so_raw = raw.get("serial_output", {})
    if isinstance(so_raw, dict):
        so = cfg["serial_output"]
        so["enabled"]   = _coerce(so_raw.get("enabled",   so["enabled"]),   bool, so["enabled"])
        so["port"]      = _coerce(so_raw.get("port",      so["port"]),      str,  so["port"])
        so["baud_rate"] = _coerce(so_raw.get("baud_rate", so["baud_rate"]), int,  so["baud_rate"])
        _valid_bauds = {1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600}
        if so["baud_rate"] not in _valid_bauds:
            logger.warning("Config: unrecognised baud rate %d — using 115200", so["baud_rate"])
            so["baud_rate"] = 115200

    return cfg


# ---------------------------------------------------------------------------
# ConfigManager
# ---------------------------------------------------------------------------

class ConfigManager:
    """Manages loading and saving of tuio_bridge_config.json."""

    def __init__(self) -> None:
        self._path = _config_path()
        self._config: dict = deepcopy(DEFAULT_CONFIG)

    # ---- public API --------------------------------------------------------

    @property
    def path(self) -> str:
        return self._path

    @property
    def config(self) -> dict:
        """Return a deep copy of the current config."""
        return deepcopy(self._config)

    def get(self, *keys: str, default: Any = None) -> Any:
        """Nested key access: get('tuio_input', 'port')."""
        node = self._config
        for k in keys:
            if isinstance(node, dict):
                node = node.get(k, default)
            else:
                return default
        return node

    def set(self, keys: list[str], value: Any) -> None:
        """Set a nested key. Marks config dirty (caller must call save())."""
        node = self._config
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = value

    def set_target(self, index: int, key: str, value: Any) -> None:
        """Update a single field in a target by index."""
        if 0 <= index < len(self._config["osc_output"]["targets"]):
            self._config["osc_output"]["targets"][index][key] = value

    def load(self) -> bool:
        """Load config from disk. Returns True on success, False if file missing."""
        if not os.path.exists(self._path):
            logger.info("Config file not found at %s — writing defaults", self._path)
            self.save()
            return False
        try:
            with open(self._path, encoding="utf-8") as f:
                raw = json.load(f)
            self._config = _validate_config(raw)
            logger.info("Config loaded from %s", self._path)
            return True
        except json.JSONDecodeError as exc:
            logger.error("Config: JSON parse error in %s: %s — using defaults", self._path, exc)
            return False
        except OSError as exc:
            logger.error("Config: cannot read %s: %s", self._path, exc)
            return False

    def save(self) -> bool:
        """Save current config to disk. Returns True on success."""
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2)
            logger.info("Config saved to %s", self._path)
            return True
        except OSError as exc:
            logger.error("Config: cannot write %s: %s", self._path, exc)
            return False

    def add_target(self) -> int:
        """Append a default target. Returns the new index."""
        targets = self._config["osc_output"]["targets"]
        if len(targets) < 8:
            targets.append(deepcopy(DEFAULT_TARGET))
        return len(targets) - 1

    def remove_target(self, index: int) -> bool:
        """Remove target at index. Returns True on success (min 1 target)."""
        targets = self._config["osc_output"]["targets"]
        if 0 <= index < len(targets) and len(targets) > 1:
            targets.pop(index)
            return True
        return False

    def replace(self, new_config: dict) -> None:
        """Replace the entire config (e.g. after user edits in GUI)."""
        self._config = _validate_config(new_config)
