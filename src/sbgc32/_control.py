"""CMD_CONTROL and CMD_CONTROL_CONFIG implementation details."""

from __future__ import annotations

import ctypes
from math import isfinite

from .native import NativeControlAxisConfig, NativeControlConfig
from .types import (
    CommandConfirmation,
    ConfirmationStatus,
    ControlAxis,
    ControlAxisConfig,
    ControlConfig,
    ControlConfigFlag,
    ControlFlag,
    ControlMode,
)


def validate_uint(value: object, name: str, maximum: int) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= maximum
    ):
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


def control(self, axes: tuple[ControlAxis, ControlAxis, ControlAxis], *, need_confirmation: bool = False) -> CommandConfirmation | None:
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
    return make_confirmation(self._native.control(
        self._device, tuple(modes), tuple(speeds), tuple(angles),
        need_confirmation=need_confirmation,
    ))


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
        flags = flags & ~int(ControlConfigFlag.NO_CONFIRM) if confirm_control else flags | int(ControlConfigFlag.NO_CONFIRM)
    priorities = validate_int_tuple(config.channel_priorities, "channel_priorities", 5, 0xFF)
    if len(config.axes) != 3 or any(not isinstance(axis, ControlAxisConfig) for axis in config.axes):
        raise TypeError("config.axes must contain ControlAxisConfig for roll, pitch, and yaw")
    native_axes = (NativeControlAxisConfig * 3)(*(
        NativeControlAxisConfig(
            angle_lpf=validate_uint(axis.angle_lpf, "angle_lpf", 0xFF),
            speed_lpf=validate_uint(axis.speed_lpf, "speed_lpf", 0xFF),
            rc_lpf=validate_uint(axis.rc_lpf, "rc_lpf", 0xFF),
            acceleration_limit=validate_uint(axis.acceleration_limit, "acceleration_limit", 0xFFFF),
            jerk_slope=validate_uint(axis.jerk_slope, "jerk_slope", 0xFF),
        ) for axis in config.axes
    ))
    native_config = NativeControlConfig(
        timeout_ms=validate_uint(config.timeout_ms, "timeout_ms", 0xFFFF),
        channel_priorities=(ctypes.c_uint8 * 5)(*priorities), axis=native_axes,
        rc_expo_rate=validate_uint(config.rc_expo_rate, "rc_expo_rate", 0xFF),
        flags=flags, euler_order=validate_uint(config.euler_order, "euler_order", 0xFF),
    )
    return make_confirmation(self._native.control_config(
        self._device, native_config, need_confirmation=need_confirmation
    ))


def control_config(self, config: ControlConfig | None = None, *, confirm_control: bool | None = None, need_confirmation: bool = False) -> CommandConfirmation | None:
    """Alias for :func:`configure_control`."""
    return configure_control(self, config, confirm_control=confirm_control, need_confirmation=need_confirmation)


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
            raise ValueError(f"Channel {index} must be in range {_API_VIRTUAL_MIN}...{_API_VIRTUAL_MAX} or None")

    self._native.set_api_virtual_channels(self._device, tuple(native_values))