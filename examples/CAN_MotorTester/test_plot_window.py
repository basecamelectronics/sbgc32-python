import importlib.util
import os
import queue
import threading
import time
import unittest
from unittest.mock import patch

AVAILABLE = all(importlib.util.find_spec(name) for name in ("numpy", "pyqtgraph", "PySide6"))


@unittest.skipUnless(AVAILABLE, "Install requirements-plots.txt for Qt tests")
class PlotWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from plot_window import QtWidgets

        cls.application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        from plot_window import PlotWindow

        self.window = PlotWindow(queue.Queue(), queue.Queue(), threading.Event())
        self.window.timer.stop()
        self.window.show()
        self.application.processEvents()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.application.processEvents()

    def sample(self, sequence, generation=0, value=10):
        self.window.consume(
            ("sample", generation, 0, self.window.origin + sequence * 0.02, sequence, (value,) * 21)
        )

    def test_single_plot_with_independent_signal_selection(self):
        from plot_window import FIELDS, pg

        self.assertEqual(len(self.window.findChildren(pg.PlotWidget)), 1)
        chart = self.window.chart
        for field in (9, 10, 1, 2, 16, 17, 18, 19):
            chart.add_signal(field)
        self.assertEqual(len(chart.curves), 10)
        self.assertEqual(sum(s.enabled.isChecked() for s in chart.selectors), 10)
        values = tuple(range(21))
        for driver in range(2):
            self.window.consume(
                (
                    "sample",
                    0,
                    driver,
                    self.window.origin,
                    1,
                    tuple(value + driver * 100 for value in values),
                )
            )
        for index, selector in enumerate(chart.selectors):
            self.assertEqual(selector.field.count(), len(FIELDS))
            selector.field.setCurrentIndex(index)
            selector.driver.setCurrentIndex(index % 2)
            selector.enabled.setChecked(True)
        self.window.render()
        for index, curve in enumerate(chart.curves):
            self.assertTrue(curve.isVisible())
            self.assertEqual(curve.yData.tolist(), [index + (index % 2) * 100])
            self.assertIs(curve.getViewBox(), chart.plot.getViewBox())
        self.assertEqual(chart.axis_label, "Value (units in legend)")
        self.assertIn("[rpm]", chart.legend_labels[5])
        chart.selectors[0].enabled.setChecked(False)
        self.assertFalse(chart.curves[0].isVisible())
        self.assertTrue(chart.curves[1].isVisible())

    def test_axis_unit_tracks_visible_signals(self):
        chart = self.window.chart
        self.assertEqual(chart.axis_label, "rpm")
        chart.add_signal(9)
        chart.selectors[2].enabled.setChecked(True)
        self.assertEqual(chart.axis_label, "Value (units in legend)")
        chart.selectors[2].enabled.setChecked(False)
        self.assertEqual(chart.axis_label, "rpm")
        for selector in chart.selectors:
            selector.enabled.setChecked(False)
        self.assertTrue(all(not curve.isVisible() for curve in chart.curves))
        chart.selectors[2].enabled.setChecked(True)
        self.assertEqual(chart.axis_label, "deg")

    def test_add_remove_rows_and_recover_from_empty_plot(self):
        chart = self.window.chart
        self.assertEqual(len(chart.selectors), 2)
        chart.add_button.click()
        self.assertEqual(len(chart.selectors), 3)
        chart.selectors[1].remove.click()
        self.assertEqual(len(chart.curves), 2)
        while chart.selectors:
            chart.selectors[0].remove.click()
        self.assertEqual(len(chart.plot.plotItem.legend.items), 0)
        chart.add_button.click()
        self.sample(1)
        self.window.render()
        self.assertEqual(chart.curves[0].yData.tolist(), [10])

    def test_slow_telemetry_is_connected_with_measurement_markers(self):
        import numpy as np

        # Reproduce the log: absent DRV2 delays each valid DRV1 reply by ~1 s.
        for sequence in range(3):
            self.window.samples.put(
                (
                    "sample",
                    0,
                    0,
                    self.window.origin + sequence * 1.1,
                    sequence,
                    (10 + sequence,) * 21,
                )
            )
        self.window.tick()
        curve = self.window.chart.curves[0]
        np.testing.assert_allclose(curve.yData, [10, 11, 12])
        self.assertEqual(curve.opts["connect"], "finite")
        self.assertTrue(curve.opts["antialias"])
        self.assertEqual(len(curve.isolated_points.points()), 3)
        np.testing.assert_allclose(curve.isolated_points.getData()[1], [10, 11, 12])

    def test_light_palette_and_plot(self):
        from plot_window import QtGui

        self.assertEqual(self.window.palette().color(QtGui.QPalette.Window).name(), "#ffffff")
        self.assertEqual(self.window.chart.plot.backgroundBrush().color().name(), "#ffffff")

    def test_legend_click_updates_the_visibility_checkbox(self):
        self.sample(1)
        self.window.render()
        panel = self.window.chart
        curve = panel.curves[0]
        curve.setVisible(False)
        panel.plot.plotItem.legend.items[0][0].sigClicked.emit(curve)
        self.assertFalse(panel.selectors[0].enabled.isChecked())
        self.window.render()
        self.assertFalse(curve.isVisible())

    def test_pause_freezes_view_but_acquisition_continues(self):
        self.sample(1)
        self.window.pause.setChecked(True)
        self.sample(2, value=20)
        self.window.render()
        curve = self.window.chart.curves[0]
        self.assertEqual(curve.yData.tolist(), [10])
        self.assertEqual(self.window.history.counts[0], 2)
        self.window.pause.setChecked(False)
        self.assertEqual(curve.yData.tolist(), [10, 20])

    def test_new_connection_discards_old_generation(self):
        self.sample(1, generation=1)
        self.sample(2, generation=2, value=20)
        self.sample(3, generation=1, value=99)
        self.assertEqual(self.window.history.snapshot()[0][:, 1].tolist(), [20])
        self.window.consume(("reset", 3))
        self.assertEqual(self.window.history.counts, [0, 0])

    def test_clear_ignores_already_queued_old_samples(self):
        self.sample(1)
        self.window.clear_history()
        self.window.consume(("sample", 0, 0, self.window.accept_after - 0.01, 2, (20,) * 21))
        self.assertEqual(self.window.history.counts, [0, 0])

    def test_manual_y_and_time_controls(self):
        panel = self.window.chart
        panel.auto_y.setChecked(False)
        panel.y_min.setValue(-25)
        panel.y_max.setValue(75)
        self.assertEqual(panel.plot.viewRange()[1], [-25, 75])
        panel.y_min.setValue(100)
        self.assertIn("less than", panel.note.text())
        panel.manual_range((True, False))
        self.assertFalse(self.window.follow.isChecked())
        self.window.time_window.setValue(5)
        self.assertTrue(self.window.follow.isChecked())
        self.application.processEvents()
        start, end = panel.plot.viewRange()[0]
        self.assertAlmostEqual(end - start, 5)


