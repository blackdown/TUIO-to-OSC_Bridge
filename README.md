# TUIO Bridge

A cross-platform desktop application that receives TUIO 1.1 touch data over UDP, displays it in a live monitor, and re-emits clean individual OSC messages to up to four downstream targets — primarily Pixera, but also TouchDesigner, Notch, or any OSC-capable application.

**Platforms:** Windows 10/11 · macOS (including Apple Silicon ARM) · Linux

---

## Why this exists

Raw TUIO arrives as multi-argument OSC bundles that most media server OSC inputs (including Pixera's DirectNetworkOsc module) cannot parse natively. TUIO Bridge unpacks the protocol and re-emits flat, well-named individual OSC messages — one attribute per message — that every OSC target can consume directly.

---

## Requirements

- Python 3.10 or later
- PySide6 ≥ 6.6
- python-osc ≥ 1.8

```bash
pip install -r requirements.txt
```

No compiled extensions — works on Apple Silicon ARM natively.

---

## Running

```bash
python main.py
```

The app starts listening on UDP port 3333 immediately and writes its config to `tuio_bridge_config.json` on first launch.

---

## OSC Output Format

Each active touch cursor emits these messages per frame:

```
/tuio/cursor/{id}/x       float   normalised 0.0–1.0
/tuio/cursor/{id}/y       float   normalised 0.0–1.0
/tuio/cursor/{id}/x_vel   float
/tuio/cursor/{id}/y_vel   float
/tuio/cursor/{id}/accel   float
/tuio/cursor/{id}/alive   int     1 = active, 0 = removed
```

For fiducial objects (`/tuio/2Dobj`) additionally:

```
/tuio/object/{id}/class_id  int
/tuio/object/{id}/angle     float   radians
```

The address base path (`/tuio/cursor`) is configurable in the GUI. The `{id}` token is always substituted with the session ID integer.

---

## Per-Target Transforms

Each of the four output targets supports independent:

| Transform | Description |
|-----------|-------------|
| Flip X    | Mirror left/right (1 − x) |
| Flip Y    | Mirror top/bottom (1 − y) |
| Swap X↔Y  | Exchange x and y axes |
| Scale X/Y | Multiply normalised value by factor |
| Offset X/Y | Add fixed offset after scaling |

---

## Config File

Settings auto-save to `tuio_bridge_config.json` on close. All fields are human-readable and can be edited manually. See `backend/config_manager.py` for the full schema.

---

## Project Structure

```
main.py                    Entry point
backend/
  config_manager.py        JSON config persistence
  tuio_receiver.py         TUIO 1.1 UDP listener and parser
  bridge_engine.py         Transform logic and OSC dispatcher
  cursor_model.py          Qt list model for live monitor table
  log_model.py             Qt list model for OSC log panel
  bridge_controller.py     Root QML-exposed controller
qml/
  Main.qml                 Application window (3-panel SplitView)
  ConfigPanel.qml          Left panel: settings
  MonitorPanel.qml         Centre panel: live touch table
  LogPanel.qml             Right panel: scrolling OSC log
  components/
    StatusBar.qml          Bottom status bar
    TargetRow.qml          One OSC output target row
    TransformGroup.qml     Flip/scale/offset controls
    DoubleSpinBox.qml      Float-capable SpinBox
```

---

## Packaging with PyInstaller

```bash
pip install pyinstaller
pyinstaller --windowed --name "TUIO Bridge" --add-data "qml:qml" main.py
```

The `--windowed` flag suppresses the terminal on macOS and Windows.
