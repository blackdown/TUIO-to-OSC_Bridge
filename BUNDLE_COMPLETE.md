# Complete Protocol Bridges Bundle ✓

**Created**: 2026-06-27

This repository now contains a **complete bundle** of all 4 protocol bridge applications:

1. ✅ **TUIO-to-OSC_Bridge** - TUIO to OSC converter (PySide6)
2. ✅ **PSN → TUIO Mapper** - Kratos PSN to TUIO (customtkinter)
3. ✅ **MPE-to-OSC** - MIDI Polyphonic Expression to OSC (JUCE/C++)
4. ✅ **Emotiv → Pixera Bridge** - EEG to Pixera OSC (customtkinter)

## Structure

All projects are organized in the `protocol-bridges/` directory for easy distribution as a single bundle.

```
protocol-bridges/
├── TUIO-to-OSC_Bridge/     ← Main entry point (this repo)
├── psn_tuio_mapper_gui/    ← Secondary GUI app
├── MPE-to-OSC/             ← JUCE plugin source
├── emotiv-pixera-bridge/   ← EEG metrics bridge
└── README.md               ← Bundle documentation
```

## Next Steps

1. **Create a Release** with `protocol-bridges/` as a downloadable zip
2. **Tag as v1.0.0-bundle** to indicate complete feature set
3. **Update all individual repos** to reference this bundle

Each project retains its own independent repo for:
- Individual development workflows
- Separate issue tracking
- Independent versioning when needed

But they are now **unified under one conceptual bundle** for end-users who want all bridges together.
