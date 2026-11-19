"""Standalone PyQtGraph viewer; receives numbers and never opens a serial port."""

import queue
from time import monotonic

from PySide6 import QtCore, QtGui, QtWidgets

# Select PySide6 before PyQtGraph chooses a Qt binding.
# isort: split

import numpy as np
import pyqtgraph as pg
from motor_telemetry import FIELDS
from plot_history import PlotHistory

DEFAULT_SIGNALS = (5, 6, 9, 10, 1, 2, 17, 18, 19, 20)
COLORS = (
    "#2563eb", "#c2410c", "#15803d", "#be185d", "#a16207",
    "#7e22ce", "#0f766e", "#b91c1c", "#475569", "#4338ca",
)


class CurveSelector(QtWidgets.QWidget):
    def __init__(self, selected, color):
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        self.enabled = QtWidgets.QCheckBox()
        self.enabled.setChecked(True)
        self.enabled.setToolTip("Show this signal")
        self.enabled.setStyleSheet(f"QCheckBox {{ color: {color}; }}")
        self.enabled.setText("●")
        self.driver = QtWidgets.QComboBox()
        self.driver.addItems(("DRV1", "DRV2"))
        self.field = QtWidgets.QComboBox()
        self.field.setMinimumWidth(180)
        self.set_fields(range(len(FIELDS)), selected)
        self.remove = QtWidgets.QPushButton("Remove")
        layout.addWidget(self.enabled)
        layout.addWidget(self.driver)
        layout.addWidget(self.field, 1)
        layout.addWidget(self.remove)

    def set_fields(self, indices, selected):
        self.field.blockSignals(True)
        self.field.clear()
        for index in indices:
            field = FIELDS[index]
            self.field.addItem(f"{field.name} [{field.unit}]", index)
        position = self.field.findData(selected)
        self.field.setCurrentIndex(max(0, position))
        self.field.blockSignals(False)


