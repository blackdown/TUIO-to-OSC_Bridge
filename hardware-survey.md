# Blackdown Bridge Projects — Hardware Survey
**Prepared:** 2026-06-27  
**Scope:** Protocol conversion bridges only (ML/vision projects excluded)  
**Purpose:** Feed into Flux.ai PCB/hardware design for a dedicated compact host box  
**Account:** github.com/blackdown (Antony Bailey, Blackdown Solutions)

> **Note on data quality:** GitHub file access for this session is scoped to `TUIO-to-OSC_Bridge`. That project has full source-level analysis. All other projects are documented from repository metadata plus naming inference — sections marked ⚠️ need verification. Application-layer port numbers and API details are deliberately excluded: those are software configuration, not hardware requirements.

---

## Protocol Conversion Map

All bridges in this set share the same pattern: they receive data on one transport/wire format and emit it as flat OSC over UDP to downstream targets. The conversion is always at the **encoding and addressing layer**, not the physical transport layer — everything moves over standard Ethernet UDP except MIDI, which arrives over USB.

```
PSN (binary, UDP multicast) ───────► TUIO 1.1 (OSC bundle, UDP)
                                               │
TUIO 1.1 (OSC bundle, UDP) ────────────────────┤
                                               ▼
                                      Flat OSC / UDP ──► Pixera
MIDI MPE (USB serial) ─────────────────────────┤         Notch
                                               │         TouchDesigner
OSC from Cortex bridge (UDP) ──────────────────┤         (any OSC target)
                                               │
OSC (Cascade sources) ─────────────────────────┘

pixera-pipeline-mapper: internal state ──────────────────► Pixera TCP
```

**Every source ends up as OSC over UDP or Pixera over TCP.** The host box needs to speak:
- UDP (unicast and multicast) on its Ethernet interface
- USB serial (for Pi Pico hardware node)
- USB MIDI (for MPE controller)

---

## Conversion Profiles

---

### 1. TUIO-to-OSC_Bridge
_Full source confirmed_

**Conversion:** TUIO 1.1 OSC bundle → flat individual OSC messages

