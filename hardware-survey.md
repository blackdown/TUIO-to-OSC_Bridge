# Blackdown Bridge Projects — Hardware Survey
**Prepared:** 2026-06-27  
**Scope:** Protocol conversion bridges only (ML/vision projects excluded)  
**Purpose:** Feed into Flux.ai PCB/hardware design for a dedicated compact host box  
**Account:** github.com/blackdown (Antony Bailey, Blackdown Solutions)

> **Note on data quality:** GitHub file access for this session is scoped to `TUIO-to-OSC_Bridge`. That project has full source-level analysis. All other projects are documented from repository metadata plus protocol inference — sections marked ⚠️ _Inferred_ need verification once full repo access is available.

---

## Projects in Scope

| # | Repo | Protocol In | Protocol Out | Language | Last Push |
|---|------|------------|-------------|---------|-----------|
| 1 | `TUIO-to-OSC_Bridge` | TUIO 1.1 / OSC+UDP | OSC / UDP | Python | 2026-04-12 |
| 2 | `psn_tuio_mapper_gui` | PSN / UDP multicast | TUIO / OSC+UDP | Python | 2026-06-17 |
| 3 | `emotiv-pixera-bridge` | Emotiv Cortex / WebSocket | OSC or JSON-RPC / TCP | Python | 2026-04-29 |
| 4 | `Cascade_System-OSCbridge` | OSC / UDP | OSC / UDP | Python | 2025-10-03 |
| 5 | `MPE-to-OSC` | MIDI MPE / USB | OSC / UDP | C++ | 2025-11-28 |
| 6 | `pixera-pipeline-mapper` | Internal / event | Pixera JSON-RPC / TCP | Python | 2026-05-12 |
| — | `Cascade_System-PiPico` | GPIO / I2C / ADC | USB serial | MicroPython | 2025-10-03 |

The Pi Pico project is firmware that runs on the microcontroller itself, not on the host box — but it determines the USB serial requirement on the host.

---

## Bridge Profiles

---

### 1. TUIO-to-OSC_Bridge
**`github.com/blackdown/TUIO-to-OSC_Bridge`** | Public | Python  
_Full source analysis_

**Purpose**  
Receives TUIO 1.1 touch/object/blob data as OSC bundles over UDP from any TUIO-capable touchscreen, tracker, or simulator. Unpacks the multi-argument bundles (which most media servers cannot parse natively) and re-emits clean flat individual OSC messages — one attribute per datagram — to up to 8 configurable downstream targets: Pixera, TouchDesigner, Notch, or any OSC application.

**Protocol stack**

| Layer | Detail |
|-------|--------|
| Transport in | UDP, bind `0.0.0.0:3333` |
| Protocol in | TUIO 1.1 — all 9 profiles: `2Dcur`, `2Dobj`, `2Dblb`, `25Dcur`, `25Dobj`, `25Dblb`, `3Dcur`, `3Dobj`, `3Dblb` |
| Transport out | UDP, per-target IP:port |
| Protocol out | Individual OSC messages (`/tuio/{type}/{id}/{attribute}`) |
| Config | JSON file (`tuio_bridge_config.json`) |

**Runtime**
- Python 3.12+
- PySide6 ≥ 6.8 (Qt6 / QML / Material — desktop GUI)
- python-osc ≥ 1.8

**Direction** — Bidirectional: UDP server (in) + UDP client (out)

**Current state** — Working and released. Standalone `.exe` available. Active development.

**Ports**

| Port | Proto | Dir | Notes |
|------|-------|-----|-------|
| 3333 | UDP | IN | TUIO listen; configurable |
| 7000 | UDP | OUT | Default OSC target (Pixera); configurable per target |
| up to 8 ports | UDP | OUT | Additional targets, user-configured |

**Architecture notes**  
Three threads: UDP listener (`ThreadingOSCUDPServer`), engine dispatch loop, Qt main thread. Queue-based handoff — no busy-wait. Max 20 tracked objects (configurable to 100).

**Headless concern**  
Currently a desktop Qt GUI. Backend modules (`tuio_receiver.py`, `bridge_engine.py`, `config_manager.py`) are cleanly separated from the QML frontend. Adapting to a headless service is a realistic refactor; alternatively runs under a virtual framebuffer on Linux.

---

### 2. psn_tuio_mapper_gui
**`github.com/blackdown/psn_tuio_mapper_gui`** | Public | Python  
⚠️ _Inferred_

