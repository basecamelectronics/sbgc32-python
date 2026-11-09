import queue
import unittest
from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import Mock

from motor_actions import ACTIONS, ActionRunner, ConfirmationStatus


class ActionTests(unittest.TestCase):
    def test_all_actions_and_masks_once(self):
        self.assertEqual([int(action) for _, action in ACTIONS], list(range(1, 7)))
        for mask in (1, 2, 3):
            for label, action in ACTIONS:
                device = Mock()
                future = Future()
                device.ext_motors_action.return_value = future
                requests, events = queue.Queue(), []
                runner = ActionRunner(device, requests, events.append)
                runner.tick()
                device.ext_motors_action.assert_not_called()
                requests.put((mask, action, label))
                runner.tick()
                runner.tick()
                device.ext_motors_action.assert_called_once_with(
                    mask, action, need_confirmation=True, timeout=1.0
                )
                future.set_result(SimpleNamespace(status=ConfirmationStatus.RECEIVED))
                runner.tick()
                runner.tick()
                self.assertEqual(len(events), 1)
                self.assertIn("confirmed", events[0][1])
                self.assertEqual(device.ext_motors_action.call_count, 1)

    def test_timeout_and_rejection_are_not_retried(self):
        for timeout in (True, False):
            future = Future()
            device = Mock()
            device.ext_motors_action.return_value = future
            requests, events = queue.Queue(), []
            requests.put((1, ACTIONS[0][1], "Off"))
            runner = ActionRunner(device, requests, events.append)
            runner.tick()
            if timeout:
                future.set_exception(TimeoutError("No confirmation"))
            else:
                future.set_result(SimpleNamespace(status=ConfirmationStatus.ERROR, error_code=1))
            runner.tick()
            runner.tick()
            self.assertIn("no automatic retry", events[0][1])
            self.assertEqual(device.ext_motors_action.call_count, 1)


if __name__ == "__main__":
    unittest.main()
