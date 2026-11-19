import importlib.util
import math
import queue
import unittest
from unittest.mock import Mock, patch

from motor_telemetry import FIELDS, STATE, decode_state
from plot_bridge import PlotBridge


class TelemetryTests(unittest.TestCase):
    def test_all_fields_use_shared_display_units(self):
        raw = (
            1,
            32767,
            -32767,
            6,
            -6,
            1000000,
            -1000000,
            4096,
            -4096,
            1048576,
            -524288,
            5,
            15,
            30,
            60,
            100,
            65535,
            1200,
            24000,
            -5,
            42,
        )
        values = decode_state(STATE.pack(*raw))
        self.assertEqual(len(FIELDS), 21)
        self.assertEqual(len({field.name for field in FIELDS}), 21)
        self.assertEqual(values[:3], (1, 100, -100))
        self.assertAlmostEqual(values[3], 0.1220740379)
        self.assertAlmostEqual(values[4], -0.1220740379)
        self.assertAlmostEqual(values[5], 30 / math.pi)
        self.assertAlmostEqual(values[6], -30 / math.pi)
        self.assertEqual(values[7:], (90, -90, 360, -180, 5, 5, 10, 20, 100, 100, 1200, 24, -5, 42))
        with self.assertRaises(ValueError):
            decode_state(bytes(44))


@unittest.skipUnless(importlib.util.find_spec("numpy"), "Install requirements-plots.txt")
class HistoryTests(unittest.TestCase):
    def setUp(self):
        import numpy as np
        from plot_history import PlotHistory

        self.np = np
        self.history = PlotHistory(capacity=4)

    def test_wrap_retains_chronological_order_and_separate_drivers(self):
        for i in range(7):
            self.history.append(0, i * 0.02, i, (i,) * 21)
        self.history.append(1, 0.12, 0, (99,) * 21)
        first, second = self.history.snapshot()
        self.np.testing.assert_allclose(first[:, 0], [0.06, 0.08, 0.10, 0.12])
        self.np.testing.assert_array_equal(first[:, 1], [3, 4, 5, 6])
        self.assertEqual(second[0, 1], 99)
        first[:] = -1
        self.assertEqual(self.history.snapshot()[0][-1, 1], 6)

    def test_slow_samples_connect_but_queue_loss_and_failure_insert_gaps(self):
        self.history.append(0, 0, 1, (1,) * 21)
        self.history.append(0, 1, 2, (2,) * 21)
        self.np.testing.assert_array_equal(self.history.snapshot()[0][:, 1], [1, 2])
        self.history.append(0, 1.02, 4, (3,) * 21)
        self.assertTrue(self.np.isnan(self.history.snapshot()[0][-2, 1:]).all())
        self.history.append(0, 1.03, 5, None)
        self.assertTrue(self.np.isnan(self.history.snapshot()[0][-1, 1:]).all())
        self.assertFalse(self.history.valid[0])

    def test_stale_samples_are_ignored_and_clear_resets_sequences(self):
        self.history.append(0, 1, 4, (1,) * 21)
        self.history.append(0, 0.9, 3, (2,) * 21)
        self.history.append(0, 1, 4, (3,) * 21)
        self.assertEqual(self.history.counts[0], 1)
        self.history.clear()
        self.history.append(0, 0, 0, (4,) * 21)
        self.assertEqual(self.history.counts, [1, 0])
        self.assertEqual(self.history.snapshot()[0][0, 1], 4)


class BridgeTests(unittest.TestCase):
    def test_full_queue_drops_only_display_samples_without_blocking(self):
        bridge = PlotBridge()
        bridge.process = Mock()
        bridge.samples = queue.Queue(maxsize=1)
        bridge.publish(0, 1, (1,) * 21)
        bridge.publish(0, 2, (2,) * 21)
        self.assertEqual(bridge.dropped, 1)
        self.assertEqual(bridge.samples.get_nowait()[4], 1)
        bridge.publish(0, 3, (3,) * 21)
        self.assertEqual(bridge.samples.get_nowait()[4], 3)

    def test_reset_generation_survives_a_full_queue(self):
        bridge = PlotBridge()
        bridge.process = Mock()
        bridge.samples = queue.Queue(maxsize=1)
        bridge.publish(0, 1, None)
        bridge.reset()
        bridge.samples.get_nowait()
        bridge.publish(1, 2, (2,) * 21)
        self.assertEqual(bridge.samples.get_nowait()[:5], ("sample", 1, 1, 2, 1))

    def test_missing_optional_packages_leave_monitor_available(self):
        bridge = PlotBridge()
        with patch("plot_bridge.importlib.util.find_spec", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "requirements-plots.txt"):
                bridge.start()
        self.assertFalse(bridge.active)

    def test_close_is_nonblocking_and_terminates_an_unresponsive_viewer(self):
        bridge = PlotBridge()
        process = Mock()
        process.is_alive.return_value = True
        bridge.process = process
        bridge.samples, bridge.reports, bridge.stop_event = Mock(), queue.Queue(), Mock()
        with patch("plot_bridge.monotonic", return_value=0):
            bridge.stop()
            bridge.stop()
        bridge.stop_event.set.assert_called_once()
        with patch("plot_bridge.monotonic", return_value=3):
            bridge.poll()
        process.terminate.assert_called_once()
        process.join.assert_not_called()


if __name__ == "__main__":
    unittest.main()
