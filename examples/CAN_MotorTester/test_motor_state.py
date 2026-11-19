import threading
import unittest
from concurrent.futures import Future
from unittest.mock import patch

from motor_state import DATA_SET, RESULT_SIZE, STATE, MotorReader, angles16, format_state
from motor_telemetry import decode_state


class Device:
    def __init__(self):
        self.calls = []
        self.futures = []

    def request_motor_state(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        future = Future()
        self.futures.append(future)
        return future


class MotorStateTests(unittest.TestCase):
    def test_plot_samples_share_one_decode_and_report_gaps(self):
        device = Device()
        enabled = [threading.Event(), threading.Event()]
        enabled[0].set()
        events, samples = [], []
        reader = MotorReader(
            device, enabled, events.append, sample_emit=lambda *sample: samples.append(sample)
        )
        reader.tick(0)
        raw = list(STATE.unpack(bytes(STATE.size)))
        raw[5] = 1000000
        with patch("motor_state.decode_state", wraps=decode_state) as decoder:
            device.futures[0].set_result(STATE.pack(*raw))
            reader.tick(0.01)
            decoder.assert_called_once()
        self.assertEqual(samples[0][:2], (0, 0.01))
        self.assertAlmostEqual(samples[0][2][5], 9.5492965855)
        self.assertIn("9.55 rpm", events[0][1][1])
        reader.tick(0.02)
        device.futures[1].set_exception(TimeoutError("No reply"))
        reader.tick(1.02)
        self.assertEqual(samples[-1], (0, 1.02, None))

    def test_units_and_layout(self):
        payload = STATE.pack(
            1,
            32767,
            -32767,
            0,
            0,
            1000000,
            0,
            0,
            0,
            1048576,
            -524288,
            5,
            15,
            30,
            50,
            200,
            65535,
            1200,
            24000,
            -5,
            42,
        )
        text = format_state(payload)
        for expected in (
            "Speed | On | Index: True",
            "360.00°",
            "-180.00°",
            "Speed: 9.55 rpm | Target: 0.00 rpm",
            "100.0%",
            "Limits: 10.00 rpm, 16.67 rpm/s",
            "24.00 V",
            "-5°C",
        ):
            self.assertIn(expected, text)
        self.assertEqual(STATE.size, 47)
        with self.assertRaises(ValueError):
            format_state(payload[:-1])

    def test_signed_speed_and_limit_extremes_in_rpm(self):
        values = list(STATE.unpack(bytes(STATE.size)))
        values[5:7] = [-1000000, 6283185]
        values[13:15] = [65535, 0]
        text = format_state(STATE.pack(*values))
        self.assertIn("Speed: -9.55 rpm | Target: 60.00 rpm", text)
        self.assertIn("Limits: 21845.00 rpm, 0.00 rpm/s", text)

    def test_angles16_use_signed_16_bit_fields(self):
        values = list(STATE.unpack(bytes(STATE.size)))
        values[7:11] = [-4096, 8192, 123456, -654321]
        self.assertEqual(angles16(STATE.pack(*values)), (-90.0, 180.0))

    def test_periodic_requests_and_selection(self):
        device = Device()
        enabled = [threading.Event(), threading.Event()]
        for flag in enabled:
            flag.set()
        events = []
        reader = MotorReader(device, enabled, events.append)
        reader.tick(0)
        self.assertEqual(device.calls[0][0], (1, DATA_SET, RESULT_SIZE))
        reader.tick(0.001)
        self.assertEqual(len(device.calls), 1)
        device.futures[0].set_result(bytes(STATE.size))
        reader.tick(0.002)
        self.assertEqual(device.calls[1][0][0], 2)
        device.futures[1].set_result(bytes(STATE.size))
        reader.tick(0.003)
        reader.tick(0.019)
        self.assertEqual(len(device.calls), 2)
        reader.tick(0.020)
        self.assertEqual(device.calls[2][0][0], 1)
        enabled[0].clear()
        device.futures[2].set_result(bytes(STATE.size))
        count = len(events)
        reader.tick(0.021)
        self.assertEqual(len(events), count)
        reader.tick(0.022)
        self.assertEqual(device.calls[3][0][0], 2)
        device.futures[3].set_exception(TimeoutError("No reply"))
        reader.tick(1.022)
        self.assertIn("No state reply", events[-1][1][1])
        self.assertEqual(len(device.calls), 5)
        enabled[1].clear()
        device.futures[4].set_result(bytes(STATE.size))
        reader.tick(2)
        reader.tick(10)
        self.assertEqual(len(device.calls), 5)
        enabled[0].set()
        reader.tick(10.01)
        self.assertEqual(device.calls[5][0][0], 1)


if __name__ == "__main__":
    unittest.main()