class TelemetryPlot(QtWidgets.QWidget):
    def __init__(self, changed, manual_x):
        super().__init__()
        self.changed = changed
        self.manual_x = manual_x
        layout = QtWidgets.QHBoxLayout(self)
        controls = QtWidgets.QWidget()
        controls.setMinimumWidth(460)
        control_layout = QtWidgets.QVBoxLayout(controls)
        control_layout.setContentsMargins(0, 0, 0, 0)
        self.add_button = QtWidgets.QPushButton("+ Add signal")
        control_layout.addWidget(self.add_button)
        self.signal_layout = QtWidgets.QVBoxLayout()
        control_layout.addLayout(self.signal_layout)
        self.selectors = []
        self.curves = []
        self.next_color = 0
        self.auto_y = QtWidgets.QCheckBox("Auto Y")
        self.auto_y.setChecked(True)
        self.y_min = QtWidgets.QDoubleSpinBox()
        self.y_max = QtWidgets.QDoubleSpinBox()
        for spin, value, label in ((self.y_min, -100, "Min"), (self.y_max, 100, "Max")):
            spin.setRange(-1e9, 1e9)
            spin.setDecimals(3)
            spin.setValue(value)
            spin.setPrefix(f"{label} ")
            spin.setMaximumWidth(155)
        limits = QtWidgets.QHBoxLayout()
        limits.addWidget(self.auto_y)
        limits.addWidget(self.y_min)
        limits.addWidget(self.y_max)
        control_layout.addLayout(limits)
        self.note = QtWidgets.QLabel("All signals share one Y scale; units are shown in the legend")
        self.note.setWordWrap(True)
        control_layout.addWidget(self.note)
        control_layout.addStretch()
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(490)
        scroll.setMaximumWidth(520)
        scroll.setWidget(controls)
        layout.addWidget(scroll)
        self.plot = pg.PlotWidget(background="white")
        for name in ("left", "bottom"):
            self.plot.getAxis(name).setPen("#64748b")
            self.plot.getAxis(name).setTextPen("#334155")
        self.plot.setMinimumHeight(300)
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setLabel("bottom", "Time since graphs opened", units="s")
        self.plot.getAxis("left").enableAutoSIPrefix(False)
        self.plot.getAxis("left").setWidth(85)
        self.plot.getAxis("bottom").enableAutoSIPrefix(False)
        self.plot.addLegend(offset=(10, 5), labelTextColor="#334155",
                            brush=pg.mkBrush(255, 255, 255, 230))
        layout.addWidget(self.plot, 1)
        self.add_button.clicked.connect(lambda: self.add_signal())
        for field in DEFAULT_SIGNALS[:2]:
            self.add_signal(field, notify=False)
        self.auto_y.toggled.connect(self.apply_y)
        self.y_min.valueChanged.connect(self.apply_y)
        self.y_max.valueChanged.connect(self.apply_y)
        self.plot.getViewBox().sigRangeChangedManually.connect(self.manual_range)
        self.apply_y()

    def add_signal(self, selected=None, notify=True):
        if len(self.selectors) >= 10:
            return
        if selected is None:
            selected = DEFAULT_SIGNALS[len(self.selectors)]
        color = COLORS[self.next_color % len(COLORS)]
        self.next_color += 1
        selector = CurveSelector(selected, color)
        self.signal_layout.addWidget(selector)
        curve = self.plot.plot(pen=pg.mkPen(color, width=1.5), antialias=True)
        curve.setDownsampling(auto=True, method="peak")
        curve.setClipToView(True)
        curve.isolated_points = pg.ScatterPlotItem(size=5, pen=None, brush=color)
        self.plot.addItem(curve.isolated_points)
        curve.visibleChanged.connect(
            lambda: curve.isolated_points.setVisible(curve.isVisible())
        )
        self.selectors.append(selector)
        self.curves.append(curve)
        selector.enabled.toggled.connect(self.changed)
        selector.driver.currentIndexChanged.connect(self.changed)
        selector.field.currentIndexChanged.connect(self.changed)
        selector.remove.clicked.connect(lambda: self.remove_signal(selector))
        self.add_button.setEnabled(len(self.selectors) < 10)
        if notify:
            self.changed()

    def remove_signal(self, selector):
        index = self.selectors.index(selector)
        curve = self.curves.pop(index)
        self.plot.plotItem.legend.removeItem(curve)
        self.plot.removeItem(curve)
        self.plot.removeItem(curve.isolated_points)
        self.selectors.pop(index)
        self.signal_layout.removeWidget(selector)
        selector.deleteLater()
        self.legend_labels = None
        self.add_button.setEnabled(True)
        self.changed()

    def apply_y(self, *_):
        automatic = self.auto_y.isChecked()
        self.y_min.setEnabled(not automatic)
        self.y_max.setEnabled(not automatic)
        self.plot.getViewBox().enableAutoRange(pg.ViewBox.YAxis, automatic)
        if not automatic:
            if self.y_min.value() >= self.y_max.value():
                self.note.setText("Y minimum must be less than maximum")
                return
            self.plot.setYRange(self.y_min.value(), self.y_max.value(), padding=0)
        self.note.setText("All signals share one Y scale; units are shown in the legend")

    def manual_range(self, axes):
        if axes[0]:
            self.manual_x()
        if axes[1]:
            self.auto_y.blockSignals(True)
            self.auto_y.setChecked(False)
            self.auto_y.blockSignals(False)
            for spin, value in zip((self.y_min, self.y_max), self.plot.viewRange()[1]):
                spin.blockSignals(True)
                spin.setValue(value)
                spin.setEnabled(True)
                spin.blockSignals(False)

    def render(self, snapshots, origin):
        legend = self.plot.plotItem.legend
        labels = []
        for selector in self.selectors:
            field = FIELDS[selector.field.currentData()]
            labels.append(f"{selector.driver.currentText()} {field.name} [{field.unit}]")
        if labels != getattr(self, "legend_labels", None):
            legend.clear()
            for curve, label, selector in zip(self.curves, labels, self.selectors):
                legend.addItem(curve, label)
                legend.items[-1][0].sigClicked.connect(
                    lambda item, checkbox=selector.enabled: checkbox.setChecked(item.isVisible())
                )
            self.legend_labels = labels
        units = {
            FIELDS[selector.field.currentData()].unit
            for selector in self.selectors
            if selector.enabled.isChecked()
        }
        axis_label = next(iter(units)) if len(units) == 1 else "Value (units in legend)"
        if axis_label != getattr(self, "axis_label", None):
            self.plot.setLabel("left", axis_label)
            self.axis_label = axis_label
        for curve, selector in zip(self.curves, self.selectors):
            enabled = selector.enabled.isChecked()
            curve.setVisible(enabled)
            if not enabled:
                continue
            data = snapshots[selector.driver.currentIndex()]
            # Keep markers for sparse or isolated measurements alongside the line.
            values = data[:, selector.field.currentData() + 1]
            finite = np.isfinite(values)
            isolated = finite.copy()
            if len(values) > 1:
                close = np.diff(data[:, 0]) <= 0.25
                isolated[1:] &= ~(finite[:-1] & close)
                isolated[:-1] &= ~(finite[1:] & close)
            curve.setData(
                data[:, 0] - origin, values, connect="finite",
            )
            curve.isolated_points.setData(data[isolated, 0] - origin, values[isolated])


