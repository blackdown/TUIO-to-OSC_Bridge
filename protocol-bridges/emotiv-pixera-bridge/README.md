# Emotiv → Pixera Bridge

Bridges Emotiv Cortex EEG/metrics data to Pixera Control via OSC, with a simultaneous WebSocket rebroadcast for TouchDesigner/Notch clients.

## Requirements

- Python 3.10+
- Emotiv Launcher running with a paired EPOC X headset
- Pixera Control with an OSC input module configured

## Setup

```bash
git clone --recurse-submodules <this-repo-url>
cd emotiv-pixera-bridge
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Usage

1. Enter your Emotiv Client ID and Client Secret
2. Set Pixera IP and OSC port to match your Pixera Control OSC input module
3. Click **Connect** — the bridge authenticates with Cortex and starts the rebroadcast server
4. Click **Start OSC** to begin sending data to Pixera
5. Use **Open Monitor** for a full stream readout, **Open Log** for a detailed log window

## OSC Addresses (Pixera Control)

| Address | Range | Description |
|---|---|---|
| `/cortex/met/eng` | 0–1 | Engagement |
| `/cortex/met/exc` | 0–1 | Excitement (short-term) |
| `/cortex/met/lex` | 0–1 | Excitement (long-term) |
| `/cortex/met/str` | 0–1 | Stress |
| `/cortex/met/rel` | 0–1 | Relaxation |
| `/cortex/met/int` | 0–1 | Interest |
| `/cortex/met/attention` | 0–1 | Attention |
| `/cortex/dev/battery` | 0–100 | Battery % |
| `/cortex/dev/signal` | 0–1 | Signal quality |
| `/cortex/dev/contact/<CH>` | 0–4 | Per-channel contact quality |
| `/cortex/pow/<CH>/<band>` | µV² | Band power (theta/alpha/betaL/betaH/gamma) |