**Purpose**  
Receives PosiStageNet (PSN) position tracking data from stage automation systems (disguise, MA lighting, Pixera tracking) and maps it to TUIO 1.1 format for consumption by TUIO-aware applications — most likely piped directly into the TUIO-to-OSC_Bridge above (chain: PSN → TUIO-to-OSC_Bridge → OSC targets).

**Protocol stack**

| Layer | Detail |
|-------|--------|
| Transport in | UDP multicast — standard PSN group `236.10.10.10`, port `56565` |
| Protocol in | PSN (PosiStageNet) — binary tracker frames |
| Transport out | UDP, localhost or LAN |
| Protocol out | TUIO 1.1 OSC bundles (port 3333, feeding TUIO-to-OSC_Bridge) |

**Runtime** ⚠️
- Python (version TBC)
- Likely `python-osc`, custom PSN decoder
- GUI (tkinter or PySide6 — `_gui` suffix)

**Direction** — Multicast listener + TUIO emitter

**Ports**

| Port | Proto | Dir | Notes |
|------|-------|-----|-------|
| 56565 | UDP multicast | IN | PSN standard; NIC must join multicast group |
| 3333 | UDP | OUT | To TUIO-to-OSC_Bridge (localhost loop-back if co-located) |

**Network note**  
Requires multicast-capable NIC and an IGMP-capable switch on the show LAN. If the PSN server and this bridge are on the same physical network segment, a managed switch with IGMP snooping is sufficient.

---

### 3. emotiv-pixera-bridge
**`github.com/blackdown/emotiv-pixera-bridge`** | Private | Python  
⚠️ _Inferred_

**Purpose**  
Bridges an Emotiv EPOC or EPOC X EEG headset (BCI) to the Pixera media server. The Emotiv Cortex SDK streams biometric and cognitive data (mental commands, facial expressions, performance metrics, motion) via a local WebSocket server. This bridge subscribes to those streams and forwards relevant data to Pixera as OSC or JSON-RPC for real-time parameter control.

**Protocol stack**

| Layer | Detail |
|-------|--------|
| Transport in | WebSocket (Emotiv Cortex API, `wss://localhost:6868`) |
| Protocol in | JSON-RPC 2.0 over WebSocket (Cortex API) |
| Transport out | UDP or TCP |
| Protocol out | OSC / UDP to Pixera, or Pixera JSON-RPC / TCP |

**Runtime** ⚠️
- Python 3.10+
- `websockets` or `websocket-client`, `python-osc`

**Direction** — WebSocket client (in) + OSC/JSON-RPC client (out)

**Hardware dependency**  
Emotiv headset connects via **USB receiver dongle** (Emotiv USB). The Emotiv Cortex desktop application must also run on the host (it provides the WebSocket server on port 6868) — this is a Windows/macOS application; Linux support for Cortex is limited.

**Ports**

| Port | Proto | Dir | Notes |
|------|-------|-----|-------|
| 6868 | WSS | OUT | Emotiv Cortex API (localhost) |
| 7000 or custom | UDP/TCP | OUT | Pixera OSC or JSON-RPC |

**Platform concern**  
Emotiv Cortex is officially supported on Windows and macOS only. If the host box runs Linux, Cortex must run on a separate Windows machine and the bridge connects to it over the network (Cortex supports remote WebSocket connections).

---

### 4. Cascade_System-OSCbridge
**`github.com/blackdown/Cascade_System-OSCbridge`** | Private | Python  
⚠️ _Inferred_

**Purpose**  
OSC routing hub within the "Cascade System" — a larger bespoke production control system. Likely aggregates OSC streams from multiple sources (including the Pi Pico hardware node via the companion `Cascade_System-PiPico` firmware), applies routing/filtering logic, and dispatches to downstream targets.

**Protocol stack**

| Layer | Detail |
|-------|--------|
| Transport in/out | UDP |
| Protocol in/out | OSC (router/hub pattern) |
| Serial link | USB serial to Raspberry Pi Pico (`/dev/ttyACM0` or COM port) |

**Runtime** ⚠️
- Python
- `python-osc`, `pyserial`

**Direction** — Bidirectional OSC router + USB serial bridge

**Ports** ⚠️

| Port | Proto | Dir | Notes |
|------|-------|-----|-------|
| Custom | UDP | IN | OSC from Pico bridge or other sources |
| Custom | UDP | OUT | OSC to show targets |

**Hardware dependency**  
USB connection to the Raspberry Pi Pico (running `Cascade_System-PiPico` MicroPython firmware). Host needs one USB-A port for the Pico.

---

### 5. MPE-to-OSC
**`github.com/blackdown/MPE-to-OSC`** | Private | C++  
⚠️ _Inferred_

