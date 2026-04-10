# TUIO Bridge — Project Brief

**Python GUI Application**
Version 1.0 | Author: Ant | Status: Ready for Implementation

-----

## 1. Purpose

TUIO Bridge is a standalone Python GUI application that receives a TUIO stream (typically from a touch surface, fiducial tracker or multitouch device), decodes and displays the incoming data in a human-readable way, and re-emits clean, individually addressable OSC messages to one or more downstream targets — primarily Pixera, but also TouchDesigner, Notch or any OSC-capable application.

The core problem it solves is that raw TUIO is delivered as OSC bundles with a specific multi-argument structure that most media server OSC inputs (including Pixera’s DirectNetworkOsc module) cannot parse natively. This bridge unpacks the TUIO protocol, exposes the data clearly and re-packages it as flat, well-named OSC messages.

-----

## 2. Project Overview

|Property          |Value                                       |
|------------------|--------------------------------------------|
|Application name  |TUIO Bridge                                 |
|Language          |Python 3.10+                                |
|GUI framework     |PyQt6                                       |
|OSC library       |python-osc (pythonosc)                      |
|Target platforms  |Windows 10/11 (primary), macOS (secondary)  |
|Deployment        |Run from source or packaged with PyInstaller|
|Config persistence|JSON config file (`tuio_bridge_config.json`)|
|TUIO version      |TUIO 1.1 (2Dcur and 2Dobj profiles)         |

-----

## 3. Architecture

The application is split into three decoupled layers, consistent with the project’s broader principle of separating core logic from UI and output concerns.

### Layer 1 — TUIO Receiver (`tuio_receiver.py`)

- Listens on a configurable UDP port (default 3333) using python-osc.
- Parses incoming OSC bundles, identifying `alive`, `set` and `fseq` messages for `/tuio/2Dcur` and `/tuio/2Dobj` profiles.
- Maintains a live state dictionary of active session IDs and their current data.
- Detects object add and remove events by diffing sequential `alive` messages.
- Emits parsed data to the Bridge Engine via a thread-safe queue or callback.

### Layer 2 — Bridge Engine (`bridge_engine.py`)

- Receives parsed TUIO state from the receiver.
- Applies any configured transformations: coordinate remapping, axis flipping, value scaling.
- Constructs outgoing OSC messages according to the configured output address template.
- Dispatches individual UDP OSC messages (never bundles) to all configured output targets.
- Runs on its own thread; the UI never blocks the data path.

### Layer 3 — GUI (`main_window.py`, PyQt6)

- Provides all user-facing configuration and monitoring.
- Reads and writes config to JSON on launch and close.
- Does not participate in the data path — it only reads state for display.

-----

## 4. TUIO Input

### 4.1 Profiles Supported

|Address      |Data                                                                    |
|-------------|------------------------------------------------------------------------|
|`/tuio/2Dcur`|Cursor (touch/pointer) — session ID, x, y, x_vel, y_vel, acceleration   |
|`/tuio/2Dobj`|Object (fiducial marker) — session ID, class ID, x, y, angle, velocities|

### 4.2 Message Structure

Each TUIO bundle contains three message types on the same OSC address:

```
/tuio/2Dcur  alive  s_id0 s_id1 ...          # active session IDs (int)
/tuio/2Dcur  set    s_id x y x_vel y_vel m   # per-object data (floats 0.0–1.0)
/tuio/2Dcur  fseq   frame_id                  # frame counter (int)
```

`x` and `y` are normalised floats (0.0 to 1.0). The bridge must handle all three message types and reconstruct object lifetime from `alive` diffs.

### 4.3 Input Settings (configurable in GUI)

- Listen port (default: `3333`)
- Listen address (default: `0.0.0.0` — all interfaces)
- Active TUIO profile: `2Dcur`, `2Dobj` or both
- Maximum tracked objects (safety cap, default: 20)

-----

