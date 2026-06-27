# Blackdown Bridge Box — Hardware Design Brief
**Prepared:** 2026-06-27  
**Tool:** Flux.ai  
**Type:** Custom PCB / carrier board for dedicated protocol bridge host

---

## Purpose

A compact standalone box that runs six concurrent protocol conversion bridges for live production. All connections are hot-swap — nothing is permanently tethered. The box provides the physical interfaces; software manages detection and reconnection.

---

## Protocol conversions running on this host

| Bridge | In | Out |
|--------|-----|-----|
| TUIO-to-OSC | TUIO 1.1 OSC bundle, UDP | Flat OSC, UDP |
| PSN-to-TUIO | PosiStageNet binary, UDP multicast | TUIO 1.1, UDP |
| Emotiv-to-Pixera | OSC from Cortex bridge, UDP | OSC re-addressed, UDP |
| Cascade OSC router | OSC, UDP + USB serial | OSC, UDP |
| MPE-to-OSC | MIDI, USB or DIN | OSC, UDP |
| Pixera pipeline mapper | Internal events | Pixera TCP |

No GPU, no display, no audio processing.

---

## Physical interface requirements

### Ethernet
- **2 × Gigabit Ethernet (RJ45)** — show LAN and management/upstream, independent
- Both ports must support **UDP multicast / IGMP** (required for PosiStageNet)

### MIDI
- **DIN-5 MIDI IN** — standard opto-isolated input circuit
- **DIN-5 MIDI OUT** — standard current-source output circuit
- **USB-A port for USB MIDI** — class-compliant device connection (same port pool as USB general)
- Both DIN and USB MIDI should be available simultaneously; the MPE bridge selects whichever is active

### USB
- **4 × USB-A** minimum — for USB MIDI, serial microcontroller nodes, and any other hot-swap peripherals
- All hot-swap; no device is permanently attached

### Power
- DC barrel input, 12 V or 19 V (to suit compute module choice)
- Target < 30 W total system draw

### No display output required
- Configuration and monitoring via **web UI or custom controller application** over the network
- No HDMI, DisplayPort, or local panel needed on the PCB

---

## Compute module

Custom carrier board approach — the PCB hosts a compute module rather than discrete components:

- **Raspberry Pi CM5** is the natural choice: provides dual Ethernet, USB, UART (for DIN MIDI), and is well-suited to a custom carrier
- Alternatively: Intel N100 SODIMM-style module if x86-64 is preferred for software compatibility
- The carrier PCB provides all external connectors, power regulation, and the DIN MIDI circuit; the module provides compute and OS

---

## DIN MIDI circuit notes

Standard MIDI IN: DIN-5 socket → 220 Ω series resistor → 6N138 optocoupler → UART RX  
Standard MIDI OUT: UART TX → 220 Ω + 220 Ω resistors → DIN-5 socket pin 4/5  
Alternatively: onboard USB MIDI bridge chip (e.g. CH345G) converting DIN ↔ USB, presenting as a single USB MIDI device to the compute module — simplifies firmware, no bare UART handling needed.

---

## Summary of connectors on PCB

| Connector | Count | Notes |
|-----------|-------|-------|
| RJ45 Gigabit Ethernet | 2 | Independent MACs/PHYs |
| DIN-5 MIDI IN | 1 | Opto-isolated |
| DIN-5 MIDI OUT | 1 | Current-source driver |
| USB-A 3.0 | 4 | Hot-swap, shared pool |
| DC barrel power | 1 | 12–19 V input |
| Compute module socket | 1 | CM5 or equivalent |

---

## Open questions for design session

1. **CM5 vs x86 module** — CM5 gives a cleaner carrier design and has the UART needed for DIN MIDI natively; x86 is better if Windows compatibility for any bridge is ever needed.
2. **TRS MIDI** — worth adding 3.5 mm TRS MIDI IN/OUT alongside DIN-5? Increasingly common on modern instruments.
3. **USB MIDI bridge chip vs bare UART** — CH345G or similar simplifies the MIDI circuit and removes UART resource from the compute module; worth the extra component?
4. **Enclosure form factor** — 1U rack, desktop brick, or DIN rail mount?
5. **Status indicators** — LEDs per Ethernet port and per bridge process state (active/error) on the front panel?
