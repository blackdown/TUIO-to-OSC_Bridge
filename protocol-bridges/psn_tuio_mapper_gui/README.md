# PSN → TUIO Mapper

A GUI tool that receives Naostage Kratos PSN (PosiStageNet) tracker data over UDP multicast and re-broadcasts it as TUIO 1.1 `2Dcur` bundles to Notch.

## Usage

**Pre-built:** download `PSN-TUIO-Mapper.exe` from releases and run it directly — no Python required.

**From source:**
```
pip install customtkinter pypsn python-osc
python app.py
```

## Configuration

| Field | Description |
|---|---|
| Local Interface IP | Network interface to listen on (`0.0.0.0` = all) |
| PSN Port | Kratos PSN UDP port (default `56565`) |
| Notch IP | IP of the machine running Notch |
| Notch Port | Port on Notch's TUIO Array node (default `3333`) |
| Origin X/Y (m) | Stage origin in Kratos world coordinates |
| Width/Height (m) | Stage dimensions — used to normalise tracker positions |
| Send Rate (Hz) | How many TUIO bundles to send per second |
| Timeout (s) | How long a tracker can go silent before being dropped |

Settings are saved automatically when you press **START**.
