"""Desktop monitor built on the supplied sbgc32 library."""

import logging
import math
import queue
import threading
import tkinter as tk
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import monotonic
from tkinter import ttk

from connection import DiagnosticSimpleBGC as SimpleBGC
from motor_actions import ACTIONS, ActionRunner
from motor_config import ConfigPanel, ConfigRunner
from motor_control import ControlSender
from motor_state import MotorReader
from motor_status import MotorStatus
from serial.tools import list_ports

CONNECTION_TIMEOUT = 5.0
logger = logging.getLogger(__name__)


class AngleDial(ttk.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, padding=4)
        self.angle = self.target = None
        ttk.Label(self, text=title, font=("Segoe UI", 12, "bold")).pack()
        self.canvas = tk.Canvas(
            self, width=190, height=130, background="#f8fafc", highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, pady=3)
        self.value = ttk.Label(self, text="ANGLE16: —", foreground="#2563eb")
        self.value.pack()
        self.target_value = ttk.Label(self, text="ANGLE16_SETPOINT: —", foreground="#d97706")
        self.target_value.pack()
        self.canvas.bind("<Configure>", lambda event: self.draw())

    def update_angles(self, angle, target):
        self.angle, self.target = angle, target
        self.value.config(text="ANGLE16: —" if angle is None else f"ANGLE16: {angle:+.2f}°")
        self.target_value.config(
            text="ANGLE16_SETPOINT: —" if target is None else f"ANGLE16_SETPOINT: {target:+.2f}°"
        )
        self.draw()

    def draw(self):
        c = self.canvas
        c.delete("all")
        x, y = c.winfo_width() / 2, c.winfo_height() / 2
        r = max(10, min(x, y) - 30)
        c.create_oval(x - r, y - r, x + r, y + r, outline="#cbd5e1", width=2)
        for degrees in range(0, 360, 30):
            a = math.radians(degrees)
            c.create_line(
                x + (r - 7) * math.sin(a),
                y - (r - 7) * math.cos(a),
                x + r * math.sin(a),
                y - r * math.cos(a),
                fill="#94a3b8",
            )
        for degrees, label in [(0, "0°"), (90, "+90°"), (180, "±180°"), (270, "−90°")]:
            a = math.radians(degrees)
            c.create_text(
                x + (r + 19) * math.sin(a), y - (r + 19) * math.cos(a), text=label, fill="#64748b"
            )
        for angle, color, length, width, tag in (
            (self.target, "#d97706", 0.62, 6, "target_arrow"),
            (self.angle, "#2563eb", 0.88, 3, "actual_arrow"),
        ):
            if angle is not None:
                a = math.radians(angle)
                c.create_line(
                    x,
                    y,
                    x + r * length * math.sin(a),
                    y - r * length * math.cos(a),
                    fill=color,
                    width=width,
                    arrow=tk.LAST,
                    arrowshape=(12, 14, 5),
                    tags=tag,
                )
        if self.angle is not None or self.target is not None:
            c.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#475569", outline="")


class Monitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SimpleBGC — Board Monitor")
        self.geometry("1100x740")
        self.minsize(950, 620)
        self.events = queue.Queue()
        self.stop = threading.Event()
        self.reset_requested = threading.Event()
        self.worker = None
        self.closing = False
        self.protocol("WM_DELETE_WINDOW", self.close_window)

        toolbar = ttk.Frame(self, padding=16)
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="COM port:").pack(side="left", padx=(0, 8))
        self.port = ttk.Combobox(toolbar, state="readonly", width=36)
        self.port.pack(side="left")
        self.refresh = ttk.Button(toolbar, text="Refresh", command=self.refresh_ports)
        self.refresh.pack(side="left", padx=8)
        self.connect = ttk.Button(toolbar, text="Connect", command=self.toggle_connection)
        self.connect.pack(side="left")
        self.reset_button = ttk.Button(
            toolbar, text="Reset SBGC", state="disabled", command=self.request_reset
        )
        self.reset_button.pack(side="left", padx=8)
        self.board = tk.StringVar(value="Board: —    Firmware: —")
        ttk.Label(self, textvariable=self.board, padding=(16, 0), font=("Segoe UI", 12)).pack(
            anchor="w"
        )
        body = ttk.Frame(self, padding=(12, 8))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, minsize=220)
        body.rowconfigure(0, weight=1)
        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        self.controls_canvas = tk.Canvas(left, highlightthickness=0, width=700, height=400)
        self.controls_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.controls_canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.controls_canvas.configure(yscrollcommand=scrollbar.set)
        controls = ttk.Frame(self.controls_canvas)
        self.controls_frame = controls
        content_id = self.controls_canvas.create_window((0, 0), window=controls, anchor="nw")
        controls.bind(
            "<Configure>",
            lambda event: self.controls_canvas.configure(
                scrollregion=self.controls_canvas.bbox("all")
            ),
        )
        self.controls_canvas.bind(
            "<Configure>",
            lambda event: self.controls_canvas.itemconfigure(content_id, width=event.width),
        )
        gauges = ttk.LabelFrame(body, text="Driver angles", padding=4)
        gauges.grid(row=0, column=1, sticky="nsew")
        gauges.columnconfigure(0, weight=1)
        self.dials = []
        for index, title in enumerate(("DRV1", "DRV2")):
            gauges.rowconfigure(index, weight=1, uniform="dial")
            dial = AngleDial(gauges, title)
            dial.grid(row=index, column=0, sticky="nsew")
            self.dials.append(dial)
        ttk.Label(gauges, text="Degrees • positive clockwise", font=("Segoe UI", 9)).grid(
            row=2, column=0, pady=4
        )
        motors = ttk.LabelFrame(
            controls, text="External motor state • 50 Hz (20 ms per driver)", padding=10
        )
        motors.pack(fill="x", pady=(0, 8))
        self.motor_enabled = [threading.Event(), threading.Event()]
        self.motor_checks = []
        self.connected = False
        self.motor_text = []
        for index in range(2):
            panel = ttk.Frame(motors)
            panel.grid(row=0, column=index, sticky="nsew", padx=8)
            motors.columnconfigure(index, weight=1, uniform="motor")
            self.motor_enabled[index].set()
            selected = tk.BooleanVar(value=True)
            self.motor_checks.append(selected)
            ttk.Checkbutton(
                panel,
                text=f"Poll DRV{index + 1}",
                variable=selected,
                command=lambda i=index: self.toggle_motor(i),
            ).pack(anchor="w", pady=(0, 6))
            value = tk.StringVar(value="Disconnected")
            self.motor_text.append(value)
            telemetry = ttk.Label(panel, textvariable=value, justify="left", wraplength=340)
            telemetry.pack(fill="x")
            panel.bind(
                "<Configure>",
                lambda event, label=telemetry: label.config(wraplength=max(100, event.width)),
            )
        actions = ttk.LabelFrame(controls, text="External motor actions", padding=10)
        actions.pack(fill="x", pady=8)
        targets = ttk.Frame(actions)
        targets.pack(fill="x")
        self.action_targets = [tk.BooleanVar(value=False), tk.BooleanVar(value=False)]
        self.action_requests = queue.Queue()
        self.action_busy = False
        self.action_buttons = []
        for index, selected in enumerate(self.action_targets):
            ttk.Checkbutton(
                targets,
                text=f"Execute on DRV{index + 1}",
                variable=selected,
                command=self.update_action_buttons,
            ).pack(side="left", padx=(0, 16))
        buttons = ttk.Frame(actions)
        buttons.pack(fill="x", pady=8)
        for position, (label, action) in enumerate(ACTIONS):
            button = ttk.Button(
                buttons,
                text=label,
                state="disabled",
                command=lambda a=action, name=label: self.request_action(a, name),
            )
            button.grid(row=position // 3, column=position % 3, sticky="ew", padx=3, pady=3)
            buttons.columnconfigure(position % 3, weight=1)
            self.action_buttons.append(button)
        self.action_status = tk.StringVar(value="Select driver(s) to enable actions")
        ttk.Label(actions, textvariable=self.action_status, wraplength=650).pack(anchor="w")
        state_blocks = ttk.Frame(actions)
        state_blocks.pack(fill="x", pady=(8, 0))
        self.motor_status_blocks = []
        for index in range(2):
            state_blocks.columnconfigure(index, weight=1, uniform="driver_status")
            block = MotorStatus(state_blocks, index)
            block.grid(row=0, column=index, sticky="nsew", padx=3)
            self.motor_status_blocks.append(block)
        control = ttk.LabelFrame(
            controls, text="External motor control • DATA_SET = 0 • 50 ms", padding=10
        )
        control.pack(fill="x", pady=8)
        self.control_sender = ControlSender()
        self.control_running = False
        self.control_stopping = False
        self.control_targets = [tk.BooleanVar(value=False), tk.BooleanVar(value=False)]
        self.control_values = [tk.IntVar(value=0), tk.IntVar(value=0)]
        row = ttk.Frame(control)
        row.pack(fill="x")
        for index, selected in enumerate(self.control_targets):
            ttk.Checkbutton(
                row, text=f"DRV{index + 1}", variable=selected, command=self.update_control
            ).pack(side="left", padx=(0, 16))
        self.control_button = ttk.Button(
            row, text="Start sending", state="disabled", command=self.toggle_control
        )
        self.control_button.pack(side="right")
        sliders = ttk.Frame(control)
        sliders.pack(fill="x")
        self.control_home_buttons = []
        for index, value in enumerate(self.control_values):
            panel = ttk.Frame(sliders)
            panel.grid(row=0, column=index, sticky="ew", padx=6)
            sliders.columnconfigure(index, weight=1, uniform="setpoint")
            home = ttk.Button(
                panel, text=f"DRV{index + 1} Home (0)", command=lambda v=value: v.set(0)
            )
            home.pack(anchor="e")
            self.control_home_buttons.append(home)
            tk.Scale(
                panel,
                from_=-32768,
                to=32767,
                resolution=1,
                orient="horizontal",
                variable=value,
                label=f"DRV{index + 1} SETPOINT16 (raw)",
                sliderlength=28,
                troughcolor="#64748b",
                activebackground="#0891b2",
            ).pack(fill="x")
        self.control_status = tk.StringVar(value="Stopped • select driver(s)")
        ttk.Label(control, textvariable=self.control_status, wraplength=650).pack(anchor="w")
        for value in self.control_values:
            value.trace_add("write", lambda *_: self.update_control())
        configuration = ttk.Frame(controls)
        configuration.pack(fill="x", pady=8)
        self.config_requests = queue.Queue()
        self.config_panels = []
        for index in range(2):
            configuration.columnconfigure(index, weight=1, uniform="config")
            panel = ConfigPanel(
                configuration, index, lambda i, config: self.config_requests.put((i, config))
            )
            panel.grid(row=0, column=index, sticky="nsew", padx=4)
            self.config_panels.append(panel)
        self.status = tk.StringVar(value="Disconnected")
        ttk.Label(self, textvariable=self.status, padding=16, wraplength=850).pack(anchor="w")
        self.refresh_ports()
        self.after(10, self.process_events)

    def toggle_motor(self, index):
        if self.motor_checks[index].get():
            self.motor_enabled[index].set()
            self.motor_text[index].set("Waiting for data…" if self.connected else "Disconnected")
        else:
            self.motor_enabled[index].clear()
            self.motor_text[index].set("Polling disabled")
            self.dials[index].update_angles(None, None)
            self.motor_status_blocks[index].set_flags(None)

    def request_reset(self):
        if not self.connected or self.stop.is_set() or self.reset_requested.is_set():
            return
        self.connected = False
        self.control_running = False
        self.update_control()
        self.update_action_buttons()
        self.reset_button.config(state="disabled")
        self.connect.config(state="disabled")
        self.status.set("Sending controller reset…")
        self.reset_requested.set()

    def update_control(self):
        if not self.connected:
            for block in self.motor_status_blocks:
                block.set_flags(None)
        self.reset_button.config(
            state="normal" if self.connected and not self.stop.is_set() else "disabled"
        )
        for panel in self.config_panels:
            panel.connected = self.connected and not self.stop.is_set()
            if not panel.connected:
                panel.busy = False
                panel.status.set("Disconnected — configuration is not resent")
            panel.refresh()
        mask = sum(1 << i for i, value in enumerate(self.control_targets) if value.get())
        available = self.connected and not self.stop.is_set() and bool(mask)
        if not available:
            self.control_running = False
        self.control_sender.configure(
            self.control_running, mask, tuple(v.get() for v in self.control_values)
        )
        if self.control_stopping:
            button_text, status_text = "Stopping motors…", "Waiting for safe-stop confirmation"
        elif self.control_running:
            button_text, status_text = "Stop sending", "Sending every 50 ms"
        else:
            button_text, status_text = "Start sending", "Stopped"
        self.control_button.config(
            text=button_text,
            state="normal" if available and not self.control_stopping else "disabled",
        )
        self.control_status.set(
            f"{status_text} • "
            f"FOR_MOTORS = 0x{mask:02X} • DRV1 = {self.control_values[0].get()} • DRV2 = {self.control_values[1].get()}"
        )

    def toggle_control(self):
        if not self.connected or self.stop.is_set() or self.control_stopping:
            return
        if self.control_running:
            self.control_stopping = self.control_sender.request_stop()
            self.control_running = False
        else:
            self.control_running = True
        self.update_control()
        self.update_action_buttons()

    def update_action_buttons(self):
        enabled = (
            self.connected
            and not self.stop.is_set()
            and not self.action_busy
            and not self.control_stopping
            and any(selected.get() for selected in self.action_targets)
        )
        for button in self.action_buttons:
            button.config(state="normal" if enabled else "disabled")

    def request_action(self, action, label):
        mask = sum(1 << i for i, selected in enumerate(self.action_targets) if selected.get())
        if (
            not self.connected
            or self.stop.is_set()
            or self.action_busy
            or self.control_stopping
            or not mask
        ):
            return
        target = ", ".join(f"DRV{i + 1}" for i in range(2) if mask & (1 << i))
        self.action_busy = True
        self.update_action_buttons()
        self.action_status.set(f"{label} → {target}: waiting for confirmation…")
        self.action_requests.put((mask, action, f"{label} → {target}"))

    def refresh_ports(self):
        previous = self.port.get()
        try:
            self.ports = {
                f"{p.device} — {p.description}": p.device for p in sorted(list_ports.comports())
            }
        except Exception as error:
            self.status.set(f"Could not list COM ports: {error}")
            return
        self.port["values"] = list(self.ports)
        default_port = next(
            (label for label, device in self.ports.items() if device == "COM8"),
            next(iter(self.ports), ""),
        )
        self.port.set(previous if previous in self.ports else default_port)
        self.connect.config(state="normal" if self.ports else "disabled")
        self.status.set(
            "Select a port and click Connect"
            if self.ports
            else "No COM ports found. Connect your device and click Refresh."
        )

    def toggle_connection(self):
        if self.worker is not None:
            self.stop.set()
            self.connect.config(state="disabled")
            self.connected = False
            self.update_control()
            self.update_action_buttons()
            self.status.set("Disconnecting…")
            return
        port = self.ports.get(self.port.get())
        if not port:
            return
        self.stop.clear()
        self.reset_requested.clear()
        self.control_sender = ControlSender()
        self.control_running = False
        self.control_stopping = False
        self.action_requests = queue.Queue()
        self.config_requests = queue.Queue()
        self.action_busy = False
        self.port.config(state="disabled")
        self.refresh.config(state="disabled")
        self.connect.config(text="Disconnect")
        self.status.set(f"Connecting to {port}…")
        self.worker = threading.Thread(target=self.read_device, args=(port,), daemon=True)
        self.worker.start()

    def read_device(self, port):
        # All device I/O, including close(), stays outside the Tk event loop.
        reset_sent = False
        phase = "opening serial port"
        try:
            logger.info("Connecting to %s; board-info timeout=%.1fs", port, CONNECTION_TIMEOUT)
            with SimpleBGC(port=port) as gimbal:
                phase = "waiting for board information"
                board = gimbal.get_board_info(timeout=CONNECTION_TIMEOUT).result(
                    timeout=CONNECTION_TIMEOUT + 1
                )
                logger.info(
                    "Connected to %s: board=%s firmware=%s",
                    port,
                    board.board_version,
                    board.firmware_version,
                )
                phase = "communicating with controller"
                if not self.stop.is_set():
                    self.events.put(("board", (board.board_version, board.firmware_version)))
                motors = MotorReader(gimbal, self.motor_enabled, self.events.put)
                actions = ActionRunner(gimbal, self.action_requests, self.events.put)
                configs = ConfigRunner(gimbal, self.config_requests, self.events.put)
                while not self.stop.is_set():
                    if self.reset_requested.is_set():
                        # Wait for transmission only; the reboot may remove the port.
                        # Do not replay actions or resume control after reboot.
                        gimbal.reset(need_confirmation=False, restore_state=False).result(timeout=2)
                        reset_sent = True
                        break
                    now = monotonic()
                    actions.tick()
                    configs.tick()
                    self.control_sender.tick(gimbal, now, self.events.put)
                    motors.tick(now)
                    self.stop.wait(0.001)
        except Exception as error:
            logger.exception("Connection failure on %s while %s", port, phase)
            self.events.put(("error", f"{port}, {phase}: {type(error).__name__}: {error}"))
        finally:
            self.events.put(
                (
                    "done",
                    "Reset command sent. Wait for the controller to restart, then reconnect."
                    if reset_sent
                    else None,
                )
            )

    def process_events(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "board" and not self.stop.is_set():
                    self.board.set(f"Board: {data[0]}    Firmware: {data[1]}")
                    self.status.set("Connected • driver telemetry")
                    self.connected = True
                    self.update_control()
                    self.update_action_buttons()
                    for index, value in enumerate(self.motor_text):
                        value.set(
                            "Waiting for data…"
                            if self.motor_enabled[index].is_set()
                            else "Polling disabled"
                        )
                elif kind == "motor" and not self.stop.is_set():
                    index, message, actual, target, flags = data
                    if self.motor_enabled[index].is_set():
                        self.motor_text[index].set(message)
                        self.dials[index].update_angles(actual, target)
                        self.motor_status_blocks[index].set_flags(flags)
                elif kind == "action" and not self.stop.is_set():
                    self.action_busy = False
                    self.action_status.set(data)
                    self.update_action_buttons()
                elif kind == "config" and not self.stop.is_set():
                    index, message = data
                    panel = self.config_panels[index]
                    panel.busy = False
                    panel.status.set(message)
                    panel.refresh()
                elif kind in ("control_error", "control_stopped", "control_stop_error"):
                    self.control_running = False
                    self.control_stopping = False
                    self.update_control()
                    self.update_action_buttons()
                    self.control_status.set(data)
                elif kind == "error":
                    self.status.set(f"Connection error: {data}")
                elif kind == "done":
                    self.worker = None
                    self.connected = False
                    self.control_stopping = False
                    self.update_control()
                    self.action_busy = False
                    self.action_status.set("Disconnected — pending actions are not retried")
                    self.update_action_buttons()
                    self.port.config(state="readonly")
                    self.refresh.config(state="normal")
                    self.connect.config(text="Connect", state="normal")
                    self.board.set("Board: —    Firmware: —")
                    for dial in self.dials:
                        dial.update_angles(None, None)
                    for index, value in enumerate(self.motor_text):
                        value.set(
                            "Disconnected"
                            if self.motor_enabled[index].is_set()
                            else "Polling disabled"
                        )
                    if not self.status.get().startswith("Connection error:"):
                        self.status.set(data or "Disconnected")
        except queue.Empty:
            pass
        if self.closing and self.worker is None:
            self.destroy()
            return
        self.after(10, self.process_events)

    def close_window(self):
        self.closing = True
        self.connected = False
        self.update_control()
        self.update_action_buttons()
        self.stop.set()
        self.connect.config(state="disabled")
        self.refresh.config(state="disabled")
        self.status.set("Closing connection…")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            RotatingFileHandler(
                Path(__file__).with_name("motor-state.log"),
                maxBytes=1_000_000,
                backupCount=2,
                encoding="utf-8",
            )
        ],
    )
    Monitor().mainloop()