## 5. OSC Output

### 5.1 Output Targets

The application supports up to four simultaneous output targets. Each target is independently configurable with its own IP, port and enable toggle. This allows the bridge to feed Pixera and a secondary application (e.g. TouchDesigner or a logging tool) simultaneously.

### 5.2 Default Address Template

Outgoing OSC addresses follow a configurable template. The default:

```
/tuio/cursor/{id}/x      float  normalised 0.0–1.0
/tuio/cursor/{id}/y      float  normalised 0.0–1.0
/tuio/cursor/{id}/x_vel  float
/tuio/cursor/{id}/y_vel  float
/tuio/cursor/{id}/accel  float
/tuio/cursor/{id}/alive  int    1 = active, 0 = removed
```

For the `2Dobj` profile, additionally:

```
/tuio/object/{id}/class_id  int
/tuio/object/{id}/angle     float  radians
```

### 5.3 Address Template Customisation

The user can edit the base path prefix in the GUI. The `{id}` token is always substituted with the session ID integer. Examples of valid custom prefixes:

```
/pixera/tracking/cursor/{id}/x
/touch/{id}/position/x
```

### 5.4 Coordinate Transforms (configurable per output target)

- Flip X axis (mirrors left/right)
- Flip Y axis (mirrors top/bottom)
- Swap X and Y axes
- Scale: multiply normalised values by a configurable factor (e.g. to match screen resolution)
- Offset: add a fixed offset to X and/or Y after scaling

### 5.5 Critical Pixera Note

> **Pixera’s DirectNetworkOsc module requires individual OSC messages — not OSC bundles.** The bridge must always send messages individually via `SimpleUDPClient`, never via `OscBundleBuilder`. This is non-negotiable for Pixera compatibility.

-----

## 6. GUI Layout

The window is divided into three vertical panels, laid out with `QSplitter` so the user can resize them.

### Left Panel — Configuration

- **TUIO Input** section: port, listen address, profile selector, max objects.
- **OSC Output** section: up to four target rows, each with IP field, port field, enable checkbox and a Test button that sends a single test message.
- **Address template** field: editable base path with `{id}` token.
- **Transform settings**: per-output checkboxes for flip X, flip Y, swap axes; numeric fields for scale and offset.
- Save Config and Load Config buttons. Config auto-saves on close.

### Centre Panel — Live Monitor

- A table showing all currently active objects with columns: ID, Type (cursor/object), X, Y, X Vel, Y Vel, Accel, Angle (if applicable), Class ID (if applicable), Lifetime (seconds since first seen).
- Rows appear on object add and are removed when it leaves.
- Values update every 50 ms — not every frame, to keep the UI readable.
- Row count indicator: `Active: 3 / 20`.

### Right Panel — OSC Log

- A scrolling log of outgoing OSC messages showing address and value.
- Throttled display: maximum one message per address per 100 ms to prevent flooding.
- Filter field: type a string to show only matching addresses.
- Clear button, Pause toggle and a messages-per-second counter.

### Status Bar

- Connection state for TUIO input (Listening / Error).
- Active object count.
- Outgoing message rate (msg/s).
- Error or warning text.

-----

## 7. Config File

All settings persist to `tuio_bridge_config.json` in the application directory. On first run, defaults are written. The file is human-readable and can be edited manually.

```json
{
  "tuio_input": {
    "port": 3333,
    "address": "0.0.0.0",
    "profile": "both",
    "max_objects": 20
  },
  "osc_output": {
    "address_template": "/tuio/cursor/{id}",
    "targets": [
      {
        "ip": "127.0.0.1",
        "port": 7000,
        "enabled": true,
        "flip_x": false,
        "flip_y": false,
        "swap_axes": false,
        "scale_x": 1.0,
        "scale_y": 1.0,
        "offset_x": 0.0,
        "offset_y": 0.0
      },
      {
        "ip": "127.0.0.1",
        "port": 9000,
        "enabled": false,
        "flip_x": false,
        "flip_y": false,
        "swap_axes": false,
        "scale_x": 1.0,
        "scale_y": 1.0,
        "offset_x": 0.0,
        "offset_y": 0.0
      }
    ]
  }
}
```

