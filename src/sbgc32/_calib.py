from __future__ import annotations

import ctypes
from struct import pack, unpack

from ._control import make_confirmation
from ._service import format_table
from .types import (
    CalibCogging,
    CalibCoggingAction,
    CalibInfo,
    CommandConfirmation,
    ImuType,
)


def request_calib_info(self, imu_type: ImuType | int = ImuType.MAIN) -> CalibInfo:
    self._ensure_open()
    try:
        imu_type = ImuType(imu_type)
    except ValueError as error:
        raise ValueError("imu_type must be ImuType.MAIN or ImuType.FRAME") from error
    if imu_type not in (ImuType.MAIN, ImuType.FRAME):
        raise ValueError("imu_type must be ImuType.MAIN or ImuType.FRAME")
    values = unpack(
        "<BB3hHBBbBbbB6bb bB7s",
        self._native.request_calib_info(self._device, int(imu_type)),
    )
    return CalibInfo(
        values[0],
        ImuType(values[1]),
        values[2:5],
        values[5],
        values[6],
        values[7],
        values[8],
        bool(values[9]),
        values[10],
        values[11],
        bool(values[12]),
        values[13:19],
        values[19],
        values[20],
        values[21],
    )


def _start(self, command: str, *arguments: int) -> None:
    self._ensure_open()
    self._native.calib(command, self._device, *arguments)


def calib_acc(self) -> None:
    _start(self, "calib_acc")


def calib_gyro(self) -> None:
    _start(self, "calib_gyro")


def calib_mag(self) -> None:
    _start(self, "calib_mag")


def calib_poles(self) -> None:
    _start(self, "calib_poles")


def calib_offset(self) -> None:
    _start(self, "calib_offset")


def calib_encoders_fld_offset(self) -> None:
    _start(self, "calib_encoders_fld_offset")


def calib_encoders_offset(self, motor: int = 255) -> None:
    if type(motor) is not int or motor not in (0, 1, 2, 255):
        raise ValueError("motor must be 0, 1, 2, or 255")
    _start(self, "calib_encoders_offset", motor)


def _int16_triplet(values: object, name: str) -> tuple[int, int, int]:
    if (
        not isinstance(values, tuple)
        or len(values) != 3
        or any(type(value) is not int or not -32768 <= value <= 32767 for value in values)
    ):
        raise ValueError(f"{name} must be a tuple of three signed 16-bit integers")
    return values


def calib_bat(self, voltage: int, *, need_confirmation: bool = False) -> CommandConfirmation | None:
    if type(voltage) is not int or not 0 <= voltage <= 65535:
        raise ValueError("voltage must be in 0.01 V units and range 0..65535")
    self._ensure_open()
    return make_confirmation(
        self._native.calib_confirm(
            "calib_bat", self._device, voltage, need_confirmation=need_confirmation
        )
    )


def calib_orient_corr(self, *, need_confirmation: bool = False) -> CommandConfirmation | None:
    self._ensure_open()
    return make_confirmation(
        self._native.calib_confirm(
            "calib_orient_corr", self._device, need_confirmation=need_confirmation
        )
    )


def calib_acc_ext_ref(
    self, reference: tuple[int, int, int], *, need_confirmation: bool = False
) -> CommandConfirmation | None:
    self._ensure_open()
    values = (ctypes.c_int16 * 3)(*_int16_triplet(reference, "reference"))
    return make_confirmation(
        self._native.calib_confirm(
            "calib_acc_ext_ref",
            self._device,
            values,
            need_confirmation=need_confirmation,
        )
    )


def calib_cogging(
    self, cogging: CalibCogging, *, need_confirmation: bool = False
) -> CommandConfirmation | None:
    if not isinstance(cogging, CalibCogging):
        raise TypeError("cogging must be CalibCogging")
    if not isinstance(cogging.action, CalibCoggingAction):
        raise TypeError("action must be CalibCoggingAction")
    if not isinstance(cogging.axes, int) or not 1 <= int(cogging.axes) <= 7:
        raise ValueError("axes must select one or more axes")
    if not isinstance(cogging.axis_config, tuple) or len(cogging.axis_config) != 3:
        raise ValueError("axis_config must contain roll, pitch, yaw")
    if type(cogging.iterations) is not int or not 0 <= cogging.iterations <= 255:
        raise ValueError("iterations must be in range 0..255")
    values = [int(cogging.action), int(cogging.axes)]
    for axis in cogging.axis_config:
        if (
            any(
                type(value) is not int
                for value in (axis.angle, axis.smooth, axis.speed, axis.period)
            )
            or not 0 <= axis.angle <= 65535
            or not 0 <= axis.smooth <= 100
            or not 0 <= axis.speed <= 255
            or not 0 <= axis.period <= 65535
        ):
            raise ValueError("invalid cogging axis configuration")
        values.extend((axis.angle, axis.smooth, axis.speed, axis.period))
    data = pack(
        "<BBHBBH9sHBBH9sHBBH9sB9s",
        values[0],
        values[1],
        values[2],
        values[3],
        values[4],
        values[5],
        bytes(9),
        values[6],
        values[7],
        values[8],
        values[9],
        bytes(9),
        values[10],
        values[11],
        values[12],
        values[13],
        bytes(9),
        cogging.iterations,
        bytes(9),
    )
    self._ensure_open()
    buffer = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
    return make_confirmation(
        self._native.calib_confirm(
            "calib_cogging",
            self._device,
            buffer,
            len(data),
            need_confirmation=need_confirmation,
        )
    )


def format_calib_info(info: CalibInfo) -> str:
    return format_table(
        ("Field", "Value"),
        (
            ("Progress", f"{info.progress}%"),
            ("IMU", info.imu_type.name),
            ("Acceleration", " ".join(map(str, info.acceleration))),
            ("Gyro amplitude", str(info.gyro_amplitude)),
            ("Temperature", f"{info.temperature_celsius} C"),
            ("Heading error", str(info.heading_error_length)),
        ),
    )
