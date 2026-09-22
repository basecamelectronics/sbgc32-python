"""Asynchronous gimbal-control and virtual-channel commands.

This module only encodes SerialAPI packets.  Text rendering belongs in
``sbgc32.format``.
"""

from __future__ import annotations

import struct
from concurrent.futures import Future
from math import isfinite
from typing import TYPE_CHECKING

from ..commands import Command
from ..types import (
    CommandConfirmation,
    ConfirmationStatus,
    ControlAxis,
    ControlAxisConfig,
    ControlConfig,
    ControlConfigFlag,
    ControlExt,
    ControlExtAxis,
    ControlFlag,
    ControlMode,
    ControlQuat,
    ControlQuatConfig,
    ControlQuatConfigParameter,
    ControlQuatFlag,
    ControlQuatMode,
    ExternalMotorAction,
    ExternalMotorControl,
    ExternalMotorParameter,
    ExternalMotorsControlConfig,
    ExternalMotorsControlConfigParameter,
)
from .realtime import decode_confirmation

if TYPE_CHECKING:
    from ..device import SimpleBGC


_API_VIRTUAL_CHANNEL_COUNT = 32
_API_VIRTUAL_UNDEFINED = -10000
_API_VIRTUAL_MIN = -500
_API_VIRTUAL_MAX = 500
_EXT_MOTOR_NEED_CONFIRM = 1 << 7


def validate_uint(value: object, name: str, maximum: int) -> int:
    """Validate an unsigned protocol field.

    Kept public for the remaining legacy modules while they are migrated.
    """

    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(f"{name} must be an integer in range 0..{maximum}")
    return value


def validate_int_tuple(values: object, name: str, length: int, maximum: int) -> tuple[int, ...]:
    """Validate a fixed-size tuple of unsigned controller values."""

    if not isinstance(values, tuple) or len(values) != length:
        raise ValueError(f"{name} must be a tuple with {length} entries")
    return tuple(validate_uint(value, name, maximum) for value in values)


