# Protocol Conversion & Bridge Apps Bundle

This archive contains core source files from 4 bridge applications for protocol conversion.

## Included Repositories

### 1. TUIO-to-OSC_Bridge (Python/PySide6)
**Purpose**: Converts TUIO 1.1 touch/object/blob data to clean OSC messages
**Platform**: Windows 10/11 (.exe available)
**Key Files**:
- `main.py` - Entry point, QML application setup
- `requirements.txt` - Python dependencies
- `backend/` - TUIO receiver, OSC dispatcher, transforms
- `qml/` - Qt UI (config, monitor, log panels)

**Usage**: Listens on UDP 3333, re-emits OSC with per-target transforms (flip, scale, offset)

---

### 2. PSN → TUIO Mapper GUI (Python/customtkinter)
**Purpose**: Bridges Naostage Kratos PSN tracker data to Notch via TUIO
**Platform**: Windows (standalone .exe)
**Key Files**:
- `app.py` - Main GUI window (customtkinter)
- `bridge.py` - PSN receiver + TUIO BUNDLE sender
- `psn_to_tuio.py` - Headless version of same logic
- `config.py` - Config persistence

**Usage**: Receives PSN multicast (236.10.10.10:56565), normalizes stage coordinates, sends TUIO 2Dcur bundles

---

### 3. MPE-to-OSC (C++/JUCE)
**Purpose**: MIDI Polyphonic Expression (MPE) controller → OSC audio-visual bridge
**Plugin Types**: VST3, AU, Standalone
**Key Features**:
- 15-voice polyphony with per-note pressure, pitch bend, timbre
- Dual MPE modes (standard + Expressive E Osmose high-resolution)
- Sends per-voice OSC messages (note, velocity, pressure, pitch, timbre)
- Modern Ableton-inspired UI

**OSC Output**: `/prefix/1/`, `/prefix/2/`, etc. with `noteon`, `noteoff`, `note`, `velocity`, `pressure`, `pitch`, `timbre`, `relvel`

---

### 4. Emotiv → Pixera Bridge (Python)
**Purpose**: EEG/metrics from Emotiv Cortex → Pixera Control OSC + WebSocket rebroadcast
**Platform**: Windows/macOS/Linux
**Key Files**:
- `app.py` - Main GUI (customtkinter with status/metrics display)
- `bridge.py` - Cortex WebSocket client, data translator, Pixera dispatcher
- `translator.py` - Cortex JSON → OSC address mapping
- `config.py` - Credentials and endpoint config

**Streams Supported**: MET (emotions), DEV (device), EEG, POW (band power)
**Rebroadcast**: Raw Cortex JSON on WebSocket (default :8080)

---

## Quick Setup

### TUIO-to-OSC_Bridge
```bash
cd TUIO-to-OSC_Bridge
pip install -r requirements.txt
python main.py
```

### PSN → TUIO Mapper
```bash
cd psn_tuio_mapper_gui
pip install customtkinter pypsn python-osc
python app.py
```

### Emotiv → Pixera Bridge
```bash
cd emotiv-pixera-bridge
git clone --recurse-submodules .
pip install -r requirements.txt
python app.py
```

### MPE-to-OSC
Requires JUCE framework and CMake. See `MPEProject/` README.

---

## Common Dependencies

**Python Apps**:
- `python-osc>=1.8.0` - OSC protocol
- `customtkinter` - Modern UI toolkit
- `PySide6>=6.8` - Qt for TUIO Bridge

**C++ (MPE)**:
- JUCE 7+
- CMake 3.21+
- melatonin_blur, melatonin_inspector (UI modules)

---

## Architecture Overview

```
INPUT PROTOCOL → [Bridge Logic] → OUTPUT PROTOCOL (OSC)

TUIO            → [Unpack/Transform]  → OSC (per-voice)
PSN             → [Normalize coords]  → TUIO
MPE/MIDI        → [Voice manager]     → OSC (per-voice)
Cortex JSON     → [Stream parse]      → OSC + WebSocket
```

---

## File Structure in This Bundle

```
protocol-bridges/
├── TUIO-to-OSC_Bridge/
│   ├── main.py
│   ├── requirements.txt
│   ├── README.md
│   └── backend/
│       ├── bridge_controller.py
│       ├── tuio_receiver.py
│       ├── bridge_engine.py
│       └── ...
├── psn_tuio_mapper_gui/
│   ├── app.py
│   ├── bridge.py
│   ├── psn_to_tuio.py
│   ├── readme.md
│   └── ...
├── MPE-to-OSC/
│   ├── README.md
│   ├── MPEProject/
│   │   └── Source/
│   │       ├── PluginProcessor.cpp
│   │       ├── PluginEditor.cpp
│   │       └── ...
│   └── ...
├── emotiv-pixera-bridge/
│   ├── app.py
│   ├── bridge.py
│   ├── translator.py
│   ├── README.md
│   └── ...
└── ARCHIVE_MANIFEST.md (this file)
```

---

## License

- **TUIO-to-OSC_Bridge**: © 2026 Antony Bailey
- **PSN → TUIO Mapper**: Custom (see repo)
- **MPE-to-OSC**: GNU GPL 3.0 (with JUCE commercial licensing)
- **Emotiv → Pixera Bridge**: Custom

---

## Support & Issues

Each repository has its own GitHub issues tracker. See the individual READMEs for repo links.
