"""External motor wire-format regression tests; no serial port is opened."""

import struct
from concurrent.futures import Future

import pytest

from sbgc32 import ExternalMotorControl
from sbgc32.modules.control import control_ext_motors
from sbgc32.protocol import WireFrame
from sbgc32.types import ConfirmationStatus


class Capture:
    def __init__(self):
        self.calls = []

    def send_raw(self, command, payload, **kwargs):
        self.calls.append((command, payload, kwargs))
        result = Future()
        result.set_result(None)
        return result

    def request_raw(self, command, payload, **kwargs):
        self.calls.append((command, payload, kwargs))
        result = Future()
        result.set_result(kwargs['decoder'](WireFrame(2, 67, bytes((command,)))))
        return result


@pytest.mark.parametrize('mask', range(1, 128))
@pytest.mark.parametrize('confirm', [False, True])
def test_one_record_per_selected_motor_and_confirmation_bit(mask, confirm):
    device = Capture()
    reply = control_ext_motors(
        device, ExternalMotorControl(100), mask, need_confirmation=confirm, timeout=0.25,
    ).result()
    expected = bytes((mask | (0x80 if confirm else 0), 0))
    expected += bytes.fromhex('64 00') * mask.bit_count()
    assert device.calls[0][:2] == (129, expected)
    assert device.calls[0][2]['route'] == 'control'
    if confirm:
        assert reply.status == ConfirmationStatus.RECEIVED
        assert reply.command_id == 129
        assert device.calls[0][2]['timeout'] == 0.25
    else:
        assert reply is None


@pytest.mark.parametrize('data_set,record_format', [
    (0, '<h'), (1, '<i'), (2, '<hh'), (3, '<ih'), (4, '<hi'), (5, '<ii'),
])
def test_individual_values_follow_selected_motor_order_and_format(data_set, record_format):
    device = Capture()
    setpoint_bits = 32 if data_set & 1 else 16
    param_bits = 16 if data_set & 2 else 32
    values = (
        ExternalMotorControl(-(1 << (setpoint_bits - 1)), -(1 << (param_bits - 1))),
        ExternalMotorControl((1 << (setpoint_bits - 1)) - 1, (1 << (param_bits - 1)) - 1),
        ExternalMotorControl(-123, 456),
    )
    # Non-contiguous motor IDs 1, 4 and 7 must not introduce empty records.
    control_ext_motors(device, values, 0x49, data_set)
    expected = bytes((0x49, data_set))
    for value in values:
        args = (value.setpoint, value.param1) if data_set & 6 else (value.setpoint,)
        expected += struct.pack(record_format, *args)
    assert device.calls[0][:2] == (129, expected)


@pytest.mark.parametrize('control,mask,data_set', [
    (ExternalMotorControl(0), 0, 0),
    (ExternalMotorControl(0), 128, 0),
    (ExternalMotorControl(0), -1, 0),
    (ExternalMotorControl(0), 1, 6),
    (ExternalMotorControl(0), 1, 7),
    (ExternalMotorControl(0), 1, 8),
    (ExternalMotorControl(32768), 1, 0),
    (ExternalMotorControl(-32769), 1, 0),
    (ExternalMotorControl(2147483648), 1, 1),
    (ExternalMotorControl(-2147483649), 1, 1),
    (ExternalMotorControl(0, 32768), 1, 2),
    (ExternalMotorControl(0, -32769), 1, 2),
    (ExternalMotorControl(0, 2147483648), 1, 4),
    (ExternalMotorControl(0, -2147483649), 1, 4),
    (ExternalMotorControl(1.5), 1, 0),
    ((ExternalMotorControl(0),), 3, 0),
    ((ExternalMotorControl(0), ExternalMotorControl(1)), 1, 0),
    ((ExternalMotorControl(0), ExternalMotorControl(32768)), 3, 0),
    ((), 1, 0),
    ((None,), 1, 0),
    (None, 1, 0),
])
def test_invalid_input_is_rejected_before_transmission(control, mask, data_set):
    device = Capture()
    with pytest.raises((TypeError, ValueError)):
        control_ext_motors(device, control, mask, data_set)
    assert device.calls == []


def test_confirmation_requires_boolean():
    device = Capture()
    with pytest.raises(TypeError):
        control_ext_motors(device, ExternalMotorControl(0), 1, need_confirmation=1)
    assert device.calls == []
