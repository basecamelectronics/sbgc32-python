import queue
import unittest
from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import Mock

from motor_config import ConfigRunner, ConfirmationStatus, build_config


class ConfigTests(unittest.TestCase):
    def test_fields_and_targets(self):
        for index in (0, 1):
            for bit in range(6):
                config = build_config(
                    index, [i == bit for i in range(6)], ["Speed", "50", "100", "200", "300", "400"]
                )
                self.assertEqual(config.motors, 1 << index)
                self.assertEqual(config.data_set, 1 << bit)
        config = build_config(1, [True] * 6, ["Torque", "10", "21845", "0", "10", "200"])
        self.assertEqual((config.mode, config.max_speed, config.jerk_slope), (2, 65535, 10))

    def test_validation_and_omitted_values(self):
        build_config(
            0, [True, False, False, False, False, False], ["Position", "invalid", "", "", "", ""]
        )
        for value in ("-1", "21845.01", "65536", "NaN", "Infinity", "-Infinity", ""):
            with self.assertRaises(ValueError):
                build_config(
                    0,
                    [False, True, False, False, False, False],
                    ["Position", value, "0", "0", "0", "0"],
                )
        with self.assertRaises(ValueError):
            build_config(0, [False] * 6, ["Position", "0", "0", "0", "0", "0"])

    def test_rpm_limits_are_converted_to_protocol_units(self):
        for bit, name in ((1, "default_speed"), (2, "max_speed"), (3, "max_acceleration")):
            for text, expected in (
                ("0", 0),
                ("10", 30),
                ("1.5", 5),
                ("0.166666", 0),
                ("0.166667", 1),
                ("21845", 65535),
            ):
                with self.subTest(field=name, value=text):
                    values = ["Speed", "invalid", "invalid", "invalid", "0", "0"]
                    values[bit] = text
                    config = build_config(0, [i == bit for i in range(6)], values)
                    self.assertEqual(getattr(config, name), expected)
            for text in ("-0.01", "21845.01", "NaN", "Infinity", ""):
                values = ["Speed", "0", "0", "0", "0", "0"]
                values[bit] = text
                with self.assertRaises(ValueError):
                    build_config(0, [i == bit for i in range(6)], values)

    def test_other_configuration_fields_still_require_integers(self):
        for bit in (4, 5):
            values = ["Speed", "0", "0", "0", "0", "0"]
            values[bit] = "1.5"
            with self.assertRaises(ValueError):
                build_config(0, [i == bit for i in range(6)], values)

    def test_send_once_and_confirmation(self):
        device, requests, events = Mock(), queue.Queue(), []
        future = Future()
        device.configure_ext_motors.return_value = future
        config = build_config(1, [True] * 6, ["Speed", "1", "2", "3", "4", "5"])
        runner = ConfigRunner(device, requests, events.append)
        requests.put((1, config))
        runner.tick()
        runner.tick()
        device.configure_ext_motors.assert_called_once_with(
            config, need_confirmation=True, timeout=1.0
        )
        future.set_result(SimpleNamespace(status=ConfirmationStatus.ERROR))
        runner.tick()
        runner.tick()
        self.assertEqual(events[0][1][0], 1)
        self.assertIn("rejected", events[0][1][1])
        self.assertEqual(device.configure_ext_motors.call_count, 1)