TUIO wraps multiple touch/object attributes into a single multi-argument OSC bundle per frame. Most media servers (including Pixera's DirectNetworkOSC input) cannot parse these bundles natively. This bridge unpacks each bundle and re-emits every attribute as its own discrete OSC message.

| Side | Physical interface | Transport | Format |
|------|-------------------|-----------|--------|
| In | Ethernet | UDP unicast | TUIO 1.1 OSC bundle (all 9 profiles: 2D/2.5D/3D × cursor/object/blob) |
| Out | Ethernet | UDP unicast | Flat OSC — one message per attribute per object |

**Direction:** server (listen) + client (emit)  
**State:** Working and released. Active development.  
**Concurrency:** 3 threads (receiver, engine, Qt GUI). Lightweight queue-based handoff.  
**Headless:** Currently a Qt desktop GUI. Backend is cleanly separated; serviceable as a headless process.

---

### 2. psn_tuio_mapper_gui
⚠️ _Inferred_

**Conversion:** PSN binary → TUIO 1.1 OSC bundle

PosiStageNet (PSN) is a proprietary binary protocol used by stage automation and tracking systems (follow-spot, performer tracking). It is sent as UDP multicast on the show LAN. This bridge decodes PSN tracker frames and re-encodes them as TUIO 1.1 so that TUIO-aware applications — including the TUIO-to-OSC_Bridge above — can consume them.

**Chain in practice:** PSN → this bridge → TUIO-to-OSC_Bridge → flat OSC → Pixera/Notch

| Side | Physical interface | Transport | Format |
|------|-------------------|-----------|--------|
| In | Ethernet | **UDP multicast** | PSN binary (tracker position frames) |
| Out | Ethernet | UDP unicast | TUIO 1.1 OSC bundle |

**Direction:** multicast listener + TUIO emitter  
**Multicast requirement:** NIC must support IGMP; switch on the show LAN must support IGMP snooping.  
**State:** Most recently updated bridge (June 2026). Active.

---

### 3. emotiv-pixera-bridge
⚠️ _Inferred — Cortex provides its own OSC output_

**Conversion:** OSC (Cortex output) → flat OSC (Pixera-addressed)

The Emotiv Cortex system has its own built-in OSC bridge that publishes EEG/biometric data (mental commands, facial expressions, performance metrics) as OSC. This bridge receives that OSC stream and re-addresses or re-formats the messages to match Pixera's expected OSC input schema — address remapping and value scaling, not protocol translation.

| Side | Physical interface | Transport | Format |
|------|-------------------|-----------|--------|
| In | Ethernet | UDP unicast | OSC (Cortex bridge output) |
| Out | Ethernet | UDP unicast | Flat OSC (Pixera-addressed) |

**Direction:** OSC listener + OSC emitter  
**Hardware on host:** None — EEG headset and Cortex software run elsewhere on the network.  
**State:** Most recently pushed of all bridges (April 2026). Active.

---

### 4. Cascade_System-OSCbridge
⚠️ _Inferred_

**Conversion:** OSC → OSC (router/filter)

Part of the "Cascade System" — a bespoke production control system. Aggregates OSC streams from multiple internal sources (including the Cascade Pi Pico hardware node over USB serial) and routes/filters them to downstream targets. The conversion is address-space routing, not format translation.

| Side | Physical interface | Transport | Format |
|------|-------------------|-----------|--------|
| In | Ethernet + **USB serial** | UDP unicast + serial | OSC (network) + raw serial (from Pi Pico) |
| Out | Ethernet | UDP unicast | OSC |

**Hardware on host:** USB connection to Raspberry Pi Pico (the `Cascade_System-PiPico` firmware node). The Pico reads physical hardware (GPIO, ADC, I2C) and sends events to the bridge over USB serial.  
**State:** Last updated October 2025. Status uncertain — may be active or superseded.

---

### 5. MPE-to-OSC
⚠️ _Inferred_

**Conversion:** MIDI MPE (USB) → flat OSC (UDP)

MIDI Polyphonic Expression (MPE) is the per-note expressive extension to MIDI, used by controllers like Roli Seaboard, Linnstrument, and Expressive E Osmose. Standard MIDI handling treats all notes on a channel uniformly; MPE assigns each note its own channel for independent pitch bend, pressure, and slide. This bridge decodes the MPE channel layout and emits each per-note attribute as a discrete OSC message.

| Side | Physical interface | Transport | Format |
|------|-------------------|-----------|--------|
| In | **USB** | USB MIDI (class-compliant) | MIDI 1.0 with MPE channel layout |
| Out | Ethernet | UDP unicast | Flat OSC (per-note attribute messages) |

**Direction:** USB MIDI consumer + OSC emitter  
**Language:** C++ — native binary, no runtime interpreter.  
**Hardware on host:** One USB port for MIDI controller or USB-MIDI adapter.  
**Latency:** Highest real-time demand of all bridges. Musical performance requires <5 ms end-to-end. C++ handler is fast; OS scheduling is the constraint — low-latency kernel required (see OS section).  
**State:** Last updated November 2025.

---

### 6. pixera-pipeline-mapper
⚠️ _Inferred_

**Conversion:** Internal state / events → Pixera TCP control API

Not a streaming bridge — manages Pixera's internal configuration: layer routing, content assignment, preset recall. Event-driven, not continuous. Included here because it is a host-resident process with a persistent network connection to Pixera.

| Side | Physical interface | Transport | Format |
|------|-------------------|-----------|--------|
| In | — | Internal / scripted events | — |
| Out | Ethernet | **TCP** | Pixera control API |

**Direction:** Client only (outbound to Pixera)  
**Resource profile:** Negligible — idle except during state changes.

---

## Hardware Requirements

### Physical Interfaces Required on Host Box

| Interface | Required for | Minimum count |
|-----------|-------------|---------------|
| Ethernet | All bridges — UDP + TCP | **2 ports** (show LAN + management) |
| USB-A | Pi Pico (Cascade), MIDI controller | **2 ports minimum** |
| USB-A | Optional hub for expansion | +1 recommended |

**No GPIO, no audio, no display output required for bridge operation.** Display useful only for setup and debug.

### Network Capabilities

| Requirement | Needed by |
|------------|-----------|
| UDP unicast | All bridges |
| **UDP multicast (IGMP)** | psn_tuio_mapper_gui — NIC and switch must support IGMP snooping |
| TCP | pixera-pipeline-mapper |
| 1 GbE sufficient | No bridge generates significant bandwidth |

### Compute

No GPU. No high-throughput processing. The workload is entirely I/O-bound — small UDP datagrams at moderate rates, one USB MIDI stream, one USB serial stream.

| Component | Requirement |
|-----------|------------|
| CPU | 4-core x86-64, any modern low-power chip (Intel N100 or equivalent) |
| RAM | 8 GB — all 6 processes combined use ~500–600 MB |
| Storage | 32 GB SSD — OS + Python env + project files |
| GPU | None |

### OS

| Item | Requirement |
|------|------------|
| OS | Linux (Ubuntu 24.04 LTS recommended) |
| Kernel | **Low-latency kernel required** for MPE-to-OSC (`linux-lowlatency` or `PREEMPT_RT`) |
| Process management | `systemd` units — one per bridge, auto-start, auto-restart |
| Qt GUI bridges | Adapt to headless service, or run under virtual framebuffer (`Xvfb`) |

### Suggested Form Factor

NUC or Mini-ITX. Fanless or near-silent preferred (live performance environment).

| Component | Spec |
|-----------|------|
| Board | Intel N100 NUC, or Mini-ITX with low-power CPU |
| RAM | 8–16 GB DDR5 |
| Storage | 64 GB M.2 NVMe |
| NIC | 2× Ethernet (IGMP-capable) |
| USB | 4× USB-A (2 occupied: Pico + MIDI; 2 spare) |
| Power | 12–19 V DC brick, <30 W TDP |

---

## Open Questions

1. **psn_tuio_mapper_gui** — Does it emit TUIO (chaining into TUIO-to-OSC_Bridge) or direct OSC? This determines whether both must run simultaneously or if they are alternatives.
2. **MPE-to-OSC** — USB class-compliant MIDI controller direct, or DIN-5 via USB adapter? Determines USB port type needed.
3. **Cascade System** — Still active in current deployment? Pi Pico USB serial confirmed needed on host?
4. **TUIO Bridge headless** — Confirm approach: headless service refactor vs virtual display.
5. **emotiv-pixera-bridge** — Confirm OSC-in assumption. What address namespace does Cortex bridge output on?

---

_End of survey. Update once private repo source files can be read directly._
