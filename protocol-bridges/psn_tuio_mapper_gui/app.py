# PSN → TUIO Mapper GUI
# Naostage Kratos PSN tracker → TUIO 1.1 2Dcur bridge

import time
import tkinter as tk
import customtkinter as ctk
from bridge import PSNTUIOBridge
import config as cfg

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FIELD_DEFS = [
    ("PSN INPUT", [
        ("local_interface_ip", "Local Interface IP"),
        ("kratos_psn_port", "PSN Port"),
    ]),
    ("TUIO OUTPUT", [
        ("notch_ip", "Notch IP"),
        ("notch_port", "Notch Port"),
    ]),
    ("STAGE CALIBRATION", [
        ("stage_origin_x_m", "Origin X (m)"),
        ("stage_origin_y_m", "Origin Y (m)"),
        ("stage_width_m", "Width (m)"),
        ("stage_height_m", "Height (m)"),
    ]),
    ("TIMING", [
        ("send_rate_hz", "Send Rate (Hz)"),
        ("point_timeout_s", "Timeout (s)"),
    ]),
]

FIELD_TYPES = {
    "local_interface_ip": str,
    "kratos_psn_port": int,
    "notch_ip": str,
    "notch_port": int,
    "stage_origin_x_m": float,
    "stage_origin_y_m": float,
    "stage_width_m": float,
    "stage_height_m": float,
    "send_rate_hz": int,
    "point_timeout_s": float,
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PSN → TUIO Mapper")
        self.geometry("760x520")
        self.minsize(620, 430)

        self._bridge: PSNTUIOBridge | None = None
        self._config = cfg.load()
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._prev_packets = 0
        self._packet_history: list[int] = []

        self._build_left_panel()
        self._build_right_panel()

    # ------------------------------------------------------------------ #
    # Build                                                                #
    # ------------------------------------------------------------------ #

    def _build_left_panel(self) -> None:
        left = ctk.CTkFrame(self, width=240, corner_radius=0)
        left.pack(side="left", fill="y", padx=(10, 5), pady=10)
        left.pack_propagate(False)

        for section, fields in FIELD_DEFS:
            ctk.CTkLabel(
                left,
                text=section,
                font=ctk.CTkFont(size=9),
                text_color=("#1a5ece", "#4a9eff"),
            ).pack(anchor="w", padx=12, pady=(10, 1))

            for key, label in fields:
                ctk.CTkLabel(
                    left,
                    text=label,
                    font=ctk.CTkFont(size=10),
                    text_color="gray60",
                ).pack(anchor="w", padx=12, pady=0)
                entry = ctk.CTkEntry(left, height=28, font=ctk.CTkFont(size=11))
                entry.insert(0, str(self._config.get(key, "")))
                entry.pack(fill="x", padx=12, pady=(1, 3))
                self._entries[key] = entry

        self._start_btn = ctk.CTkButton(
            left,
            text="▶  START",
            command=self._on_start,
            fg_color="#0d7a3a",
            hover_color="#0a5e2c",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
        )
        self._start_btn.pack(fill="x", padx=12, pady=(14, 12), side="bottom")

    def _build_right_panel(self) -> None:
        right = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)

        self._status_label = ctk.CTkLabel(
            right,
            text="● STOPPED",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray50",
        )
        self._status_label.pack(anchor="w", padx=8, pady=(6, 4))

        canvas_frame = ctk.CTkFrame(right, fg_color="#0a0a15", corner_radius=6)
        canvas_frame.pack(fill="both", expand=True, padx=0, pady=(0, 6))
        self._canvas = tk.Canvas(canvas_frame, bg="#0a0a15", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True, padx=2, pady=2)

        self._log = tk.Text(
            right,
            height=8,
            bg="#0d0d1a",
            fg="#aaaaaa",
            font=("Courier", 10),
            state="disabled",
            relief="flat",
            padx=8,
            pady=6,
            insertbackground="#aaaaaa",
            selectbackground="#1a3460",
            wrap="none",
        )
        self._log.tag_config("error", foreground="#ff6b6b")
        self._log.pack(fill="x")

    # ------------------------------------------------------------------ #
    # Start / Stop                                                         #
    # ------------------------------------------------------------------ #

    def _on_start(self) -> None:
        raw = {key: entry.get() for key, entry in self._entries.items()}
        errors = cfg.validate(raw)

        for entry in self._entries.values():
            entry.configure(border_color=("gray70", "gray30"))
        if errors:
            for key in errors:
                self._entries[key].configure(border_color="red")
            return

        config = {key: FIELD_TYPES[key](raw[key]) for key in raw}
        cfg.save(config)

        self._bridge = PSNTUIOBridge(config)
        self._bridge.start()
        self._lock_fields(True)
        self._start_btn.configure(
            text="■  STOP",
            command=self._on_stop,
            fg_color="#8B0000",
            hover_color="#6b0000",
        )
        self._prev_packets = 0
        self._packet_history = []
        self._poll()

    def _on_stop(self) -> None:
        if self._bridge:
            self._bridge.stop()
            state = self._bridge.get_state()
            self._append_log(state["log_lines"])
            self._bridge = None
        self._lock_fields(False)
        self._start_btn.configure(
            text="▶  START",
            command=self._on_start,
            fg_color="#0d7a3a",
            hover_color="#0a5e2c",
        )
        self._canvas.delete("all")
        self._status_label.configure(text="● STOPPED", text_color="gray50")

    def _lock_fields(self, lock: bool) -> None:
        state = "disabled" if lock else "normal"
        for entry in self._entries.values():
            entry.configure(state=state)

    # ------------------------------------------------------------------ #
    # Poll loop                                                            #
    # ------------------------------------------------------------------ #

    def _poll(self) -> None:
        if not self._bridge:
            return
        try:
            state = self._bridge.get_state()
        except Exception as exc:
            import time
            self._append_log([f"{time.strftime('%H:%M:%S')}  Internal error: {exc}"])
            self._on_stop()
            return
        self._update_canvas(state["trackers"])
        self._update_status(state)
        self._append_log(state["log_lines"])
        self.after(100, self._poll)

    def _update_canvas(self, trackers: dict) -> None:
        self._canvas.delete("all")
        w = self._canvas.winfo_width() or 400
        h = self._canvas.winfo_height() or 300
        self._canvas.create_text(
            6, 4, anchor="nw", text="STAGE VIEW", fill="#222222", font=("", 7)
        )
        r = 6
        for tid, pos in trackers.items():
            cx = pos["x"] * w
            cy = pos["y"] * h
            self._canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#00ff88", outline="")
            self._canvas.create_text(cx, cy + r + 7, text=str(tid), fill="#00ff88", font=("", 8))

    def _update_status(self, state: dict) -> None:
        count = len(state["trackers"])
        delta = state["tuio_packets_sent"] - self._prev_packets
        self._prev_packets = state["tuio_packets_sent"]
        self._packet_history.append(delta)
        if len(self._packet_history) > 10:
            self._packet_history.pop(0)
        pps = sum(self._packet_history)
        errors = state["tuio_errors"]
        noun = "tracker" if count == 1 else "trackers"
        text = f"● RUNNING  |  {count} {noun}  |  {pps} pkt/s"
        color = "#00ff88"
        if errors:
            text += f"  |  ⚠ {errors} err"
            color = "#ffaa00"
        self._status_label.configure(text=text, text_color=color)

    def _append_log(self, lines: list) -> None:
        if not lines:
            return
        self._log.configure(state="normal")
        for line in lines:
            tag = "error" if "error" in line.lower() else ""
            self._log.insert("end", line + "\n", tag)
        self._log.see("end")
        self._log.configure(state="disabled")


if __name__ == "__main__":
    App().mainloop()