**Purpose**  
Bridges MIDI Polyphonic Expression (MPE) — the per-note expressive extension to MIDI used by controllers like Roli Seaboard, Linnstrument, and Expressive E Osmose — to OSC. Allows expressive MIDI performance data (per-note pitch bend, pressure, slide) to drive OSC-capable visual or audio systems in real time.

**Protocol stack**

| Layer | Detail |
|-------|--------|
| Transport in | MIDI — USB class-compliant or DIN-5 via USB adapter |
| Protocol in | MIDI 1.0 with MPE channel layout (ch 2–16 per voice) |
| Transport out | UDP |
| Protocol out | OSC (per-note attribute messages) |

**Runtime** ⚠️
- C++ compiled binary
- Likely JUCE, RtMidi, or liblo
- Runs as a native executable; no Python/Node dependency

**Direction** — MIDI client → OSC emitter

**Ports** ⚠️

| Port | Proto | Dir | Notes |
|------|-------|-----|-------|
| — | MIDI/USB | IN | Via OS MIDI subsystem |
| Custom | UDP | OUT | OSC to target |

**Hardware dependency**  
USB MIDI interface or class-compliant USB MIDI controller. Host needs one USB-A port (or USB-C with adapter) for the MIDI device.

**Latency requirement — highest of all bridges**  
Musical performance demands <5ms end-to-end MIDI-to-OSC. C++ MIDI handler is fast; the bottleneck is OS scheduling. On Linux, setting the process to `SCHED_FIFO` with `chrt` is advisable. The host box OS should be a low-latency kernel (`linux-lowlatency` package on Ubuntu, or full `PREEMPT_RT` patch).

---

### 6. pixera-pipeline-mapper
**`github.com/blackdown/pixera-pipeline-mapper`** | Private | Python  
⚠️ _Inferred_

**Purpose**  
Programmatically manages signal chains, content routing, or preset states in the Pixera media server via its JSON-RPC API. Likely used for show-state management, automated layer routing, or scripted preset recall — event-driven rather than continuous streaming.

**Protocol stack**

| Layer | Detail |
|-------|--------|
| Transport | TCP or WebSocket |
| Protocol | Pixera JSON-RPC 2.0 API |

**Runtime** ⚠️
- Python
- `websockets` or `requests`

**Direction** — Client to Pixera server (outbound only)

**Ports** ⚠️

| Port | Proto | Dir | Notes |
|------|-------|-----|-------|
| 1401 or 9999 | TCP/WebSocket | OUT | Pixera JSON-RPC (version-dependent) |

**Resource profile** — Negligible. Event-driven, not continuous.

---

## Consolidated Hardware Requirements

### Process Count and Load

| Process | CPU load | RAM est. | Threads |
|---------|---------|---------|---------|
| TUIO-to-OSC_Bridge | Low | ~150 MB (PySide6) | 3 |
| psn_tuio_mapper_gui | Low | ~80–150 MB | 2–3 |
| emotiv-pixera-bridge | Very low | ~50 MB | 2 |
| Cascade_System-OSCbridge | Very low | ~50 MB | 2–3 |
| MPE-to-OSC | Very low | ~10 MB | 1–2 |
| pixera-pipeline-mapper | Very low | ~40 MB | 1 |
| **Total** | **Low** | **~500–600 MB** | **~14** |

No GPU required. No high-throughput data processing. The host box is I/O-bound (network + USB), not compute-bound.

---

### Minimum Compute Specification

| Component | Minimum | Notes |
|-----------|---------|-------|
| CPU | 4-core x86-64, 2.0 GHz | 6 idle Python processes + 1 C++ process; 4 cores is comfortable headroom |
| RAM | 8 GB | ~600 MB used; 8 GB gives ample OS + overhead |
| Storage | 32 GB SSD | OS + Python 3.12 env + project files; NVMe not required |
| GPU | None | Explicitly excluded from scope |
| Display | Optional | Only needed if Qt GUI apps are not headless |

A **NUC-class or SBC-class** x86-64 board is sufficient. An Intel N100 or similar low-power chip handles this workload with single-digit CPU percentage.

---

### Network Interface Requirements

| Requirement | Detail |
|------------|--------|
| Ethernet ports | **2 recommended** — one show LAN (TUIO sources, PSN server, MIDI, production gear), one management/upstream |
| Multicast | PSN requires IGMP multicast on the show LAN NIC and switch |
| Speed | 1GbE is more than sufficient — all protocols are tiny UDP datagrams |
| WiFi | Not required for bridge operation |

