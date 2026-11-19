import struct
import unittest
from unittest.mock import Mock

from connection import DiagnosticSimpleBGC
from motor_config import build_config
from motor_protocol import ExternalMotorsControlConfig
from motor_state import DATA_SET, RESULT_SIZE, format_state
from motor_telemetry import STATE, decode_state

from sbgc32.protocol import WireFrame


class RevisedProtocolTests(unittest.TestCase):
    def test_logged_revised_reply_decodes_without_shifted_fields(self):
        # Captured reply included in the supplied archive's regression test.
        fields = bytes.fromhex(
            "00 f1 0a 04 0b 6c 00 00 00 6b 84 03 00 00 00 00 00 "
            "5d f5 01 ca 40 57 fd ff 5a 80 f2 ff 05 00 80 11 dc 05 "
            "87 03 c8 00 ff ff 6a 00 44 2f 1a"
        )
        with self.assertRaises(ValueError):
            decode_state(fields)
        payload = fields + bytes([32])
        values = decode_state(payload)
        self.assertEqual((DATA_SET, RESULT_SIZE, STATE.size), (0x1FFFFF, 51, 47))
        self.assertAlmostEqual(values[12], 4480 / 3)
        self.assertEqual(values[13:], (500, 301, 200, 100, 106, 12.1, 26, 32))
        self.assertIn("Default speed: 1493.33 rpm", format_state(payload))

    def test_configuration_bits_and_field_order(self):
        config = build_config(1, [True] * 6, ["Torque", "10", "20", "30", "40", "50"])
        self.assertEqual(
            config.encode(need_confirmation=True),
            struct.pack("<BHBHHHHH", 0x82, 0x3F, 2, 30, 60, 90, 40, 50),
        )
        for bit, name in enumerate(
            ("default_speed", "max_speed", "max_acceleration", "jerk_slope", "max_torque"), 1
        ):
            partial = ExternalMotorsControlConfig(1, 1 << bit, **{name: 0x1234})
            self.assertEqual(partial.encode(), struct.pack("<BHH", 1, 1 << bit, 0x1234))

    def test_restore_rc_and_confirmation_route(self):
        for index in (0, 1):
            config = build_config(index, [True] + [False] * 5, ["Restore RC (255)"] + [""] * 5)
            device = Mock()
            result = DiagnosticSimpleBGC.configure_ext_motors(
                device, config, need_confirmation=True, timeout=0.5
            )
            self.assertIs(result, device.request_raw.return_value)
            args, kwargs = device.request_raw.call_args
            self.assertEqual(args, (130, bytes([0x80 | (1 << index), 1, 0, 255])))
            self.assertEqual((kwargs["route"], kwargs["timeout"]), ("control", 0.5))
            reply = kwargs["decoder"](WireFrame(2, 67, bytes([130])))
            self.assertEqual(reply.command_id, 130)
            DiagnosticSimpleBGC.configure_ext_motors(device, config)
            device.send_raw.assert_called_once_with(130, config.encode(), route="control")

    def test_invalid_configuration_is_rejected_before_transmission(self):
        for config in (
            ExternalMotorsControlConfig(0, 1),
            ExternalMotorsControlConfig(1, 0x40),
            ExternalMotorsControlConfig(1, 1, mode=3),
            ExternalMotorsControlConfig(1, 2, default_speed=65536),
        ):
            device = Mock()
            with self.assertRaises(ValueError):
                DiagnosticSimpleBGC.configure_ext_motors(device, config)
            device.send_raw.assert_not_called()
            device.request_raw.assert_not_called()
