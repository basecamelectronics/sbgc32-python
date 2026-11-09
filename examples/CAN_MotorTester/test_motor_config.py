import queue
import unittest
from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import Mock

from motor_config import ConfigRunner, ConfirmationStatus, build_config


class ConfigTests(unittest.TestCase):
    def test_fields_and_targets(self):
        for index in (0, 1):
            for bit in range(5):
                config = build_config(
                    index, [i == bit for i in range(5)], ["Speed", "100", "200", "300", "400"]
                )
                self.assertEqual(config.motors, 1 << index)
                self.assertEqual(config.data_set, 1 << bit)
        config = build_config(1, [True] * 5, ["Torque", "65535", "0", "10", "200"])
        self.assertEqual((config.mode, config.max_speed, config.jerk_slope), (2, 65535, 10))

    def test_validation_and_omitted_values(self):
        build_config(0, [True, False, False, False, False], ["Position", "invalid", "", "", ""])
        for value in ("-1", "65536", "1.5", ""):
            with self.assertRaises(ValueError):
                build_config(
                    0, [False, True, False, False, False], ["Position", value, "0", "0", "0"]
                )
        with self.assertRaises(ValueError):
            build_config(0, [False] * 5, ["Position", "0", "0", "0", "0"])

    def test_send_once_and_confirmation(self):
        device, requests, events = Mock(), queue.Queue(), []
        future = Future()
        device.configure_ext_motors.return_value = future
        config = build_config(1, [True] * 5, ["Speed", "1", "2", "3", "4"])
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
