# TUIO Bridge

A Windows desktop application that receives TUIO 1.1 touch/object/blob data over UDP, displays it in a live monitor, and re-emits clean individual OSC messages to one or more downstream targets — primarily Pixera, but also TouchDesigner, Notch, or any OSC-capable application.

> **Current platform:** Windows 10/11 (standalone `.exe` available)

---

## Why this exists

Raw TUIO arrives as multi-argument OSC bundles that most media server OSC inputs (including Pixera's DirectNetworkOsc module) cannot parse natively. TUIO Bridge unpacks the protocol and re-emits flat, well-named individual OSC messages — one attribute per message — that every OSC target can consume directly.

---

## Download

Grab the latest zip from [Releases](../../releases) — extract and run `TUIO Bridge.exe`. No Python or Qt installation required.

---

## Running from source

**Requirements:** Python 3.12+, PySide6 ≥ 6.8, python-osc ≥ 1.8

```bash
pip install -r requirements.txt
python main.py
```

The app starts stopped. Press **Start** to begin listening on UDP port 3333. Config is written to `tuio_bridge_config.json` on first launch.

---

## TUIO Profiles Supported

All nine TUIO 1.1 profiles are supported:

| Dimension | Cursor | Object | Blob |
|-----------|--------|--------|------|
| 2D        | ✓ `/tuio/2Dcur` | ✓ `/tuio/2Dobj` | ✓ `/tuio/2Dblb` |
| 2.5D      | ✓ `/tuio/25Dcur` | ✓ `/tuio/25Dobj` | ✓ `/tuio/25Dblb` |
| 3D        | ✓ `/tuio/3Dcur` | ✓ `/tuio/3Dobj` | ✓ `/tuio/3Dblb` |

Velocity is taken directly from the TUIO data. If a simulator sends zero velocity, the bridge derives it from position deltas automatically.

---

## OSC Output Format

### Cursors
```
/tuio/cursor/{id}/x       float   normalised 0.0–1.0
/tuio/cursor/{id}/y       float   normalised 0.0–1.0
/tuio/cursor/{id}/x_vel   float
/tuio/cursor/{id}/y_vel   float
/tuio/cursor/{id}/accel   float
/tuio/cursor/{id}/alive   int     1 = active, 0 = removed
```

### Objects (additionally)
```
/tuio/object/{id}/angle     float   radians
/tuio/object/{id}/rot_vel   float
/tuio/object/{id}/class_id  int
```

### Blobs (additionally)
```
/tuio/blob/{id}/angle    float
/tuio/blob/{id}/width    float
/tuio/blob/{id}/height   float
/tuio/blob/{id}/area     float
```

For 2.5D/3D profiles a `/z` and `/z_vel` message is also sent when non-zero.

The address base path (`/tuio/cursor`) is configurable in the GUI. `{id}` is substituted with the session ID.

---

## Per-Target Transforms

Each output target supports independent transforms applied in order:

| Transform  | Description                        |
|------------|------------------------------------|
| Flip X     | Mirror left/right (`1 − x`)        |
| Flip Y     | Mirror top/bottom (`1 − y`)        |
| Swap X↔Y   | Exchange x and y axes              |
| Scale X/Y  | Multiply normalised value by factor |
| Offset X/Y | Add fixed offset after scaling     |

---

## Multiple Targets

Add up to 8 output targets via the **+ Add Target** button. Each target has its own IP, port, enable toggle, and transform settings. Remove targets with the **✕** button (minimum 1 target always kept).

---

## Config File

Settings auto-save to `tuio_bridge_config.json` on close. All fields are human-readable JSON and can be edited manually. Use **Save Config** / **Load Config** in the GUI to save and restore explicitly.

---

## Project Structure

```
main.py                      Entry point
backend/
  config_manager.py          JSON config persistence
  tuio_receiver.py           TUIO 1.1 UDP listener — all 9 profiles
  bridge_engine.py           Transform logic and OSC dispatcher
  cursor_model.py            Qt list model for live monitor table
  log_model.py               Qt list model for OSC log panel
  bridge_controller.py       Root QML-exposed controller
qml/
  Main.qml                   Application window (3-panel SplitView)
  ConfigPanel.qml            Left panel: settings and targets
  MonitorPanel.qml           Centre panel: live touch table
  LogPanel.qml               Right panel: scrolling OSC log
  components/
    StatusBar.qml            Bottom status bar
    TargetRow.qml            One OSC output target row
    TransformGroup.qml       Flip/scale/offset controls
    RealSpinBox.qml          Float-capable SpinBox
tuio_bridge.spec             PyInstaller build spec
build.bat                    One-click build script (Windows)
```

---

## Building a Standalone Exe

```bash
# Install build dependency once
pip install pyinstaller

# Build (or double-click build.bat)
pyinstaller tuio_bridge.spec --clean --noconfirm
```

Output is in `dist/TUIO Bridge/`. Zip the entire folder to distribute.

---

## Credits

© 2026 [Antony Bailey](https://github.com/blackdown)
