# Blackdown Bridge Projects — Hardware Brief
**Prepared:** 2026-06-27  
**Purpose:** Flux.ai host box hardware specification  
**Scope:** Protocol conversion bridges (ML/vision projects excluded)

---

## What the box does

A single compact host running six simultaneous bridge processes that translate specialised source protocols into OSC or Pixera control data. All traffic is Ethernet UDP or TCP except two physical connections — a USB MIDI instrument and a USB serial microcontroller node. The host does no rendering, no ML inference, and no media playback.

---

## Protocol conversions

| Bridge | In | Out |
|--------|-----|-----|
| TUIO-to-OSC | TUIO 1.1 (OSC bundle, UDP) | Flat OSC, UDP — up to 8 targets |
| PSN-to-TUIO | PosiStageNet binary, UDP multicast | TUIO 1.1, UDP |
| Emotiv-to-Pixera | OSC from Cortex bridge, UDP | OSC re-addressed for Pixera, UDP |
| Cascade OSC router | OSC, UDP + USB serial from microcontroller | OSC, UDP |
| MPE-to-OSC | MIDI Polyphonic Expression, USB | OSC, UDP |
| Pixera pipeline mapper | Internal events | Pixera TCP control API |

All six processes run concurrently. Combined load is light — the host is I/O-bound, not compute-bound.

---

## Physical interfaces required

### Ethernet
- **2 × Ethernet ports** — one show LAN (TUIO sources, PSN multicast, production gear), one management
- Must support **UDP multicast / IGMP** for PSN (PosiStageNet)
- 1 GbE sufficient — all protocols are small UDP datagrams

### USB
- **USB serial × 1** — Raspberry Pi Pico microcontroller (Cascade system hardware node)
- **USB MIDI × 1** — MPE controller (expressive MIDI instrument)
- **USB serial output × 1** — TUIO bridge serial output to downstream devices (Pi Pico or similar)
- **1–2 spare USB ports** for expansion
- Minimum **4 × USB-A 3.0** on the host

### No other physical interfaces required
Audio, GPIO, display output, and camera inputs are not needed on this box.

---

## Compute

| Resource | Requirement |
|---------|------------|
| CPU | 4-core x86-64, any modern low-power chip |
| RAM | 8 GB |
| Storage | 64 GB SSD |
| GPU | None |
| Display | Not required at runtime — one video output useful for setup |

---

## Real-time requirements

The MPE-to-OSC bridge is the only timing-critical process — musical performance demands sub-5 ms MIDI-to-OSC latency. This requires a **low-latency OS kernel**. All other bridges are tolerant of normal scheduling.

---

## OS

Linux, low-latency kernel. Six bridge processes managed as system services — auto-start, auto-restart on failure. No desktop environment required at runtime.

---

## Suggested form factor

Mini-ITX or NUC class. Fanless or near-silent — intended for live performance environments.

| Component | Target spec |
|-----------|------------|
| Board | Mini-ITX, Intel N100 or equivalent low-power x86-64 |
| RAM | 8–16 GB |
| Storage | 64 GB M.2 NVMe |
| NIC | 2 × 2.5 GbE, IGMP-capable |
| USB | 4 × USB-A 3.0 minimum |
| Power | 12–19 V DC, target < 30 W |

---

## Open questions before finalising spec

1. Does the MPE controller connect USB direct to this box, or is it on another machine?
2. Is the Cascade Pi Pico permanently tethered to this box, or hot-swapped?
3. Is a second Ethernet port essential, or is a managed switch on a single port acceptable?
4. Should the box expose a web UI for bridge config (removing any display requirement entirely)?
