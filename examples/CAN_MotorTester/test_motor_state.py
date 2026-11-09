import threading
import unittest
from concurrent.futures import Future

from motor_state import DATA_SET, RESULT_SIZE, STATE, MotorReader, angles16, format_state


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
            "57.30°/s",
            "100.0%",
            "60°/s",
            "24.00 V",
            "-5°C",
        ):
            self.assertIn(expected, text)
        self.assertEqual(STATE.size, 45)
        with self.assertRaises(ValueError):
            format_state(payload[:-1])

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
