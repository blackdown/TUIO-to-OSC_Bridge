# Blackdown Bridge Projects — Hardware Survey
**Prepared:** 2026-06-27  
**Purpose:** Feed into Flux.ai PCB/hardware design for a dedicated compact host box  
**Account:** github.com/blackdown (Antony Bailey, Blackdown Solutions)

> **Note on data quality:** The current session's GitHub file access is scoped to `TUIO-to-OSC_Bridge` only. That project has full source-level analysis. All other projects are documented from repository metadata (name, language, last push date) plus protocol inference from naming conventions — sections marked ⚠️ _Inferred_ need verification once full repo access is available.

---

## Repository Overview — All 20 Repos

| Repo | Visibility | Language | Last Push | Category |
|------|-----------|----------|-----------|----------|
| TUIO-to-OSC_Bridge | public | Python | 2026-04-12 | **Bridge** |
| emotiv-pixera-bridge | private | Python | 2026-04-29 | **Bridge** |
| psn_tuio_mapper_gui | public | Python | 2026-06-17 | **Bridge** |
| Human-Tracker_YOLO-to-OSC | private | Python | 2026-03-04 | **Bridge** |
| Vision-Model-to-OSC | private | Python | 2025-12-19 | **Bridge** |
| Cascade_System-OSCbridge | private | Python | 2025-10-03 | **Bridge** |
| MPE-to-OSC | private | C++ | 2025-11-28 | **Bridge** |
| pixera-pipeline-mapper | private | Python | 2026-05-12 | **Bridge** |
| notch-mpe-player | private | C++ | 2026-01-23 | Bridge/Tool |
| Cascade_System-PiPico | private | Python | 2025-10-03 | **Hardware** |
| NOTCH-Brightsign | private | HTML | 2026-02-24 | Integration |
| Notch-Deadline-Plugin-CmdLineRenderer | public | Python | 2026-04-08 | Render tool |
| NOTCH-Deadline-cloud-submission | private | PowerShell | 2025-10-17 | Render tool |
| NOTCH-Agents | private | Python | 2026-02-26 | Render/AI |
| Notch-Render-CLI-Generator | private | HTML | 2025-09-09 | Render tool |
| NOTCH-Data-Tool | public | HTML | 2025-05-13 | Data tool |
| notch-demo-matrix | private | HTML | 2025-08-21 | Demo |
| living-textures | private | — | 2026-05-22 | Unknown |
| cypherbot-mailpipe | private | Python | 2026-03-02 | Utility |
| video-downloader | public | Python | 2026-04-12 | Utility |

---

## Bridge / Middleware Projects — Detailed Profiles

---

### 1. TUIO-to-OSC_Bridge
**`github.com/blackdown/TUIO-to-OSC_Bridge`** | Public | Python | Last push: 2026-04-12  
_Full source analysis — highest confidence_

**Purpose**  
Receives TUIO 1.1 touch/object/blob data (as OSC bundles over UDP) from any TUIO-capable touchscreen, tracker, or simulator, unpacks the protocol, and re-emits clean flat individual OSC messages to downstream targets. Primary targets: Pixera, TouchDesigner, Notch, and any OSC-capable application. Raw TUIO bundles are incompatible with most media server OSC inputs; this bridge normalises them.

**Protocol stack**
- **In:** TUIO 1.1 over OSC/UDP — all 9 profiles (`/tuio/2Dcur`, `/tuio/2Dobj`, `/tuio/2Dblb`, `25D*`, `3D*`)
- **Out:** Individual OSC messages over UDP — one attribute per datagram, to up to 8 configurable targets

**Language and runtime**
- Python 3.12+ (uses `match` statement — 3.10 minimum, 3.12 specified)
- PySide6 ≥ 6.8 (Qt6 GUI via QML/Material theme)
- python-osc ≥ 1.8
- PyInstaller for `.exe` distribution

**Direction**  
Bidirectional in function: server (listens on UDP 3333), client (emits OSC to targets). The bridge itself is always the intermediary.

