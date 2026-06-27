# Bridge Box — Hardware Design Brief
**Prepared:** 2026-06-27
**Flux.ai scope:** Interface HAT (expansion card)

---

## Concept

A low-budget utility box for protocol bridging and timecode generation in live production environments. Primarily useful for prototyping system setups, rehearsals, and projects where a full professional middleware solution is unnecessary or unbudgeted. Not intended to replace production-grade equipment — intended to reduce the need to bodge these tasks onto a laptop or the main media server.

**Target price:** under £150 complete
**Target user:** Technical directors, show programmers, system integrators working in live performance, installation, and events

---

## Current validated use case

Naostage (performer/object tracking system) sends PSN (PosiStageNet) data over the show LAN. A Notch block on the media server receives TUIO. The bridge between them is currently an app running on the media server itself — consuming resources and adding complexity to a machine that should only be running Notch.

The box removes that bridge from the server and puts it in dedicated, isolated hardware.

```
Naostage  →  PSN (UDP multicast)  →  Bridge Box  →  TUIO (UDP)  →  Notch block
```

---

## What the box does

### Protocol bridges (software, runs on Pi 5)
| Bridge | In | Out |
|--------|-----|-----|
| PSN → TUIO | PosiStageNet binary, UDP multicast | TUIO 1.1, UDP |
| TUIO → OSC | TUIO 1.1 OSC bundle, UDP | Flat OSC, UDP — up to 8 targets |
| OSC router | OSC, UDP | OSC, UDP (filtered / re-addressed) |
| MPE → OSC | MIDI MPE, USB or DIN | OSC, UDP |
| Timecode generator | — | LTC audio + MTC MIDI |

### Timecode generation
- Generates SMPTE timecode at selectable frame rates: 24, 25, 29.97, 30 fps
- **LTC** output via 3.5mm TRS audio jack (analogue audio signal)
- **MTC** output via MIDI (DIN and/or USB)
- Sufficient for rehearsals, system testing, and Notch/Pixera sync testing — not intended as a broadcast master

### Configuration
- Web UI accessible at `bridgebox.local` on any show LAN — no app install, no account, works from a phone or tablet
- Boots and starts bridging automatically — no keyboard or screen needed in operation
- Preconfigured presets for common show topologies (e.g. "PSN to Notch", "Touch table to Pixera")

---

## Hardware architecture — three components

### 1. Compute — Raspberry Pi 5 (off-the-shelf)
- Handles all software, networking, USB
- Headless Linux, boots from SD card — full software stack is a swappable image
- Single Ethernet port (sufficient for prototype; show LAN and management share the interface)
- Replaceable as faster Pi hardware becomes available

### 2. Interface card — custom HAT (Flux.ai design)
A Pi-compatible HAT that adds the production-specific hardware the Pi 5 doesn't provide natively. This is the custom PCB design.

**Connectors on the HAT:**
| Connector | Purpose |
|-----------|---------|
| DIN-5 MIDI IN | Opto-isolated MIDI input (6N138 or equivalent) |
| DIN-5 MIDI OUT | Current-source MIDI output |
| 3.5mm TRS audio out | LTC timecode output |
| Status LEDs | Per bridge and per connection state |
| 40-pin GPIO header (female) | Connects to Pi 5 |

**Signals used from Pi GPIO:**
| Signal | Use |
|--------|-----|
| UART TX / RX | DIN MIDI IN and OUT |
| I2S (BCK, LRCK, DOUT) | Audio DAC for LTC |
| GPIO (×4 minimum) | Status LEDs |

**Key ICs on HAT:**
| Component | Function |
|-----------|---------|
| 6N138 optocoupler | MIDI IN isolation |
| PCM5102A (or similar I2S DAC) | LTC audio output |
| Resistors / protection diodes | MIDI OUT driver, protection |

The HAT is upgradable — a future revision could add more interfaces (second audio out, additional MIDI ports, GPIO expansion) without changing the Pi or software.

### 3. Enclosure — two variants

**Variant A: 3D printed**
- Open design, freely shared
- Suitable for prototyping and personal builds
- Exposes all connectors on rear panel
- Pi 5 + HAT stack fits inside

**Variant B: 1U half-rack**
- Same electronics, professional enclosure
- Fits on a tech shelf or in a compact touring rack
- Front panel: status LEDs, power indicator
- Rear panel: MIDI IN/OUT, LTC audio out, USB-A ports, Ethernet, DC power

---

## Physical interface summary (complete box)

| Interface | Connector | Count | Notes |
|-----------|-----------|-------|-------|
| Ethernet | RJ45 | 1 | Show LAN — IGMP multicast for PSN |
| MIDI IN | DIN-5 | 1 | Opto-isolated |
| MIDI OUT | DIN-5 | 1 | LTC MTC + MPE bridge output |
| LTC audio | 3.5mm TRS | 1 | SMPTE timecode audio |
| USB-A | USB-A 3.0 | 2–4 | USB MIDI, USB serial peripherals, hot-swap |
| DC power | Barrel jack | 1 | 5V via USB-C (Pi 5 standard) or external 5V |

---

## Flux.ai design scope

**Design the HAT only.** The Pi 5 is off-the-shelf; the HAT is the custom PCB.

Constraints:
- Must conform to Raspberry Pi HAT specification (65 × 56 mm, 40-pin GPIO header placement)
- UART pins (GPIO 14/15) used for MIDI — must not conflict with other HAT functions
- I2S pins (GPIO 18/19/21) used for audio DAC
- HAT EEPROM (I2C, GPIO 0/1) optional but good practice

---

## Open questions before routing

1. **UART vs USB MIDI bridge chip** — use Pi's UART directly for DIN MIDI, or put a CH345G on the HAT so MIDI appears as a USB device? UART is simpler; USB bridge is more software-friendly.
2. **TRS MIDI** — add 3.5mm TRS MIDI IN/OUT alongside DIN-5? Increasingly common on modern instruments and controllers.
3. **Second audio output** — one LTC channel is enough for the prototype; a stereo DAC costs the same as mono and leaves room for a second use later.
4. **HAT EEPROM** — include it? Allows the Pi to auto-detect and configure the HAT on boot.
5. **LED driver IC or direct GPIO** — four status LEDs can drive direct from GPIO with resistors; more LEDs need a driver IC.
