"""CMD_CONTROL and CMD_CONTROL_CONFIG implementation details."""

from __future__ import annotations

import ctypes
from math import isfinite

from ._serial_api_library import (
    NativeControlAxisConfig,
    NativeControlConfig,
    NativeControlExt,
    NativeControlExtAxis,
    NativeControlQuat,
    NativeControlQuatConfig,
    NativeExternalMotorControl,
    NativeExternalMotorsControlConfig,
)
from .types import (
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
    ControlQuatMode,
    ExternalMotorAction,
    ExternalMotorControl,
    ExternalMotorsControlConfig,
)


def validate_uint(value: object, name: str, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= maximum:
        raise ValueError(f"{name} must be an integer in range 0..{maximum}")
    return int(value)


def validate_int_tuple(values: object, name: str, length: int, maximum: int) -> tuple[int, ...]:
    if not isinstance(values, tuple) or len(values) != length:
        raise ValueError(f"{name} must be a tuple with {length} entries")
    return tuple(validate_uint(value, name, maximum) for value in values)


def control_speed_to_units(speed_degrees_per_second: float, mode: int) -> int:
    scale = 1000.0 if mode & int(ControlFlag.HIGH_RES_SPEED) else 1 / 0.1220740379
    value = round(speed_degrees_per_second * scale)
    if not -0x8000 <= value <= 0x7FFF:
        raise ValueError("axis speed is outside the range supported by CMD_CONTROL")
    return value


def control_angle_to_units(angle_degrees: float, mode: int) -> int:
    control_mode = ControlMode(mode & 0x0F)
    if control_mode in (ControlMode.RC, ControlMode.RC_HIGH_RES):
        if not angle_degrees.is_integer():
            raise ValueError("RC mode requires an integral raw RC value in angle")
        value = int(angle_degrees)
    else:
        value = round(angle_degrees * 16384.0 / 360.0)
    if not -0x8000 <= value <= 0x7FFF:
        raise ValueError("axis angle is outside the range supported by CMD_CONTROL")
    return value


def make_confirmation(confirmation: object) -> CommandConfirmation | None:
    if confirmation is None:
        return None
    return CommandConfirmation(
        command_id=confirmation.command_id,
        status=ConfirmationStatus(confirmation.status),
        command_data=confirmation.command_data,
        error_code=confirmation.error_code,
        error_data=bytes(confirmation.error_data),
    )


def control(
    self,
    axes: tuple[ControlAxis, ControlAxis, ControlAxis],
    *,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()
    if len(axes) != 3:
        raise ValueError("axes must contain exactly roll, pitch, and yaw")
    modes: list[int] = []
    speeds: list[int] = []
    angles: list[int] = []
    for axis in axes:
        if not isinstance(axis, ControlAxis):
            raise TypeError("each axis must be a ControlAxis")
        mode = int(axis.mode)
        if not 0 <= mode <= 0xFF:
            raise ValueError("axis mode must be in range 0..255")
        try:
            ControlMode(mode & 0x0F)
        except ValueError as error:
            raise ValueError("axis mode has an unknown control mode") from error
        if not isfinite(axis.speed):
            raise ValueError("axis speed must be finite")
        if not isfinite(axis.angle):
            raise ValueError("axis angle must be finite")
        modes.append(mode)
        speeds.append(control_speed_to_units(axis.speed, mode))
        angles.append(control_angle_to_units(axis.angle, mode))
    return make_confirmation(
        self._native.control(
            self._device,
            tuple(modes),
            tuple(speeds),
            tuple(angles),
            need_confirmation=need_confirmation,
        )
    )


def configure_control(
    self,
    config: ControlConfig | None = None,
    *,
    confirm_control: bool | None = None,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    """Apply CMD_CONTROL_CONFIG rules."""
    self._ensure_open()
    if config is None:
        config = ControlConfig()
    if not isinstance(config, ControlConfig):
        raise TypeError("config must be a ControlConfig")
    flags = validate_uint(config.flags, "flags", 0xFFFF)
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
        raise TypeError("config.axes must contain ControlAxisConfig for roll, pitch, and yaw")
    native_axes = (NativeControlAxisConfig * 3)(
        *(
            NativeControlAxisConfig(
                angle_lpf=validate_uint(axis.angle_lpf, "angle_lpf", 0xFF),
                speed_lpf=validate_uint(axis.speed_lpf, "speed_lpf", 0xFF),
                rc_lpf=validate_uint(axis.rc_lpf, "rc_lpf", 0xFF),
                acceleration_limit=validate_uint(
                    axis.acceleration_limit, "acceleration_limit", 0xFFFF
                ),
                jerk_slope=validate_uint(axis.jerk_slope, "jerk_slope", 0xFF),
            )
            for axis in config.axes
        )
    )
    native_config = NativeControlConfig(
        timeout_ms=validate_uint(config.timeout_ms, "timeout_ms", 0xFFFF),
        channel_priorities=(ctypes.c_uint8 * 5)(*priorities),
        axis=native_axes,
        rc_expo_rate=validate_uint(config.rc_expo_rate, "rc_expo_rate", 0xFF),
        flags=flags,
        euler_order=validate_uint(config.euler_order, "euler_order", 0xFF),
    )
    return make_confirmation(
        self._native.control_config(
            self._device, native_config, need_confirmation=need_confirmation
        )
    )


def control_config(
    self,
    config: ControlConfig | None = None,
    *,
    confirm_control: bool | None = None,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    """Alias for :func:`configure_control`."""
    return configure_control(
        self,
        config,
        confirm_control=confirm_control,
        need_confirmation=need_confirmation,
    )


_API_VIRTUAL_CHANNEL_COUNT = 32
_API_VIRTUAL_UNDEFINED = -10000
_API_VIRTUAL_MIN = -500
_API_VIRTUAL_MAX = 500


def set_api_virtual_channels(self, values: object) -> None:
    self._ensure_open()

    try:
        requested = tuple(values)
    except TypeError as error:
        raise TypeError("Values must be an iterable of channels values or None") from error

    if not 1 <= len(requested) <= _API_VIRTUAL_CHANNEL_COUNT:
        raise ValueError("Values must be in range from 1 to 32")

    native_values: list[int] = []

    for index, value in enumerate(requested, start=1):
        if value is None:
            native_values.append(_API_VIRTUAL_UNDEFINED)
        elif isinstance(value, int) and _API_VIRTUAL_MIN <= value <= _API_VIRTUAL_MAX:
            native_values.append(value)
        else:
            raise ValueError(
                f"Channel {index} must be in range {_API_VIRTUAL_MIN}...{_API_VIRTUAL_MAX} or None"
            )

    self._native.set_api_virtual_channels(self._device, tuple(native_values))


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


def control_ext(self, control: ControlExt) -> None:
    self._ensure_open()
    if not isinstance(control, ControlExt):
        raise TypeError("control must be a ControlExt")
    data_set = _validate_int(int(control.data_set), "data_set", 1, 0xFFFF)
    if len(control.axes) != 3 or any(not isinstance(axis, ControlExtAxis) for axis in control.axes):
        raise TypeError("control.axes must contain three ControlExtAxis values")
    axes = (NativeControlExtAxis * 3)(
        *(
            NativeControlExtAxis(
                mode=_validate_int(int(axis.mode), "axis mode", 0, 0xFF),
                flags=_validate_int(int(axis.flags), "axis flags", 0, 0xFF),
                speed=_validate_int(axis.speed, "axis speed", -0x80000000, 0x7FFFFFFF),
                angle=_validate_int(axis.angle, "axis angle", -0x80000000, 0x7FFFFFFF),
            )
            for axis in control.axes
        )
    )
    self._native.control_ext(self._device, NativeControlExt(data_set=data_set, axes=axes))


def control_quat(
    self, control: ControlQuat, *, need_confirmation: bool = False
) -> CommandConfirmation | None:
    self._ensure_open()
    if not isinstance(control, ControlQuat):
        raise TypeError("control must be a ControlQuat")
    mode = _validate_int(int(control.mode), "mode", 0, 0xFF)
    try:
        ControlQuatMode(mode)
    except ValueError as error:
        raise ValueError("mode must be a supported quaternion control mode") from error
    flags = _validate_int(int(control.flags), "flags", 0, 0xFF)
    if (
        not isinstance(control.attitude, tuple)
        or len(control.attitude) != 4
        or not isinstance(control.speed, tuple)
        or len(control.speed) != 3
    ):
        raise ValueError("attitude must have 4 values and speed must have 3 values")
    values = tuple(control.attitude) + tuple(control.speed)
    if any(type(value) not in (int, float) or not isfinite(value) for value in values):
        raise ValueError("quaternion control values must be finite")
    native = NativeControlQuat(
        mode=mode,
        flags=flags,
        attitude=(ctypes.c_float * 4)(*control.attitude),
        speed=(ctypes.c_float * 3)(*control.speed),
    )
    return make_confirmation(
        self._native.control_quat(self._device, native, need_confirmation=need_confirmation)
    )


def configure_control_quat(
    self, config: ControlQuatConfig, *, need_confirmation: bool = False
) -> CommandConfirmation | None:
    self._ensure_open()
    if not isinstance(config, ControlQuatConfig):
        raise TypeError("config must be a ControlQuatConfig")
    data_set = _validate_int(int(config.data_set), "data_set", 1, 0xFFFF)
    native = NativeControlQuatConfig(
        data_set=data_set,
        max_speed=(ctypes.c_uint16 * 3)(
            *_validate_tuple(config.max_speed, "max_speed", 3, 0, 0xFFFF)
        ),
        acceleration_limit=(ctypes.c_uint16 * 3)(
            *_validate_tuple(config.acceleration_limit, "acceleration_limit", 3, 0, 0xFFFF)
        ),
        jerk_slope=(ctypes.c_uint16 * 3)(
            *_validate_tuple(config.jerk_slope, "jerk_slope", 3, 0, 0xFFFF)
        ),
        flags=_validate_int(int(config.flags), "flags", 0, 0xFFFF),
        attitude_lpf_frequency=_validate_int(
            config.attitude_lpf_frequency, "attitude_lpf_frequency", 0, 0xFF
        ),
        speed_lpf_frequency=_validate_int(
            config.speed_lpf_frequency, "speed_lpf_frequency", 0, 0xFF
        ),
    )
    return make_confirmation(
        self._native.control_quat_config(self._device, native, need_confirmation=need_confirmation)
    )


def ext_motors_action(
    self,
    motors: int,
    action: ExternalMotorAction | int,
    *,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()
    motors = _validate_int(int(motors), "motors", 1, 0x7F)
    action = _validate_int(int(action), "action", 1, 6)
    return make_confirmation(
        self._native.ext_motors_action(
            self._device, motors, action, need_confirmation=need_confirmation
        )
    )


def control_ext_motors(
    self,
    control: ExternalMotorControl,
    motors: int,
    data_set: int = 0,
    *,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()
    if not isinstance(control, ExternalMotorControl):
        raise TypeError("control must be an ExternalMotorControl")
    native = NativeExternalMotorControl(
        setpoint=_validate_int(control.setpoint, "setpoint", -0x80000000, 0x7FFFFFFF),
        param1=_validate_int(control.param1, "param1", -0x80000000, 0x7FFFFFFF),
    )
    return make_confirmation(
        self._native.ext_motors_control(
            self._device,
            native,
            _validate_int(int(motors), "motors", 1, 0x7F),
            _validate_int(int(data_set), "data_set", 0, 7),
            need_confirmation=need_confirmation,
        )
    )


def configure_ext_motors(
    self, config: ExternalMotorsControlConfig, *, need_confirmation: bool = False
) -> CommandConfirmation | None:
    self._ensure_open()
    if not isinstance(config, ExternalMotorsControlConfig):
        raise TypeError("config must be an ExternalMotorsControlConfig")
    native = NativeExternalMotorsControlConfig(
        motors=_validate_int(int(config.motors), "motors", 1, 0x7F),
        data_set=_validate_int(int(config.data_set), "data_set", 1, 0x1F),
        mode=_validate_int(int(config.mode), "mode", 0, 2),
        max_speed=_validate_int(config.max_speed, "max_speed", 0, 0xFFFF),
        max_acceleration=_validate_int(config.max_acceleration, "max_acceleration", 0, 0xFFFF),
        jerk_slope=_validate_int(config.jerk_slope, "jerk_slope", 0, 0xFFFF),
        max_torque=_validate_int(config.max_torque, "max_torque", 0, 0xFFFF),
    )
    return make_confirmation(
        self._native.ext_motors_control_config(
            self._device, native, need_confirmation=need_confirmation
        )
    )


def set_api_virtual_channels_hr(self, values: object) -> None:
    self._ensure_open()
    try:
        requested = tuple(values)
    except TypeError as error:
        raise TypeError("values must be an iterable of channel values or None") from error
    if not 1 <= len(requested) <= _API_VIRTUAL_CHANNEL_COUNT:
        raise ValueError("values must contain from 1 to 32 entries")
    native_values = tuple(
        -32768 if value is None else _validate_int(value, "channel value", -16384, 16384)
        for value in requested
    )
    self._native.set_api_virtual_channels_hr(self._device, native_values)
