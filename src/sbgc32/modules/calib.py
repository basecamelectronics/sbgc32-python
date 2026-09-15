"""Asynchronous calibration commands."""

from __future__ import annotations

import struct
from concurrent.futures import Future
from typing import TYPE_CHECKING

from ..commands import Command
from ..protocol import WireFrame
from ..types import CalibCogging, CalibCoggingAction, CalibInfo, CommandConfirmation, ImuType
from .realtime import decode_confirmation

if TYPE_CHECKING:
    from ..device import SimpleBGC


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
            int(command), payload, timeout=timeout, route="calib", decoder=decode_confirmation
        )
    return self.send_raw(int(command), payload, route="calib")


def _decode_info(frame: WireFrame) -> CalibInfo:
    if len(frame.payload) != 33:
        raise ValueError("CALIB_INFO response must contain 33 bytes")
    values = struct.unpack("<BB3hHBBbBbbB6bbbB7s", frame.payload)
    try:
        imu_type = ImuType(values[1])
    except ValueError as error:
        raise ValueError("CALIB_INFO contains unsupported IMU type") from error
    return CalibInfo(
        values[0],
        imu_type,
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


def request_calib_info(
    self: SimpleBGC, imu_type: ImuType | int = ImuType.MAIN, *, timeout: float | None = 1.0
) -> Future[CalibInfo]:
    try:
        selected = ImuType(imu_type)
    except ValueError as error:
        raise ValueError("imu_type must be ImuType.MAIN or ImuType.FRAME") from error
    if selected not in (ImuType.MAIN, ImuType.FRAME):
        raise ValueError("imu_type must be ImuType.MAIN or ImuType.FRAME")
    return self.request_raw(
        int(Command.CMD_CALIB_INFO),
        bytes((int(selected),)) + bytes(11),
        timeout=timeout,
        route="calib",
        decoder=_decode_info,
    )


def _start(command: Command):
    def method(self: SimpleBGC) -> Future[None]:
        return self.send_raw(int(command), route="calib")

    return method


calib_acc = _start(Command.CMD_CALIB_ACC)
calib_gyro = _start(Command.CMD_CALIB_GYRO)
calib_mag = _start(Command.CMD_CALIB_MAG)
calib_poles = _start(Command.CMD_CALIB_POLES)
calib_offset = _start(Command.CMD_CALIB_OFFSET)
calib_encoders_fld_offset = _start(Command.CMD_ENCODERS_CALIB_FLD_OFFSET_4)


def calib_encoders_offset(self: SimpleBGC, motor: int = 255) -> Future[None]:
    if type(motor) is not int or motor not in (0, 1, 2, 255):
        raise ValueError("motor must be 0, 1, 2, or 255")
    return self.send_raw(int(Command.CMD_ENCODERS_CALIB_OFFSET_4), bytes((motor,)), route="calib")


def calib_bat(
    self: SimpleBGC, voltage: int, *, need_confirmation: bool = False, timeout: float | None = 1.0
) -> Future[CommandConfirmation | None]:
    if type(voltage) is not int or not 0 <= voltage <= 65535:
        raise ValueError("voltage must be in 0.01 V units and range 0..65535")
    return _confirmation(
        self, Command.CMD_CALIB_BAT, struct.pack("<H", voltage), need_confirmation, timeout
    )


def calib_orient_corr(
    self: SimpleBGC, *, need_confirmation: bool = False, timeout: float | None = 1.0
) -> Future[CommandConfirmation | None]:
    return _confirmation(self, Command.CMD_CALIB_ORIENT_CORR, bytes(16), need_confirmation, timeout)


def _triplet(value: object) -> tuple[int, int, int]:
    if (
        not isinstance(value, tuple)
        or len(value) != 3
        or any(type(item) is not int or not -32768 <= item <= 32767 for item in value)
    ):
        raise ValueError("reference must be a tuple of three signed 16-bit integers")
    return value


def calib_acc_ext_ref(
    self: SimpleBGC,
    reference: tuple[int, int, int],
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    return _confirmation(
        self,
        Command.CMD_CALIB_ACC_EXT_REF,
        struct.pack("<3h14s", *_triplet(reference), bytes(14)),
        need_confirmation,
        timeout,
    )


def calib_cogging(
    self: SimpleBGC,
    cogging: CalibCogging,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    if (
        not isinstance(cogging, CalibCogging)
        or not isinstance(cogging.action, CalibCoggingAction)
        or not isinstance(cogging.axes, int)
        or not 1 <= int(cogging.axes) <= 7
        or not isinstance(cogging.axis_config, tuple)
        or len(cogging.axis_config) != 3
        or type(cogging.iterations) is not int
        or not 0 <= cogging.iterations <= 255
    ):
        raise ValueError("invalid cogging calibration configuration")
    payload = bytearray((int(cogging.action), int(cogging.axes)))
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
        payload.extend(
            struct.pack("<HBBH9s", axis.angle, axis.smooth, axis.speed, axis.period, bytes(9))
        )
    payload.extend((cogging.iterations,))
    payload.extend(bytes(9))
    return _confirmation(
        self, Command.CMD_CALIB_COGGING, bytes(payload), need_confirmation, timeout
    )
