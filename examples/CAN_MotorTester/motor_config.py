"""Independent external motor configuration forms and asynchronous sender."""

import queue
import tkinter as tk
from tkinter import ttk

from sbgc32 import ConfirmationStatus, ExternalMotorsControlConfig

FIELDS = (
    ("mode", "Mode"),
    ("max_speed", "Max speed (×2 °/s)"),
    ("max_acceleration", "Max acceleration (×2 °/s²)"),
    ("jerk_slope", "Jerk slope (ms)"),
    ("max_torque", "Max torque (0–65535)"),
)
MODES = ("Position", "Speed", "Torque")


def build_config(index, selected, values):
    parameters = {}
    mask = 0
    for bit, ((name, label), enabled, text) in enumerate(zip(FIELDS, selected, values)):
        if not enabled:
            continue
        mask |= 1 << bit
        if name == "mode":
            parameters[name] = MODES.index(text)
        else:
            try:
                value = int(text)
            except ValueError:
                raise ValueError(f"{label}: enter an integer") from None
            if not 0 <= value <= 65535:
                raise ValueError(f"{label}: enter 0–65535")
            parameters[name] = value
    if not mask:
        raise ValueError("Select at least one field")
    return ExternalMotorsControlConfig(motors=1 << index, data_set=mask, **parameters)


class ConfigPanel(ttk.LabelFrame):
    def __init__(self, parent, index, submit):
        super().__init__(parent, text=f"DRV{index + 1} configuration", padding=8)
        self.index, self.submit = index, submit
        self.connected = self.busy = False
        self.selected = [tk.BooleanVar(value=False) for _ in FIELDS]
        self.values = [tk.StringVar(value="Position" if i == 0 else "0") for i in range(5)]
        self.inputs = []
        self.columnconfigure(1, weight=1)
        for row, ((name, label), selected, value) in enumerate(
            zip(FIELDS, self.selected, self.values)
        ):
            ttk.Checkbutton(self, text=label, variable=selected, command=self.refresh).grid(
                row=row, column=0, sticky="w", pady=3
            )
            entry = (
                ttk.Combobox(self, textvariable=value, values=MODES, width=12)
                if row == 0
                else ttk.Entry(self, textvariable=value, width=12)
            )
            entry.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=3)
            self.inputs.append(entry)
        self.button = ttk.Button(self, text=f"Send DRV{index + 1} config", command=self.send)
        self.button.grid(row=5, column=0, columnspan=2, sticky="ew", pady=8)
        self.status = tk.StringVar(value="Check fields to include in DATA_SET")
        label = ttk.Label(self, textvariable=self.status, wraplength=300)
        label.grid(row=6, column=0, columnspan=2, sticky="ew")
        self.bind("<Configure>", lambda event: label.config(wraplength=max(100, event.width - 20)))
        self.refresh()

    def refresh(self):
        for i, (selected, entry) in enumerate(zip(self.selected, self.inputs)):
            entry.config(
                state=("readonly" if i == 0 else "normal") if selected.get() else "disabled"
            )
        self.button.config(
            state="normal"
            if self.connected and not self.busy and any(v.get() for v in self.selected)
            else "disabled"
        )

    def send(self):
        if not self.connected or self.busy:
            return
        try:
            config = build_config(
                self.index, [v.get() for v in self.selected], [v.get() for v in self.values]
            )
        except ValueError as error:
            self.status.set(str(error))
            return
        self.busy = True
        self.status.set(f"DATA_SET=0x{config.data_set:02X} • waiting for confirmation…")
        self.refresh()
        self.submit(self.index, config)


class ConfigRunner:
    def __init__(self, device, requests, emit):
        self.device, self.requests, self.emit = device, requests, emit
        self.pending = None

    def tick(self):
        if self.pending is not None:
            index, future = self.pending
            if not future.done():
                return
            self.pending = None
            try:
                reply = future.result()
                if reply is None or reply.status != ConfirmationStatus.RECEIVED:
                    raise ValueError(f"Configuration rejected: {reply!r}")
                message = "Controller confirmed configuration"
            except Exception as error:
                message = f"{type(error).__name__}: {error} • no automatic retry"
            self.emit(("config", (index, message)))
        try:
            index, config = self.requests.get_nowait()
        except queue.Empty:
            return
        try:
            self.pending = (
                index,
                self.device.configure_ext_motors(config, need_confirmation=True, timeout=1.0),
            )
        except Exception as error:
            self.emit(("config", (index, f"{type(error).__name__}: {error}")))
