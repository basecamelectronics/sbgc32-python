"""Telemetry-driven indicators for the mutually exclusive motor states."""

import tkinter as tk
from tkinter import ttk

STATES = (
    ("OFF BRAKE", "#2563eb"),
    ("ON", "#15803d"),
    ("OFF FLOATING", "#b45309"),
    ("OFF SAFE STOP", "#b91c1c"),
)


class MotorStatus(ttk.LabelFrame):
    def __init__(self, parent, index):
        super().__init__(parent, text=f"DRV{index + 1} • STATE_FLAGS", padding=6)
        self.cells = []
        for i, (name, _) in enumerate(STATES):
            cell = tk.Label(self, text=name, padx=6, pady=6, anchor="center")
            cell.grid(row=i // 2, column=i % 2, sticky="ew", padx=2, pady=2)
            self.columnconfigure(i % 2, weight=1, uniform="state")
            self.cells.append(cell)
        self.index_pin = tk.Label(self, padx=6, pady=6, anchor="center")
        self.index_pin.grid(row=2, column=0, columnspan=2, sticky="ew", padx=2, pady=2)
        self.description = ttk.Label(self)
        self.description.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.set_flags(None)

    def set_flags(self, flags):
        active = None if flags is None else flags & 3
        for i, (cell, (name, color)) in enumerate(zip(self.cells, STATES)):
            selected = active == i
            cell.config(
                text=("● " if selected else "") + name,
                background=color if selected else "#e2e8f0",
                foreground="white" if selected else "#475569",
            )
        self.description.config(
            text="No current telemetry" if flags is None else f"Active: {STATES[active][0]}"
        )
        pin_high = flags is not None and bool(flags & (1 << 2))
        self.index_pin.config(
            text="INDEX PIN: —"
            if flags is None
            else f"INDEX PIN: {'HIGH (1)' if pin_high else 'LOW (0)'}",
            background="#e2e8f0" if flags is None else ("#15803d" if pin_high else "#475569"),
            foreground="#475569" if flags is None else "white",
        )
