"""Nonblocking, optional bridge from Tkinter to a separate Qt process."""

import importlib.util
import multiprocessing
import queue
import traceback
from time import monotonic

INSTALL_HINT = "py -m pip install -r examples/CAN_MotorTester/requirements-plots.txt"


def _run_window(samples, reports, stop):
    try:
        # Import Qt only in the child: Tkinter owns the parent event loop.
        from plot_window import run_window

        run_window(samples, reports, stop)
    except Exception:
        reports.put(("error", traceback.format_exc()))


class PlotBridge:
    """All public methods are called by the Tk thread; no serial access here."""

    def __init__(self):
        self.process = None
        self.samples = self.reports = self.stop_event = None
        self.deadline = None
        self.generation = 0
        self.sequences = [0, 0]
        self.dropped = 0

    @property
    def active(self):
        return self.process is not None

    def start(self):
        if self.active:
            return
        missing = [
            name
            for name in ("numpy", "pyqtgraph", "PySide6")
            if importlib.util.find_spec(name) is None
        ]
        if missing:
            raise RuntimeError(f"Missing: {', '.join(missing)}. Install with:\n{INSTALL_HINT}")
        context = multiprocessing.get_context("spawn")
        self.samples = context.Queue(maxsize=512)
        self.samples.cancel_join_thread()
        self.reports = context.Queue()
        self.stop_event = context.Event()
        self.process = context.Process(
            target=_run_window,
            args=(self.samples, self.reports, self.stop_event),
            daemon=True,
        )
        try:
            self.process.start()
        except Exception:
            self.process = None
            self.samples.close()
            self.reports.close()
            raise
        self.deadline = None
        self.dropped = 0

    def _send(self, message):
        if not self.active or self.deadline is not None:
            return
        try:
            self.samples.put_nowait(message)
        except queue.Full:
            self.dropped += 1

    def publish(self, motor, timestamp, values):
        self.sequences[motor] += 1
        self._send(("sample", self.generation, motor, timestamp, self.sequences[motor], values))

    def reset(self):
        self.generation += 1
        self.sequences = [0, 0]
        self._send(("reset", self.generation))

    def stop(self):
        if self.active and self.deadline is None:
            self.stop_event.set()
            self.deadline = monotonic() + 2.0

    def poll(self):
        if not self.active:
            return []
        events = []
        while True:
            try:
                events.append(self.reports.get_nowait())
            except queue.Empty:
                break
        if self.deadline is not None and monotonic() >= self.deadline and self.process.is_alive():
            self.process.terminate()
            self.deadline = monotonic() + 1.0
        if not self.process.is_alive():
            self.process.join(timeout=0)
            if self.process.exitcode and self.deadline is None:
                events.append(("error", f"Graph process exited with code {self.process.exitcode}"))
            self.process.close()
            self.process = None
            self.samples.close()
            self.reports.close()
            self.samples = self.reports = self.stop_event = None
            self.deadline = None
            events.append(("closed", "Graphs closed"))
        return events