**Port inventory — all bridges combined:**

| Port | Proto | Dir | Service |
|------|-------|-----|---------|
| 3333 | UDP | IN | TUIO listen (TUIO-to-OSC_Bridge) |
| 56565 | UDP multicast | IN | PSN listen (psn_tuio_mapper_gui) |
| 6868 | WSS | OUT | Emotiv Cortex API |
| 7000 | UDP | OUT | OSC → Pixera (default) |
| 1401 / 9999 | TCP | OUT | Pixera JSON-RPC (pixera-pipeline-mapper) |
| custom | UDP | OUT | OSC → Notch, TouchDesigner, other targets |

No port conflicts. All inbound ports are on distinct numbers.

---

### USB Interface Requirements

| Device | Interface | Count |
|--------|-----------|-------|
| Emotiv USB receiver dongle | USB-A | 1 |
| Raspberry Pi Pico (Cascade System) | USB-A (micro-B or USB-C cable) | 1 |
| MIDI controller / interface | USB-A | 1 |
| USB hub (optional expansion) | USB-A | 1 |
| **Minimum USB-A ports on host** | | **3 (4 with hub port)** |

---

### OS and Platform

| Consideration | Recommendation |
|--------------|---------------|
| OS | Ubuntu 22.04 LTS or 24.04 LTS |
| Kernel | `linux-lowlatency` package (for MPE-to-OSC scheduling) |
| Python | 3.12, single shared venv per project or `uv` managed |
| Process management | `systemd` units for each bridge — auto-start, auto-restart, logging |
| Qt GUI bridges | Run under `Xvfb` virtual display, or refactor to headless backends |
| Emotiv Cortex | ⚠️ Windows/macOS only — may require Cortex on a separate Windows machine; bridge connects over network WebSocket |

---

### Real-Time / Latency Summary

| Bridge | Latency demand | Mechanism |
|--------|---------------|-----------|
| MPE-to-OSC | **High** (<5 ms) | C++ MIDI handler; `SCHED_FIFO` priority on Linux |
| TUIO-to-OSC_Bridge | Medium (<20 ms) | Thread + queue; adequate as-is |
| psn_tuio_mapper_gui | Medium (PSN ~50 Hz) | Multicast listener |
| emotiv-pixera-bridge | Low | WebSocket polling; biometric data is slow-changing |
| Cascade_System-OSCbridge | Medium | Dependent on Cascade requirements |
| pixera-pipeline-mapper | Low | Event-driven |

---

### Suggested Host Box Specification

| Component | Spec |
|-----------|------|
| Form factor | Mini-ITX or Intel NUC |
| CPU | Intel N100 / N305, or AMD Ryzen 5 5560U — fanless or near-silent |
| RAM | 8 GB DDR5 (16 GB if budget allows) |
| Storage | 64 GB M.2 NVMe SSD |
| GPU | Integrated only (no discrete GPU needed) |
| NIC | 2× 2.5GbE (Intel i226 or similar) |
| USB | 4× USB-A 3.0, 1× USB-C |
| Display | 1× HDMI or DisplayPort (for setup/debug; can be disconnected at runtime) |
| Audio | Not required |
| Power | 12–19 V DC brick; target <30 W TDP |
| OS | Ubuntu 24.04 LTS + linux-lowlatency kernel |

**Suitable off-the-shelf candidates:** Minisforum UN100, ASUS NUC 14 Essential, Topton N100 bare-board (for custom Flux.ai integration).

---

## Open Questions for Verification

1. **Emotiv Cortex platform** — Does the Cortex app run on Linux (limited support), or must it run on a separate Windows host with the bridge connecting remotely via WebSocket?
2. **psn_tuio_mapper_gui output** — Does it emit TUIO (chaining into TUIO-to-OSC_Bridge on port 3333) or direct OSC? This determines whether both processes must run simultaneously or if they are alternatives.
3. **MPE-to-OSC MIDI input** — USB class-compliant MIDI, or DIN-5 via adapter? Determines USB port type needed.
4. **TUIO Bridge headless** — Decision needed: adapt backend as a systemd service (preferred for a dedicated box), or run under Xvfb? The backend decoupling in the source makes a service refactor straightforward.
5. **Cascade System status** — Is `Cascade_System-OSCbridge` still an active deployment, or has it been superseded by newer projects?
6. **pixera-pipeline-mapper API version** — Pixera JSON-RPC port differs between Pixera versions (1401 vs 9999); confirm which version is targeted.

---

_End of survey. Update once private repo source files can be read directly._