def _validate_int(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in range {minimum}..{maximum}")
    return value


def _validate_tuple(
    values: object, name: str, length: int, minimum: int, maximum: int
) -> tuple[int, ...]:
    if not isinstance(values, tuple) or len(values) != length:
        raise ValueError(f"{name} must be a tuple with {length} entries")
    return tuple(_validate_int(value, name, minimum, maximum) for value in values)


def control_speed_to_units(speed_degrees_per_second: float, mode: int) -> int:
    """Convert degrees/s to the signed 16-bit ``CMD_CONTROL`` value."""

    scale = 1000.0 if mode & int(ControlFlag.HIGH_RES_SPEED) else 1 / 0.1220740379
    value = round(speed_degrees_per_second * scale)
    if not -0x8000 <= value <= 0x7FFF:
        raise ValueError("axis speed is outside the range supported by CMD_CONTROL")
    return value


def control_angle_to_units(angle_degrees: float, mode: int) -> int:
    """Convert an angle in degrees to the signed 16-bit protocol value."""

    control_mode = ControlMode(mode & 0x0F)
    if control_mode in (ControlMode.RC, ControlMode.RC_HIGH_RES):
        if not float(angle_degrees).is_integer():
            raise ValueError("RC mode requires an integral raw RC value in angle")
        value = int(angle_degrees)
    else:
        value = round(angle_degrees * 16384.0 / 360.0)
    if not -0x8000 <= value <= 0x7FFF:
        raise ValueError("axis angle is outside the range supported by CMD_CONTROL")
    return value


def make_confirmation(confirmation: object) -> CommandConfirmation | None:
    """Convert a legacy native confirmation object during the transition."""

    if confirmation is None:
        return None
    return CommandConfirmation(
        command_id=confirmation.command_id,
        status=ConfirmationStatus(confirmation.status),
        command_data=confirmation.command_data,
        error_code=confirmation.error_code,
        error_data=bytes(confirmation.error_data),
    )


def _confirmation(
    self: SimpleBGC,
    command: Command,
    payload: bytes,
    need_confirmation: bool,
    timeout: float | None,
) -> Future[CommandConfirmation | None]:
    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")
    if need_confirmation:
        return self.request_raw(
            int(command), payload, timeout=timeout, route="control", decoder=decode_confirmation
        )
    return self.send_raw(int(command), payload, route="control")


def control(
    self: SimpleBGC,
    axes: tuple[ControlAxis, ControlAxis, ControlAxis],
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Queue one 15-byte ``CMD_CONTROL`` command for roll, pitch and yaw."""

    if len(axes) != 3:
        raise ValueError("axes must contain exactly roll, pitch, and yaw")
    modes: list[int] = []
    speeds: list[int] = []
    angles: list[int] = []
    for axis in axes:
        if not isinstance(axis, ControlAxis):
            raise TypeError("each axis must be a ControlAxis")
        mode = validate_uint(int(axis.mode), "axis mode", 0xFF)
        try:
            ControlMode(mode & 0x0F)
        except ValueError as error:
            raise ValueError("axis mode has an unknown control mode") from error
        if not isfinite(axis.speed) or not isfinite(axis.angle):
            raise ValueError("axis speed and angle must be finite")
        modes.append(mode)
        speeds.append(control_speed_to_units(axis.speed, mode))
        angles.append(control_angle_to_units(axis.angle, mode))
    return _confirmation(
        self,
        Command.CMD_CONTROL,
        struct.pack(
            "<3B6h",
            *modes,
            *(value for speed, angle in zip(speeds, angles) for value in (speed, angle)),
        ),
        need_confirmation,
        timeout,
    )


def configure_control(
    self: SimpleBGC,
    config: ControlConfig | None = None,
    *,
    confirm_control: bool | None = None,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Apply ``CMD_CONTROL_CONFIG`` rules."""

    if config is None:
        config = ControlConfig()
    if not isinstance(config, ControlConfig):
        raise TypeError("config must be a ControlConfig")
    flags = validate_uint(int(config.flags), "flags", 0xFFFF)
    if confirm_control is not None:
        if type(confirm_control) is not bool:
            raise TypeError("confirm_control must be bool or None")
        flags = (
            flags & ~int(ControlConfigFlag.NO_CONFIRM)
            if confirm_control
            else flags | int(ControlConfigFlag.NO_CONFIRM)
        )
    priorities = validate_int_tuple(config.channel_priorities, "channel_priorities", 5, 0xFF)
    if len(config.axes) != 3 or any(
        not isinstance(axis, ControlAxisConfig) for axis in config.axes
    ):
        raise TypeError("config.axes must contain three ControlAxisConfig values")
    payload = bytearray(
        struct.pack("<H5B", validate_uint(config.timeout_ms, "timeout_ms", 0xFFFF), *priorities)
    )
    for axis in config.axes:
        payload.extend(
            struct.pack(
                "<3BHBB",
                validate_uint(axis.angle_lpf, "angle_lpf", 0xFF),
                validate_uint(axis.speed_lpf, "speed_lpf", 0xFF),
                validate_uint(axis.rc_lpf, "rc_lpf", 0xFF),
                validate_uint(axis.acceleration_limit, "acceleration_limit", 0xFFFF),
                validate_uint(axis.jerk_slope, "jerk_slope", 0xFF),
                0,
            )
        )
    payload.extend(
        struct.pack(
            "<BHB9s",
            validate_uint(config.rc_expo_rate, "rc_expo_rate", 0xFF),
            flags,
            validate_uint(config.euler_order, "euler_order", 0xFF),
            bytes(9),
        )
    )
    return _confirmation(
        self, Command.CMD_CONTROL_CONFIG, bytes(payload), need_confirmation, timeout
    )


def control_config(
    self: SimpleBGC,
    config: ControlConfig | None = None,
    *,
    confirm_control: bool | None = None,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Alias for :func:`configure_control`."""

    return configure_control(
        self,
        config,
        confirm_control=confirm_control,
        need_confirmation=need_confirmation,
        timeout=timeout,
    )


def _virtual_channels(values: object, minimum: int, maximum: int, undefined: int) -> bytes:
    try:
        requested = tuple(values)
    except TypeError as error:
        raise TypeError("values must be an iterable of channel values or None") from error
    if not 1 <= len(requested) <= _API_VIRTUAL_CHANNEL_COUNT:
        raise ValueError("values must contain from 1 to 32 entries")
    encoded = tuple(
        undefined if value is None else _validate_int(value, "channel value", minimum, maximum)
        for value in requested
    )
    return struct.pack(f"<{len(encoded)}h", *encoded)


def set_api_virtual_channels(self: SimpleBGC, values: object) -> Future[None]:
    """Set up to 32 standard-resolution virtual RC channels."""

    return self.send_raw(
        int(Command.CMD_API_VIRT_CH_CONTROL),
        _virtual_channels(values, _API_VIRTUAL_MIN, _API_VIRTUAL_MAX, _API_VIRTUAL_UNDEFINED),
        route="control",
    )


def control_ext(self: SimpleBGC, control: ControlExt) -> Future[None]:
    """Queue variable-length ``CMD_CONTROL_EXT`` data."""

    if not isinstance(control, ControlExt):
        raise TypeError("control must be a ControlExt")
    data_set = _validate_int(int(control.data_set), "data_set", 1, 0xFFFF)
    if len(control.axes) != 3 or any(not isinstance(axis, ControlExtAxis) for axis in control.axes):
        raise TypeError("control.axes must contain three ControlExtAxis values")
    payload = bytearray(struct.pack("<H", data_set))
    for index, axis in enumerate(control.axes):
        bits = (data_set >> (index * 5)) & 0x1F
        if not bits:
            continue
        mode = validate_uint(int(axis.mode), "axis mode", 0xFF)
        try:
            ControlMode(mode & 0x0F)
        except ValueError as error:
            raise ValueError("axis mode has an unknown control mode") from error
        payload.extend((mode, validate_uint(int(axis.flags), "axis flags", 0xFF)))
        if bits & 0x01:
            payload.extend(
                struct.pack("<h", _validate_int(axis.speed, "axis speed", -0x8000, 0x7FFF))
            )
        elif bits & 0x08:
            payload.extend(
                struct.pack("<i", _validate_int(axis.speed, "axis speed", -0x80000000, 0x7FFFFFFF))
            )
        if bits & 0x02:
            payload.extend(
                struct.pack("<h", _validate_int(axis.angle, "axis angle", -0x8000, 0x7FFF))
            )
        elif bits & 0x04:
            payload.extend(
                struct.pack("<i", _validate_int(axis.angle, "axis angle", -0x80000000, 0x7FFFFFFF))
            )
    return self.send_raw(int(Command.CMD_CONTROL_EXT), bytes(payload), route="control")


def control_quat(
    self: SimpleBGC,
    control: ControlQuat,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Control orientation and/or speed using a target quaternion."""

    if not isinstance(control, ControlQuat):
        raise TypeError("control must be a ControlQuat")
    try:
        mode = ControlQuatMode(control.mode)
    except ValueError as error:
        raise ValueError("mode must be a supported quaternion control mode") from error
    flags = validate_uint(int(control.flags), "flags", 0xFF)
    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")
    if need_confirmation:
        flags |= int(ControlQuatFlag.NEED_CONFIRM)
    if not isinstance(control.attitude, tuple) or len(control.attitude) != 4:
        raise ValueError("attitude must have four values")
    if not isinstance(control.speed, tuple) or len(control.speed) != 3:
        raise ValueError("speed must have three values")
    values = (*control.attitude, *control.speed)
    if any(type(value) not in (int, float) or not isfinite(value) for value in values):
        raise ValueError("quaternion control values must be finite")
    payload = bytearray((int(mode), flags))
    if mode in (ControlQuatMode.ATTITUDE, ControlQuatMode.SPEED_ATTITUDE):
        payload.extend(struct.pack("<4f", *control.attitude))
    if mode in (
        ControlQuatMode.SPEED,
        ControlQuatMode.SPEED_ATTITUDE,
        ControlQuatMode.SPEED_LIMITED,
    ):
        payload.extend(struct.pack("<3f", *control.speed))
    return _confirmation(self, Command.CMD_CONTROL_QUAT, bytes(payload), need_confirmation, timeout)


def configure_control_quat(
    self: SimpleBGC,
    config: ControlQuatConfig,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Configure quaternion-control filters and motion profile."""

    if not isinstance(config, ControlQuatConfig):
        raise TypeError("config must be a ControlQuatConfig")
    data_set = _validate_int(int(config.data_set), "data_set", 1, 0xFFFF)
    payload = bytearray(struct.pack("<H", data_set))
    selected = ControlQuatConfigParameter(data_set)
    if selected & ControlQuatConfigParameter.MAX_SPEED:
        payload.extend(
            struct.pack("<3H", *_validate_tuple(config.max_speed, "max_speed", 3, 0, 0xFFFF))
        )
    if selected & ControlQuatConfigParameter.ACCELERATION_LIMIT:
        payload.extend(
            struct.pack(
                "<3H",
                *_validate_tuple(config.acceleration_limit, "acceleration_limit", 3, 0, 0xFFFF),
            )
        )
    if selected & ControlQuatConfigParameter.JERK_SLOPE:
        payload.extend(
            struct.pack("<3H", *_validate_tuple(config.jerk_slope, "jerk_slope", 3, 0, 0xFFFF))
        )
    if selected & ControlQuatConfigParameter.FLAGS:
        payload.extend(struct.pack("<H", validate_uint(int(config.flags), "flags", 0xFFFF)))
    if selected & ControlQuatConfigParameter.ATTITUDE_LPF_FREQUENCY:
        payload.append(validate_uint(config.attitude_lpf_frequency, "attitude_lpf_frequency", 0xFF))
    if selected & ControlQuatConfigParameter.SPEED_LPF_FREQUENCY:
        payload.append(validate_uint(config.speed_lpf_frequency, "speed_lpf_frequency", 0xFF))
    return _confirmation(
        self, Command.CMD_CONTROL_QUAT_CONFIG, bytes(payload), need_confirmation, timeout
    )


def ext_motors_action(
    self: SimpleBGC,
    motors: int,
    action: ExternalMotorAction | int,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Run an action on selected external motors."""

    selected = _validate_int(int(motors), "motors", 1, 0x7F)
    action_value = _validate_int(int(action), "action", 1, 6)
    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")
    if need_confirmation:
        selected |= _EXT_MOTOR_NEED_CONFIRM
    return _confirmation(
        self,
        Command.CMD_EXT_MOTORS_ACTION,
        bytes((selected, action_value)),
        need_confirmation,
        timeout,
    )


def control_ext_motors(
    self: SimpleBGC,
    control: ExternalMotorControl,
    motors: int,
    data_set: ExternalMotorParameter | int = 0,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Set extra-motor setpoint data for the three protocol motor slots."""

    if not isinstance(control, ExternalMotorControl):
        raise TypeError("control must be an ExternalMotorControl")
    selected = _validate_int(int(motors), "motors", 1, 0x7F)
    parameters = _validate_int(int(data_set), "data_set", 0, 0x07)
    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")
    if need_confirmation:
        selected |= _EXT_MOTOR_NEED_CONFIRM
    setpoint_size = 4 if parameters & int(ExternalMotorParameter.SETPOINT_32BIT) else 2
    setpoint = _validate_int(
        control.setpoint,
        "setpoint",
        -(1 << (setpoint_size * 8 - 1)),
        (1 << (setpoint_size * 8 - 1)) - 1,
    )
    param_size = 2 if parameters & int(ExternalMotorParameter.PARAM1_16BIT) else 4
    param1 = _validate_int(
        control.param1, "param1", -(1 << (param_size * 8 - 1)), (1 << (param_size * 8 - 1)) - 1
    )
    payload = bytearray((selected, parameters))
    for _ in range(3):
        payload.extend(struct.pack("<i" if setpoint_size == 4 else "<h", setpoint))
        if parameters & int(ExternalMotorParameter.PARAM1_16BIT):
            payload.extend(struct.pack("<h", param1))
        elif parameters & int(ExternalMotorParameter.PARAM1_32BIT):
            payload.extend(struct.pack("<i", param1))
    return _confirmation(
        self, Command.CMD_EXT_MOTORS_CONTROL, bytes(payload), need_confirmation, timeout
    )


def configure_ext_motors(
    self: SimpleBGC,
    config: ExternalMotorsControlConfig,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Configure run-time parameters for selected external motors."""

    if not isinstance(config, ExternalMotorsControlConfig):
        raise TypeError("config must be an ExternalMotorsControlConfig")
    selected = _validate_int(int(config.motors), "motors", 1, 0x7F)
    data_set = _validate_int(int(config.data_set), "data_set", 1, 0x1F)
    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")
    if need_confirmation:
        selected |= _EXT_MOTOR_NEED_CONFIRM
    parameters = ExternalMotorsControlConfigParameter(data_set)
    payload = bytearray(struct.pack("<BH", selected, data_set))
    if parameters & ExternalMotorsControlConfigParameter.MODE:
        payload.append(_validate_int(int(config.mode), "mode", 0, 2))
    if parameters & ExternalMotorsControlConfigParameter.MAX_SPEED:
        payload.extend(struct.pack("<H", validate_uint(config.max_speed, "max_speed", 0xFFFF)))
    if parameters & ExternalMotorsControlConfigParameter.MAX_ACCELERATION:
        payload.extend(
            struct.pack("<H", validate_uint(config.max_acceleration, "max_acceleration", 0xFFFF))
        )
    if parameters & ExternalMotorsControlConfigParameter.JERK_SLOPE:
        payload.extend(struct.pack("<H", validate_uint(config.jerk_slope, "jerk_slope", 0xFFFF)))
    if parameters & ExternalMotorsControlConfigParameter.MAX_TORQUE:
        payload.extend(struct.pack("<H", validate_uint(config.max_torque, "max_torque", 0xFFFF)))
    return _confirmation(
        self,
        Command.CMD_EXT_MOTORS_CONTROL_CONFIG,
        bytes(payload),
        need_confirmation,
        timeout,
    )


def set_api_virtual_channels_hr(self: SimpleBGC, values: object) -> Future[None]:
    """Set up to 32 high-resolution virtual RC channels."""

    return self.send_raw(
        int(Command.CMD_API_VIRT_CH_HIGH_RES),
        _virtual_channels(values, -16384, 16384, -32768),
        route="control",
    )