class PlotWindow(QtWidgets.QMainWindow):
    def __init__(self, samples, reports, stop):
        super().__init__()
        self.samples, self.reports, self.stop = samples, reports, stop
        self.origin = monotonic()
        self.accept_after = -np.inf
        self.generation = -1
        self.history = PlotHistory()
        self.paused_snapshot = None
        self.paused_time = None
        self.chart = None
        palette = QtGui.QPalette()
        for role, color in (
            (QtGui.QPalette.Window, "#ffffff"),
            (QtGui.QPalette.WindowText, "#1e293b"),
            (QtGui.QPalette.Base, "#ffffff"),
            (QtGui.QPalette.AlternateBase, "#f1f5f9"),
            (QtGui.QPalette.Text, "#1e293b"),
            (QtGui.QPalette.Button, "#f1f5f9"),
            (QtGui.QPalette.ButtonText, "#1e293b"),
            (QtGui.QPalette.Highlight, "#2563eb"),
            (QtGui.QPalette.HighlightedText, "#ffffff"),
            (QtGui.QPalette.ToolTipBase, "#ffffff"),
            (QtGui.QPalette.ToolTipText, "#1e293b"),
        ):
            palette.setColor(role, QtGui.QColor(color))
        self.setPalette(palette)
        self.setWindowTitle("SimpleBGC — Motor telemetry")
        self.resize(1400, 800)
        root = QtWidgets.QWidget()
        self.setCentralWidget(root)
        layout = QtWidgets.QVBoxLayout(root)
        toolbar = QtWidgets.QHBoxLayout()
        toolbar.addWidget(QtWidgets.QLabel("Time window:"))
        self.time_window = QtWidgets.QDoubleSpinBox()
        self.time_window.setRange(0.1, 300)
        self.time_window.setValue(10)
        self.time_window.setSuffix(" s")
        toolbar.addWidget(self.time_window)
        self.follow = QtWidgets.QCheckBox("Follow live")
        self.follow.setChecked(True)
        toolbar.addWidget(self.follow)
        self.pause = QtWidgets.QPushButton("Pause display")
        self.pause.setCheckable(True)
        toolbar.addWidget(self.pause)
        clear = QtWidgets.QPushButton("Clear history")
        clear.clicked.connect(self.clear_history)
        toolbar.addWidget(clear)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.chart = TelemetryPlot(self.render, lambda: self.follow.setChecked(False))
        layout.addWidget(self.chart, 1)
        self.time_window.valueChanged.connect(self.follow_time)
        self.follow.toggled.connect(self.render)
        self.pause.toggled.connect(self.pause_display)
        self.render()
        self.statusBar().showMessage("Waiting for telemetry — enable polling in the Tkinter window")
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.tick)
        self.timer.start()

    def follow_time(self, *_):
        self.follow.setChecked(True)
        self.render()

    def clear_history(self, *_):
        self.history.clear()
        self.accept_after = monotonic()
        if self.pause.isChecked():
            self.paused_snapshot = self.history.snapshot()
        self.render()

    def pause_display(self, paused):
        self.paused_snapshot = self.history.snapshot() if paused else None
        self.paused_time = monotonic() if paused else None
        self.pause.setText("Resume display" if paused else "Pause display")
        self.render()

    def consume(self, message):
        kind, generation, *sample = message
        if generation < self.generation:
            return
        if generation > self.generation:
            self.history.clear()
            self.generation = generation
            if self.pause.isChecked():
                self.paused_snapshot = self.history.snapshot()
        if kind == "sample":
            motor, timestamp, sequence, values = sample
            if timestamp >= self.accept_after:
                self.history.append(motor, timestamp, sequence, values)

    def tick(self):
        if self.stop.is_set():
            self.close()
            return
        deadline = monotonic() + 0.008
        for _ in range(512):
            try:
                self.consume(self.samples.get_nowait())
            except queue.Empty:
                break
            if monotonic() >= deadline:
                break
        if not self.pause.isChecked():
            self.render()
        now = monotonic()
        states = []
        for index, timestamp in enumerate(self.history.last_time):
            state = (
                "no current telemetry"
                if not self.history.valid[index]
                else f"last sample {now - timestamp:.1f} s ago"
            )
            states.append(f"DRV{index + 1}: {state}")
        mode = "Paused display; acquisition continues" if self.pause.isChecked() else "Live"
        self.statusBar().showMessage(
            f"{mode} | {' | '.join(states)} | Disable polling for unused drivers"
        )

    def render(self, *_):
        if self.chart is None:
            return
        snapshots = (
            self.paused_snapshot if self.paused_snapshot is not None else self.history.snapshot()
        )
        self.chart.render(snapshots, self.origin)
        if self.follow.isChecked():
            end = (self.paused_time if self.paused_time is not None else monotonic()) - self.origin
            self.chart.plot.setXRange(end - self.time_window.value(), end, padding=0)

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()


def run_window(samples, reports, stop):
    pg.setConfigOptions(antialias=True)
    application = QtWidgets.QApplication([])
    application.setStyle("Fusion")
    window = PlotWindow(samples, reports, stop)
    window.show()
    reports.put(("ready", "Graphs open"))
    application.exec()