-----

## 8. Dependencies

|Package     |Purpose             |Install                 |
|------------|--------------------|------------------------|
|PyQt6       |GUI framework       |`pip install PyQt6`     |
|python-osc  |OSC send and receive|`pip install python-osc`|
|Python 3.10+|Minimum version     |—                       |

No other external dependencies. Standard library modules used: `threading`, `queue`, `json`, `socket`, `time`, `logging`.

-----

## 9. File Structure

```
tuio_bridge/
  main.py                   # Entry point — creates QApplication and MainWindow
  main_window.py            # PyQt6 main window and panel layout
  tuio_receiver.py          # TUIO/OSC listener and parser
  bridge_engine.py          # Transform logic and OSC output dispatcher
  config_manager.py         # JSON read/write, defaults, validation
  tuio_bridge_config.json   # Auto-generated on first run
  requirements.txt          # PyQt6, python-osc
```

-----

## 10. Implementation Notes

### Threading model

The TUIO receiver runs in a daemon thread using python-osc’s `ThreadingOSCUDPServer`. Parsed state is placed on a thread-safe queue consumed by the bridge engine on its own thread. The Qt GUI polls a shared state snapshot via a `QTimer` at 50 ms intervals. No OSC or networking code runs on the Qt main thread.

### Object lifetime tracking

Maintain a dict keyed by session ID. On each `alive` message, diff the incoming ID set against the known set:

- IDs present in `alive` but not in the dict are **new** — emit `alive=1` and record a `first_seen` timestamp.
- IDs in the dict but absent from `alive` have been **removed** — emit a final `alive=0` message and delete the entry.

### OSC output — Pixera compatibility

Use python-osc’s `SimpleUDPClient` for all output. Never use `OscMessageBuilder` with a bundle wrapper. Each attribute (`x`, `y`, `x_vel`, etc.) is sent as a separate message. This is required for Pixera compatibility and keeps addresses clean for Chataigne and TouchDesigner as well.

### GUI update rate

The live monitor table and OSC log update via `QTimer` at 50 ms (20 fps). The underlying data may arrive at 60–120 Hz from the TUIO source; the GUI does not need to display every frame. The bridge engine dispatches OSC in real time regardless of GUI refresh rate.

### Error handling

- Port bind failures (e.g. port already in use) must be caught and reported in the status bar with a clear message.
- Malformed TUIO bundles must be silently skipped with an incremented error counter shown in the status bar.
- Network errors on OSC output must not crash the engine — log and continue.

-----

## 11. Out of Scope for Phase 1

- TUIO 2.0 support (candidate for a later phase).
- Recording and playback of TUIO sessions.
- Visual canvas or touch-point visualisation — the table monitor is sufficient.
- WebSocket or TCP transport for TUIO input (UDP only).
- Installer / packaged executable — PyInstaller packaging is a separate step after validation.

-----

## 12. Acceptance Criteria

- [ ] Application starts without error and begins listening on the configured TUIO port.
- [ ] Incoming TUIO cursors appear in the live monitor table within one second of the first touch event.
- [ ] OSC messages arrive at Pixera’s DirectNetworkOsc module with clean individual addresses, verified via Pixera’s OSC log or a secondary OSC monitor.
- [ ] Removing a touch from the surface removes the row from the monitor table and sends a final `alive=0` message.
- [ ] All settings persist correctly across application restarts.
- [ ] Coordinate transforms (flip, scale, offset) produce correct values verified against known input.
- [ ] Multiple output targets can be enabled simultaneously with independent settings.
- [ ] Application handles port conflicts and network errors gracefully without crashing.