@unittest.skipUnless(AVAILABLE, "Install requirements-plots.txt for process tests")
class PlotProcessTests(unittest.TestCase):
    def test_spawn_close_and_reopen_without_hardware(self):
        from plot_bridge import PlotBridge

        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        bridge = PlotBridge()
        try:
            for _ in range(2):
                bridge.start()
                deadline = time.monotonic() + 15
                ready = False
                while time.monotonic() < deadline and bridge.active:
                    events = bridge.poll()
                    self.assertFalse([event for event in events if event[0] == "error"], events)
                    if any(event[0] == "ready" for event in events):
                        ready = True
                        break
                    time.sleep(0.03)
                self.assertTrue(ready, "Graph process did not start")
                bridge.publish(0, time.monotonic(), (10,) * 21)
                bridge.reset()
                bridge.stop()
                deadline = time.monotonic() + 6
                while bridge.active and time.monotonic() < deadline:
                    bridge.poll()
                    time.sleep(0.03)
                self.assertFalse(bridge.active, "Graph process did not exit")
        finally:
            if bridge.active:
                bridge.stop()
                deadline = time.monotonic() + 6
                while bridge.active and time.monotonic() < deadline:
                    bridge.poll()
                    time.sleep(0.03)


@unittest.skipUnless(AVAILABLE and os.name == "nt", "Windows Tk/Qt lifecycle smoke test")
class TkPlotLifecycleTests(unittest.TestCase):
    def test_main_window_closes_its_viewer_without_a_serial_connection(self):
        from app import Monitor

        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        with patch("app.list_ports.comports", return_value=[]):
            monitor = Monitor()
        monitor.withdraw()
        try:
            monitor.toggle_graphs()
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline and monitor.graph_status.get() != "Graphs open":
                monitor.update()
                time.sleep(0.03)
            self.assertEqual(monitor.graph_status.get(), "Graphs open")
            self.assertIsNone(monitor.worker)
            monitor.close_window()
            deadline = time.monotonic() + 6
            while monitor.plotter.active and time.monotonic() < deadline:
                monitor.update()
                time.sleep(0.03)
            self.assertFalse(monitor.plotter.active)
        finally:
            if monitor.plotter.active:
                monitor.plotter.stop()
                deadline = time.monotonic() + 6
                while monitor.plotter.active and time.monotonic() < deadline:
                    monitor.plotter.poll()
                    time.sleep(0.03)
            try:
                monitor.destroy()
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
