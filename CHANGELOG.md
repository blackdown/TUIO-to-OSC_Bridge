# Changelog

## v1.0.0 — 2026-04-12

Initial public release.

### Features

- **TUIO 1.1 receiver** — all nine profiles: 2D/2.5D/3D × cursor/object/blob
- **Live monitor** — scrolling table showing active session IDs, type, position, velocity, acceleration, angle, class ID and lifetime
- **OSC log panel** — real-time scrolling view of outgoing OSC messages with address filter and pause button
- **Dynamic output targets** — add up to 8 independent OSC destinations, each with its own IP, port, enable toggle and transform settings
- **Per-target transforms** — Flip X, Flip Y, Swap X↔Y, Scale X/Y, Offset X/Y applied independently per target
- **Velocity derivation** — when a TUIO simulator sends zero velocity the bridge computes it automatically from position deltas
- **Config persistence** — settings saved to `tuio_bridge_config.json`; Save/Load buttons with visual confirmation feedback
- **Material Dark UI** — PySide6/QML interface with three resizable panels (config · monitor · log)
- **Standalone Windows exe** — built with PyInstaller, no Python required to run
