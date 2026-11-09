import threading
import unittest
from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import Mock

from app import Monitor
from motor_control import ControlSender

from sbgc32 import ConfirmationStatus, ExternalMotorAction, ExternalMotorControl
from sbgc32.modules.control import control_ext_motors, ext_motors_action


def completed(value=None):
    future = Future()
    future.set_result(value)
    return future


class ControlTests(unittest.TestCase):
    def test_cadence_latest_values_and_no_backlog(self):
        sender, device, events = ControlSender(), Mock(), []
        future = Future()
        device.control_ext_motors.return_value = future
        sender.tick(device, 0, events.append)
        device.control_ext_motors.assert_not_called()
        sender.configure(True, 1, (100, -200))
        sender.tick(device, 0, events.append)
        device.control_ext_motors.assert_called_once_with((ExternalMotorControl(100),), 1)
        sender.tick(device, 1, events.append)
        self.assertEqual(device.control_ext_motors.call_count, 1)
        future.set_result(None)
        sender.configure(True, 3, (0, -200))
        sender.tick(device, 1.01, events.append)
        device.control_ext_motors.assert_called_with(
            (ExternalMotorControl(0), ExternalMotorControl(-200)), 3
        )
        sender.tick(device, 1.04, events.append)
        self.assertEqual(device.control_ext_motors.call_count, 2)
        sender.tick(device, 1.061, events.append)
        self.assertEqual(device.control_ext_motors.call_count, 3)
        sender.configure(False, 3, (0, -200))
        sender.tick(device, 2, events.append)
        self.assertEqual(device.control_ext_motors.call_count, 3)
        device.ext_motors_action.assert_not_called()

    def test_stop_waits_for_last_transmission_and_preserves_targets(self):
        for mask in (1, 2, 3):
            with self.subTest(mask=mask):
                sender, device, events = ControlSender(), Mock(), []
                transmission, confirmation = Future(), Future()
                device.control_ext_motors.return_value = transmission
                device.ext_motors_action.return_value = confirmation
                sender.configure(True, mask, (100, -200))
                sender.tick(device, 0, events.append)
                self.assertTrue(sender.request_stop())
                self.assertFalse(sender.request_stop())
                sender.configure(True, 3 ^ mask, (300, 400))
                sender.tick(device, 1, events.append)
                device.ext_motors_action.assert_not_called()
                transmission.set_result(None)
                sender.tick(device, 2, events.append)
                device.ext_motors_action.assert_called_once_with(
                    mask, ExternalMotorAction.OFF_SAFE, need_confirmation=True, timeout=1.0
                )
                sender.tick(device, 3, events.append)
                self.assertEqual(device.control_ext_motors.call_count, 1)
                confirmation.set_result(SimpleNamespace(status=ConfirmationStatus.RECEIVED))
                sender.tick(device, 4, events.append)
                sender.tick(device, 5, events.append)
                self.assertEqual(events[-1][0], "control_stopped")
                self.assertFalse(sender.running)
                self.assertEqual(device.ext_motors_action.call_count, 1)
                self.assertEqual(device.control_ext_motors.call_count, 1)
                sender.configure(True, mask, (0, 0))
                sender.tick(device, 6, events.append)
                self.assertEqual(device.control_ext_motors.call_count, 2)

    def test_stop_before_first_tick_sends_no_setpoint(self):
        sender, device = ControlSender(), Mock()
        sender.configure(True, 2, (0, 100))
        self.assertTrue(sender.request_stop())
        sender.tick(device, 0, lambda event: None)
        device.control_ext_motors.assert_not_called()
        device.ext_motors_action.assert_called_once_with(
            2, ExternalMotorAction.OFF_SAFE, need_confirmation=True, timeout=1.0
        )

    def test_stop_failure_reports_uncertain_motor_state_without_retry(self):
        for failure in ("timeout", "rejected", "missing", "disconnected"):
            with self.subTest(failure=failure):
                sender, device, events = ControlSender(), Mock(), []
                future = Future()
                if failure == "disconnected":
                    device.ext_motors_action.side_effect = OSError("Disconnected")
                else:
                    device.ext_motors_action.return_value = future
                sender.configure(True, 1, (0, 0))
                sender.request_stop()
                sender.tick(device, 0, events.append)
                if failure == "timeout":
                    future.set_exception(TimeoutError("No reply"))
                elif failure == "rejected":
                    future.set_result(SimpleNamespace(status=ConfirmationStatus.ERROR))
                elif failure == "missing":
                    future.set_result(None)
                sender.tick(device, 1, events.append)
                sender.tick(device, 2, events.append)
                self.assertEqual(events[-1][0], "control_stop_error")
                self.assertIn("may still be enabled", events[-1][1])
                self.assertEqual(device.ext_motors_action.call_count, 1)
                device.control_ext_motors.assert_not_called()
                self.assertFalse(sender.running)
                self.assertEqual(sender.stop_mask, 0)

    def test_failed_last_setpoint_does_not_skip_requested_stop(self):
        sender, device = ControlSender(), Mock()
        future = Future()
        device.control_ext_motors.return_value = future
        sender.configure(True, 1, (0, 0))
        sender.tick(device, 0, lambda event: None)
        sender.request_stop()
        future.set_exception(OSError("Write failed"))
        with self.assertLogs("motor_control", level="WARNING"):
            sender.tick(device, 1, lambda event: None)
        device.ext_motors_action.assert_called_once()

    def test_transport_failure_stops_sending(self):
        sender, device, events = ControlSender(), Mock(), []
        device.control_ext_motors.side_effect = OSError("Disconnected")
        sender.configure(True, 1, (0, 0))
        sender.tick(device, 0, events.append)
        sender.tick(device, 1, events.append)
        self.assertFalse(sender.running)
        self.assertEqual(device.control_ext_motors.call_count, 1)
        self.assertEqual(events[0][0], "control_error")

    def test_button_requests_motor_stop_and_blocks_second_click(self):
        sender = ControlSender()
        sender.configure(True, 3, (100, -200))
        monitor = SimpleNamespace(
            connected=True,
            stop=threading.Event(),
            control_stopping=False,
            control_running=True,
            control_sender=sender,
            update_control=Mock(),
            update_action_buttons=Mock(),
        )
        Monitor.toggle_control(monitor)
        self.assertFalse(monitor.control_running)
        self.assertTrue(monitor.control_stopping)
        self.assertEqual(sender.stop_mask, 3)
        Monitor.toggle_control(monitor)
        monitor.update_control.assert_called_once()

    def test_real_library_packets_for_distinct_targets_then_safe_stop(self):
        class Device:
            control_ext_motors = control_ext_motors
            ext_motors_action = ext_motors_action

            def __init__(self):
                self.packets = []

            def send_raw(self, command, payload, **kwargs):
                self.packets.append((command, payload))
                return completed()

            def request_raw(self, command, payload, **kwargs):
                self.packets.append((command, payload))
                return completed(SimpleNamespace(status=ConfirmationStatus.RECEIVED))

        sender, device, events = ControlSender(), Device(), []
        sender.configure(True, 3, (-1, 123))
        sender.tick(device, 0, events.append)
        sender.request_stop()
        sender.tick(device, 1, events.append)
        sender.tick(device, 2, events.append)
        self.assertEqual(
            device.packets,
            [
                (129, bytes.fromhex("03 00 ff ff 7b 00")),
                (128, bytes.fromhex("83 03")),
            ],
        )
        self.assertEqual(events[-1][0], "control_stopped")


if __name__ == "__main__":
    unittest.main()
