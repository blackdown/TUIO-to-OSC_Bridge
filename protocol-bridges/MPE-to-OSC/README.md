# MPE-to-OSC

A JUCE audio plugin that converts MIDI Polyphonic Expression (MPE) messages into OSC (Open Sound Control) messages for creative applications.

## What is this?

MPE-to-OSC bridges the gap between expressive MIDI controllers and creative software that uses OSC. It translates the nuanced, per-note expression data from MPE controllers into OSC messages that can control visuals, synthesizers, or any OSC-enabled application.

Perfect for:
- Connecting MPE controllers (like Roli Seaboard, Expressive E Osmose, Haken Continuum) to visual software
- Integrating expressive playing into live performances with TouchDesigner, Max/MSP, or other OSC-capable software
- Creating interactive audio-visual installations

## Features

- **Full MPE Support**: Up to 15 voices with per-note pressure, pitch bend, and timbre (slide)
- **Dual MPE Modes**:
  - **Standard MPE**: Compatible with most MPE controllers (uses channel pressure, pitch bend, CC74)
  - **Osmose MPE+**: High-resolution 14-bit mode for Expressive E Osmose (USB2 connection)
- **Real-time OSC Output**: Sends continuous per-voice expression data
- **Flexible Configuration**:
  - Set custom OSC host and port
  - Customize OSC address prefix
  - Enable/disable logging for debugging
- **Modern UI**: Clean, Ableton Live-inspired interface with visual feedback for MIDI and OSC activity
- **Debug Tools**: Built-in Melatonin Inspector for UI development (debug builds only)

## Installation

1. Download the latest release for your platform
2. Copy the plugin to your DAW's plugin folder:
   - **macOS VST3**: `~/Library/Audio/Plug-Ins/VST3/`
   - **Windows VST3**: `C:\Program Files\Common Files\VST3\`
3. Launch your DAW and load the plugin on a MIDI track
4. Configure your MPE controller's settings in your DAW

## Usage

### Basic Setup

1. **Load the plugin** in your DAW on a MIDI track
2. **Configure OSC** in the Connection tab:
   - Set the target host (default: 127.0.0.1)
   - Set the target port (default: 8000)
   - Optionally customize the OSC prefix (default: /notch/)
3. **Select MPE mode** based on your controller
4. **Play your MPE controller** and watch the voice activity indicators