**Current state**  
Working and released. Standalone `.exe` available via GitHub Releases. README is complete, changelog present, build pipeline (PyInstaller spec + `build.bat`) in place. Actively developed (last push April 2026).

**Network requirements**
| Interface | Protocol | Port | Direction |
|-----------|----------|------|-----------|
| `0.0.0.0` bind | UDP | **3333** | IN (TUIO listen) |
| Configurable per-target | UDP | **7000** (default) | OUT (OSC to Pixera etc.) |
| Additional targets | UDP | User-configured | OUT (up to 8 targets) |

Default OSC output port is 7000 (Pixera's DirectNetworkOsc default). Targets are IP:port pairs, so the host needs IP reachability to all downstream devices.

**Resource profile**
- Lightweight: event-driven threaded architecture (one daemon thread for UDP listener, one for engine dispatch, main thread for Qt GUI)
- Queue-based frame processing — no busy-wait
- Maximum 20 simultaneous tracked objects (configurable, max 100)
- GUI renders a live monitor table and scrolling OSC log — requires a display or must be adapted for headless operation
- PyInstaller `.exe` is Windows-only; running from source on Linux/macOS is feasible with Python 3.12 + PySide6

**Hardware interface requirements**  
Ethernet only. No serial, USB, GPIO, or audio. The TUIO source (touchscreen, tracker) connects over the network.

**Headless note**  
Currently a desktop GUI application. For a headless host box this would need either a lightweight display (or virtual framebuffer), or a refactor of the backend to a service with a remote config interface. Backend modules (`tuio_receiver.py`, `bridge_engine.py`, `config_manager.py`) are cleanly decoupled from the GUI and could be run standalone.

---

### 2. emotiv-pixera-bridge
**`github.com/blackdown/emotiv-pixera-bridge`** | Private | Python | Last push: 2026-04-29  
⚠️ _Inferred from name and domain knowledge — verify against source_

**Purpose**  
Bridges an Emotiv EEG headset (BCI — Brain-Computer Interface) to the Pixera media server. The Emotiv Cortex API streams cognitive/biometric data (mental commands, performance metrics, facial expressions, motion) that is likely re-emitted as OSC or JSON-RPC to Pixera for real-time VFX control.

> This may be related to or evolved from the `bridge-cortex-client` Python project you referenced at `C:\Users\Antony Bailey\Documents\Github\bridge-cortex-client`.

**Protocol stack** ⚠️
- **In:** Emotiv Cortex API — WebSocket JSON-RPC 2.0 (localhost:6868 or cloud)
- **Out:** OSC/UDP to Pixera, or Pixera JSON-RPC over TCP (port 1401 or WebSocket)

**Language and runtime** ⚠️
- Python (version TBC from source)
- Likely: `websocket-client` or `websockets`, `python-osc` or Pixera SDK

**Direction** — Client (to Cortex API) + Client (to Pixera) — fully outbound from bridge

**Current state** — Active development (last push April 2026, most recently pushed of all bridge projects)

**Network requirements** ⚠️
| Interface | Protocol | Port | Direction |
|-----------|----------|------|-----------|
| localhost | WebSocket/JSON-RPC | **6868** | OUT (Emotiv Cortex API) |
| Pixera host | OSC/UDP or JSON-RPC | **7000 / 1401** | OUT |

**Resource profile** ⚠️  
Low CPU. WebSocket client is async/event-driven. No GPU required.

**Hardware interface requirements** ⚠️  
Emotiv headset connects via USB dongle (Emotiv USB receiver) or Bluetooth. The host box will need a **USB port** for the Emotiv receiver dongle.

---

### 3. psn_tuio_mapper_gui
**`github.com/blackdown/psn_tuio_mapper_gui`** | Public | Python | Last push: 2026-06-17  
⚠️ _Inferred from name — source is public, no README description provided_

**Purpose**  
Maps PSN (PosiStageNet) position tracking data to TUIO format. PSN is a stage automation position tracking protocol used with systems like disguise, Pixera, and MA lighting. This bridge translates performer/prop position data from a PSN server into TUIO events, likely for consumption by the TUIO-to-OSC_Bridge or directly by touch-aware applications.

**Protocol stack** ⚠️
- **In:** PSN (PosiStageNet) — UDP multicast, typically `236.10.10.10:56565`
- **Out:** TUIO 1.1 OSC bundles over UDP (port 3333 or configurable)

**Language and runtime** ⚠️
- Python (version TBC)
- Likely: `python-osc`, possibly custom PSN decoder (PSN is not widely packaged)
- GUI component (indicated by `_gui` suffix) — likely tkinter or PyQt/PySide

**Direction** — Server/client bridge: PSN listener + TUIO emitter

**Current state** — Most recently updated (June 2026), actively developed

**Network requirements** ⚠️
| Interface | Protocol | Port | Direction |
|-----------|----------|------|-----------|
| Multicast group | UDP | **56565** (PSN standard) | IN |
| Localhost / target | UDP | **3333** | OUT (to TUIO-to-OSC_Bridge) |

Host needs multicast-capable Ethernet interface (IGMP). If PSN server and this bridge run on the same host as TUIO-to-OSC_Bridge, port 3333 loop-back is used.

**Hardware interface requirements** ⚠️  
Ethernet with multicast support. No additional hardware.

---

### 4. Human-Tracker_YOLO-to-OSC
**`github.com/blackdown/Human-Tracker_YOLO-to-OSC`** | Private | Python | Last push: 2026-03-04  
⚠️ _Inferred from name_

**Purpose**  
Uses YOLO (You Only Look Once) computer vision to detect and track humans in a camera feed, then emits their positions/bounding boxes as OSC messages to downstream targets (Pixera, Notch, TouchDesigner, etc.).

**Protocol stack** ⚠️
- **In:** Camera feed — USB webcam, IP camera (RTSP), or capture card
- **Out:** OSC over UDP (position, bounding box, confidence, track ID)

**Language and runtime** ⚠️
- Python 3.10+
- Likely: `ultralytics` (YOLOv8/YOLOv11), `opencv-python`, `python-osc`
- Optional: CUDA for GPU inference

**Direction** — Server/client: camera consumer + OSC emitter

**Current state** — Last updated March 2026, likely functional

**Network requirements** ⚠️
| Interface | Protocol | Port | Direction |
|-----------|----------|------|-----------|
| IP camera (optional) | RTSP | varies | IN |
| OSC target | UDP | configurable | OUT |

**Resource profile** ⚠️  
**HIGH CPU / GPU.** YOLO inference at useful frame rates (≥15fps) requires:
- CPU-only: modern multi-core CPU, ~2–4 cores saturated, latency ~50–200ms per frame
- With GPU: CUDA-capable NVIDIA GPU strongly recommended for real-time performance
- A dedicated host box running this alongside other bridges **must have a discrete GPU or NPU**, or accept reduced frame rates

**Hardware interface requirements** ⚠️  
USB (camera or capture card), or RTSP-capable Ethernet. If a physical camera is attached directly: **USB 3.0 port required**.

---

### 5. Vision-Model-to-OSC
**`github.com/blackdown/Vision-Model-to-OSC`** | Private | Python | Last push: 2025-12-19  
⚠️ _Inferred from name_

**Purpose**  
Similar to YOLO-to-OSC but uses a broader "vision model" — possibly a different detection model (MediaPipe, SAM, DINO, or a custom model), or a higher-level computer vision pipeline that outputs structured data as OSC. May handle pose estimation, object classification, or depth sensing.

**Protocol stack** ⚠️
- **In:** Camera / image stream
- **Out:** OSC over UDP

**Language and runtime** ⚠️
- Python 3.10+
- Likely: `mediapipe`, `torch`/`torchvision`, or `transformers` + `python-osc`

**Direction** — Camera consumer + OSC emitter

**Current state** — Last updated December 2025, possibly older/experimental relative to YOLO project

**Resource profile** ⚠️  
**HIGH CPU / GPU** — same considerations as Human-Tracker above. If both vision projects run simultaneously on the host box, a capable discrete GPU becomes mandatory.

**Hardware interface requirements** ⚠️  
USB (camera), or RTSP Ethernet.

---

### 6. Cascade_System-OSCbridge
**`github.com/blackdown/Cascade_System-OSCbridge`** | Private | Python | Last push: 2025-10-03  
⚠️ _Inferred from name_

**Purpose**  
OSC bridge component of the "Cascade System" — appears to be a larger bespoke production control system. This module likely aggregates or routes OSC messages between components of the Cascade system, possibly including the Pi Pico hardware node (see project 7 below).

**Protocol stack** ⚠️
- **In/Out:** OSC over UDP — router/hub pattern likely

**Language and runtime** ⚠️
- Python

**Direction** — Bidirectional OSC router

**Current state** — Last updated October 2025, may be superseded by newer projects

**Network requirements** ⚠️
- OSC UDP on configurable ports, likely internal/localhost routing

**Hardware interface requirements** ⚠️  
Likely communicates with the Pi Pico via USB serial (`/dev/ttyACM0` or similar).

---

### 7. Cascade_System-PiPico
**`github.com/blackdown/Cascade_System-PiPico`** | Private | Python | Last push: 2025-10-03  
⚠️ _Inferred from name_

**Purpose**  
MicroPython firmware for a Raspberry Pi Pico, forming the hardware interface node of the Cascade System. The Pi Pico likely reads physical sensors (buttons, encoders, ADC, GPIO) and/or drives outputs (LEDs, relays), communicating with the host via USB serial.

**Language and runtime**  
MicroPython (runs on the Pico, not the host box)

**Direction** — Hardware I/O node; USB-serial bridge to host

**Hardware interface requirements**  
The **host box requires a USB port** to connect the Pi Pico. The Pico itself is the hardware layer; the host runs the companion bridge software (`Cascade_System-OSCbridge`).

---

### 8. MPE-to-OSC
**`github.com/blackdown/MPE-to-OSC`** | Private | C++ | Last push: 2025-11-28  
⚠️ _Inferred from name_

**Purpose**  
Bridges MIDI Polyphonic Expression (MPE) — the extended MIDI standard for per-note pitch bend, pressure, and slide — to OSC. Allows MPE controllers (Roli Seaboard, Linnstrument, Expressive E Osmose, etc.) to drive OSC-capable visual/audio systems directly.

**Protocol stack** ⚠️
- **In:** MIDI (USB or DIN) — MPE channel layout (channels 2–16 per voice)
- **Out:** OSC over UDP

**Language and runtime** ⚠️
- C++ (compiled binary)
- Likely: JUCE, RtMidi, or liblo
- Build toolchain: CMake + compiler

**Direction** — MIDI client → OSC emitter

**Current state** — Last updated November 2025

**Network requirements** ⚠️
- OSC UDP output on configurable port

**Hardware interface requirements** ⚠️  
**USB MIDI interface required** (or built-in USB MIDI if the controller supports class-compliant USB MIDI). Host needs a USB port or physical MIDI DIN port (via USB-MIDI adapter).

**Resource profile** ⚠️  
Very low — C++ MIDI event handler. Negligible CPU.

---

### 9. pixera-pipeline-mapper
**`github.com/blackdown/pixera-pipeline-mapper`** | Private | Python | Last push: 2026-05-12  
⚠️ _Inferred from name_

**Purpose**  
Maps or manages signal chains, content routing, or layer configurations in the Pixera media server. Likely uses Pixera's JSON-RPC or WebSocket API to programmatically reconfigure the server's processing pipeline — possibly for show-state management, preset recall, or automated routing.

**Protocol stack** ⚠️
- **Out:** Pixera JSON-RPC over TCP or WebSocket (port 1401 or 9999)

**Language and runtime** ⚠️
- Python

**Direction** — Client to Pixera server

**Current state** — Active (May 2026)

**Network requirements** ⚠️
| Interface | Protocol | Port | Direction |
|-----------|----------|------|-----------|
| Pixera host | JSON-RPC/TCP or WebSocket | **1401 / 9999** | OUT |

---

### 10. notch-mpe-player
**`github.com/blackdown/notch-mpe-player`** | Private | C++ | Last push: 2026-01-23  
⚠️ _Inferred from name_

**Purpose**  
Plays back MPE data (MIDI Polyphonic Expression or possibly motion/performance capture data) inside Notch real-time VFX blocks. Likely a Notch plugin (DLL) or companion utility that feeds expressive performance data into Notch's parameter system.

**Language and runtime** ⚠️
- C++ — likely compiled as a Notch plugin DLL or standalone executable

**Direction** — Playback/driver for Notch

**Current state** — Last updated January 2026

**Hardware interface requirements** ⚠️  
Runs on the Notch machine (not necessarily the bridge host). May use MIDI or OSC to receive data from MPE-to-OSC.

---

### 11. NOTCH-Brightsign
**`github.com/blackdown/NOTCH-Brightsign`** | Private | HTML/JS | Last push: 2026-02-24  
⚠️ _Inferred from name_

**Purpose**  
Integration layer between Notch real-time VFX blocks and BrightSign media players. BrightSign players can run HTML5 content and expose a local webserver/WebSocket API; this integration likely provides parameter exchange or show-state synchronisation between Notch and BrightSign.

**Protocol stack** ⚠️
- BrightSign UDP/WebSocket API, or Notch OSC input
- HTML/JS (browser-based or BrightSign runtime)

**Direction** — Integration/sync

**Note:** Runs on BrightSign hardware — not a candidate for the host box.

---

## Supporting Tools (Not Bridge Processes)

These run as pipeline tooling rather than real-time bridges and are unlikely to need a dedicated process slot on the host box:

| Project | Purpose | Runtime | Notes |
|---------|---------|---------|-------|
| `Notch-Deadline-Plugin-CmdLineRenderer` | Deadline render submission for Notch | Python | Render farm tool, not real-time |
| `NOTCH-Deadline-cloud-submission` | Cloud render submission | PowerShell | Windows-only, render farm |
| `NOTCH-Agents` | AI agents for Notch workflow | Python | Likely offline/batch |
| `Notch-Render-CLI-Generator` | Generate CLI render commands | HTML/JS | Web tool |
| `NOTCH-Data-Tool` | Weather feed CSV generator | HTML/JS | Web tool |
| `video-downloader` | yt-dlp wrapper | Python | Utility |
| `cypherbot-mailpipe` | Mail pipeline | Python | Utility |
| `living-textures` | Unknown | — | Needs investigation |
| `notch-demo-matrix` | Demo content | HTML | Demo |

---

## Consolidated Hardware Requirements

### Concurrent Processes

| Process | Language | CPU Load | GPU? | USB? | MIDI? |
|---------|---------|---------|------|------|-------|
| TUIO-to-OSC_Bridge | Python/Qt | Low | No | No | No |
| emotiv-pixera-bridge | Python | Low | No | Yes (dongle) | No |
| psn_tuio_mapper_gui | Python | Low | No | No | No |
| Human-Tracker_YOLO-to-OSC | Python | **High** | **Yes** | Yes (camera) | No |
| Vision-Model-to-OSC | Python | **High** | **Yes** | Yes (camera) | No |
| Cascade_System-OSCbridge | Python | Low | No | Yes (Pico) | No |
| MPE-to-OSC | C++ | Very Low | No | Yes (MIDI) | Yes |
| pixera-pipeline-mapper | Python | Low | No | No | No |

**Total simultaneous bridge processes: 8** (assuming all run concurrently)  
**Of those, 2 require GPU inference** (YOLO + Vision model)

---

### Runtime Dependencies

| Dependency | Version | Required by |
|-----------|---------|-------------|
| Python | **3.12+** | TUIO bridge (confirmed); likely all Python projects |
| PySide6 | ≥ 6.8 | TUIO bridge (confirmed); psn_tuio_mapper_gui (likely) |
| python-osc | ≥ 1.8 | TUIO bridge (confirmed); all OSC-output Python bridges |
| ultralytics (YOLOv8+) | latest | Human-Tracker (⚠️ inferred) |
| opencv-python | latest | YOLO + Vision bridges (⚠️ inferred) |
| websockets / websocket-client | latest | emotiv-pixera-bridge (⚠️ inferred) |
| torch / torchvision | latest + CUDA | Vision-Model-to-OSC (⚠️ inferred) |
| C++ build toolchain | — | MPE-to-OSC, notch-mpe-player (pre-compiled binaries likely) |
| Node.js | TBC | None confirmed — all JS/HTML projects appear browser-based |

**No Node.js runtime confirmed as required.** All real-time bridges are Python or C++.

---

### Network Interface Requirements

| Requirement | Detail |
|------------|--------|
| Ethernet ports | **Minimum 2 recommended** — one for upstream (TUIO/PSN sources, show network) and one for downstream (Pixera, Notch, TouchDesigner on production LAN). Single port with managed switch is acceptable. |
| Multicast support | Required for PSN (PosiStageNet) — IGMP-capable NIC and switch |
| Bandwidth | Very low — all protocols are lightweight UDP datagrams. Gigabit Ethernet is ample. |
| WiFi | Not required for bridge operation; optional for management access |
| IP cameras | If YOLO/Vision bridges pull RTSP feeds from IP cameras, these need reachability on the show LAN |

**Ports that must be open/bound on the host box:**

| Port | Protocol | Direction | Service |
|------|----------|-----------|---------|
| 3333 | UDP | IN | TUIO listen (TUIO-to-OSC_Bridge) |
| 56565 | UDP multicast | IN | PSN listen (psn_tuio_mapper_gui) |
| 6868 | WebSocket | OUT | Emotiv Cortex API (localhost if Cortex runs on same box) |
| 7000 | UDP | OUT | OSC to Pixera (TUIO bridge default) |
| 1401 / 9999 | TCP/WebSocket | OUT | Pixera JSON-RPC (pixera-pipeline-mapper) |
| Various | UDP | OUT | OSC to Notch, TouchDesigner, other targets |

---

### Hardware Interface Requirements

| Interface | Required for | Count |
|-----------|-------------|-------|
| **USB-A 3.0** | Emotiv receiver dongle, Pi Pico, USB camera(s), MIDI interface | Minimum **4 ports** |
| **USB-C** | Optional — camera or MIDI device alternate connector | 1 recommended |
| **GPIO / I2C / SPI** | None confirmed — Pi Pico is the hardware layer, not the host | None required on host |
| **Audio** | None confirmed | Not required |
| **Display output** | Required if running TUIO Bridge and psn_tuio_mapper_gui as Qt GUIs; optional if adapted to headless services | 1× DisplayPort or HDMI |
| **Serial / DIN MIDI** | Only if MPE-to-OSC uses DIN MIDI rather than USB | TBC |

---

### Compute and Platform Requirements

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| **CPU** | 4-core x86-64 | 8-core (AMD Ryzen or Intel Core — to handle YOLO + multiple Python threads simultaneously) |
| **RAM** | 8 GB | 16 GB (YOLO models are ~600MB–6GB depending on variant; PySide6 + multiple processes add up) |
| **GPU** | None (YOLO runs on CPU slowly) | **Discrete GPU with CUDA** — NVIDIA RTX 3060 or better for real-time YOLO + Vision model inference |
| **Storage** | 32 GB SSD | 64 GB (OS + Python envs + YOLO model weights) |
| **OS** | Linux (Ubuntu 22.04+) or Windows 10/11 | Ubuntu 22.04 LTS headless for service deployment; Windows if GUI apps are kept as-is |
| **Platform** | x86-64 | x86-64 (CUDA requirement rules out ARM Cortex-A for GPU projects; Raspberry Pi CM5 is insufficient) |

---

### Real-Time / Latency Requirements

| Project | Latency sensitivity | Notes |
|---------|-------------------|-------|
| TUIO-to-OSC_Bridge | **Medium** — touch tracking; <20ms end-to-end desirable | Thread-based, queue depth 512 frames — adequate |
| psn_tuio_mapper_gui | **Medium** — stage position tracking | PSN typically 50Hz |
| emotiv-pixera-bridge | Low — biometric data changes slowly | WebSocket polling |
| YOLO / Vision bridges | **Low–Medium** — visual tracking; 15–30fps target | GPU inference latency is the bottleneck |
| MPE-to-OSC | **High** — musical performance; <5ms desirable | C++ MIDI handler — OS scheduling is the constraint; may need real-time scheduling priority |
| pixera-pipeline-mapper | Low — pipeline/preset control | Event-driven, not continuous |
| Cascade_System-OSCbridge | Medium | Dependent on Cascade system requirements |

**MPE-to-OSC is the highest real-time demand** — a real-time Linux kernel (`PREEMPT_RT`) patch or at minimum high-priority thread scheduling is advisable for musical responsiveness.

---

### Summary for Flux.ai Design Session

**Form factor driver:** The GPU requirement (for YOLO + Vision-Model) is the dominant constraint. A compact host box will need either:
1. **Full desktop GPU** (PCIe x16 slot) — pushes form factor to Mini-ITX at minimum
2. **NVIDIA Jetson Orin** — ARM-based, has onboard GPU/NPU, but CUDA support for Python ML is confirmed; PySide6/Qt GUI apps may need adaptation or a virtual display
3. **Separate machines** — run vision-heavy bridges on a GPU machine, lightweight OSC bridges on a smaller SBC

**Minimum viable single-box spec:**
- Mini-ITX or Micro-ATX
- AMD Ryzen 7 5700U (integrated Radeon) or Intel Core i7/i9 12th gen
- Discrete GPU: NVIDIA RTX 3060 12GB (good CUDA + VRAM headroom for two vision models)
- 32 GB DDR4/DDR5
- 256 GB NVMe SSD
- 4× USB-A 3.0, 1× USB-C
- 2× 2.5GbE or 1× 2.5GbE + 1× 1GbE (show LAN separation)
- DisplayPort or HDMI (for Qt GUI apps, or remote management)
- No audio I/O required (MIDI is USB)
- Small chassis: Fractal Node 202 or equivalent

**If GPU bridges are offloaded to a separate inference box:**
- Host box drops to NUC/SBC class (Intel NUC 13 Pro or similar)
- 16 GB RAM, 4-core, integrated graphics, 4× USB, 2× Ethernet — sufficient for the remaining 6 lightweight Python bridges

---

## Open Questions for Verification

1. **emotiv-pixera-bridge** — Does it require the Emotiv Cortex application to run locally (adding another process), or does it connect to a remote Cortex server? Does it need Bluetooth in addition to USB dongle?
2. **Vision-Model-to-OSC** — What model/framework exactly? This determines GPU VRAM requirement.
3. **psn_tuio_mapper_gui** — Does it output TUIO (feeding into TUIO-to-OSC_Bridge) or direct OSC? If TUIO, these two are chained processes, not separate.
4. **MPE-to-OSC** — USB MIDI or DIN MIDI? What OSC target port?
5. **Cascade_System-OSCbridge + PiPico** — Is this still an active deployment or superseded by newer projects?
6. **TUIO-to-OSC_Bridge headless** — Confirmed Windows GUI currently. Decision needed: adapt backend as a Linux service, or run under Xvfb virtual display on Linux, or keep on Windows?
7. **living-textures** — No language detected. Needs investigation.
8. **bridge-cortex-client** (mentioned in brief) — Is this the same repo as `emotiv-pixera-bridge`, or a separate project not yet on GitHub?

---

_End of survey. Document should be updated once full source access is available for private repositories._
