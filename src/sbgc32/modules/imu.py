"""Asynchronous external-IMU and AHRS helper commands."""

from __future__ import annotations

import struct
from concurrent.futures import Future
from math import isfinite
from typing import TYPE_CHECKING

from ..commands import Command
from ..protocol import WireFrame
from ..types import (
    AhrsHelper,
    AhrsHelperCorrection,
    AhrsHelperDirection,
    AhrsHelperLocation,
    AhrsHelperOption,
    AhrsHelperReference,
    AhrsHelperTranslation,
    ExternalImuCommandType,
    ExternalImuDebugInfo,
    ExternalSensorCommandFlag,
    GyroCorrection,
    HelperData,
    HelperDataExt,
    HelperDataFlag,
    ImuType,
)

if TYPE_CHECKING:
    from ..device import SimpleBGC


_EXT_IMU_DEBUG_SIZE = 74


def _uint8(value: object, name: str) -> int:
    if type(value) is not int or not 0 <= value <= 0xFF:
        raise ValueError(f"{name} must be an integer in range 0..255")
    return value


def _int16(value: object, name: str) -> int:
    if type(value) is not int or not -0x8000 <= value <= 0x7FFF:
        raise ValueError(f"{name} must be a signed 16-bit integer")
    return value


def _int16_triplet(values: object, name: str) -> tuple[int, int, int]:
    if not isinstance(values, tuple) or len(values) != 3:
        raise ValueError(f"{name} must be a tuple with three entries")
    return tuple(_int16(value, name) for value in values)


def _float_triplet(values: object, name: str) -> tuple[float, float, float]:
    if not isinstance(values, tuple) or len(values) != 3:
        raise ValueError(f"{name} must be a tuple with three entries")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)
        for value in values
    ):
        raise ValueError(f"{name} must contain finite numbers")
    return tuple(float(value) for value in values)


def _command_type(value: ExternalImuCommandType | int) -> ExternalImuCommandType:
    if isinstance(value, bool):
        raise ValueError("command_type must be TX, RX, or TX_RX")
    try:
        return ExternalImuCommandType(value)
    except ValueError as error:
        raise ValueError("command_type must be TX, RX, or TX_RX") from error


def _command_payload(
    payload: object,
    command_type: ExternalImuCommandType | int,
    response_size: int | None,
) -> tuple[bytes, ExternalImuCommandType, int]:
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    if len(payload) > 254:
        raise ValueError("payload must contain at most 254 bytes")
    selected_type = _command_type(command_type)
    if selected_type is ExternalImuCommandType.TX:
        if response_size is not None:
            raise ValueError("response_size is only valid for RX or TX_RX commands")
        return payload, selected_type, len(payload)
    if response_size is None:
        if selected_type is ExternalImuCommandType.RX:
            raise ValueError("RX commands require response_size")
        response_size = len(payload)
    response_size = _uint8(response_size, "response_size")
    if response_size > 254:
        raise ValueError("response_size must not exceed 254")
    if selected_type is ExternalImuCommandType.TX_RX and response_size != len(payload):
        raise ValueError("TX_RX requires response_size equal to the payload size")
    if selected_type is ExternalImuCommandType.RX and payload:
        raise ValueError("RX commands must use an empty payload")
    return payload, selected_type, response_size


def _decode_ext_imu_debug(frame: WireFrame) -> ExternalImuDebugInfo:
    if len(frame.payload) != _EXT_IMU_DEBUG_SIZE:
        raise ValueError(
            f"EXT_IMU_DEBUG_INFO response must contain {_EXT_IMU_DEBUG_SIZE} bytes, "
            f"got {len(frame.payload)}"
        )
    values = struct.unpack("<7BHH2B13x12f", frame.payload)
    return ExternalImuDebugInfo(
        main_imu_ref_src=values[0],
        frame_imu_ref_src=values[1],
        main_imu_z_ref_error=values[2],
        main_imu_h_ref_error=values[3],
        frame_imu_z_ref_error=values[4],
        frame_imu_h_ref_error=values[5],
        external_imu_status=values[6],
        packets_received=values[7],
        parse_error_count=values[8],
        external_heading_correction=values[9],
        external_attitude_correction=values[10],
        dcm=tuple(values[11:20]),
        acceleration_body=(values[20], values[21], values[22]),
    )


def request_ext_imu_debug(
    self: SimpleBGC, *, timeout: float | None = 1.0
) -> Future[ExternalImuDebugInfo]:
    """Request the 74-byte diagnostic state of the external IMU."""

    return self.request_raw(
        int(Command.CMD_EXT_IMU_DEBUG_INFO),
        timeout=timeout,
        route="imu",
        decoder=_decode_ext_imu_debug,
    )


def _decode_external_command(frame: WireFrame, response_size: int) -> tuple[int, bytes]:
    expected_size = response_size + 1
    if len(frame.payload) != expected_size:
        raise ValueError(
            f"external IMU response must contain {expected_size} bytes, got {len(frame.payload)}"
        )
    return frame.payload[0], frame.payload[1:]


def _send_external_command(
    self: SimpleBGC,
    serial_command_id: int,
    payload: bytes,
    command_type: ExternalImuCommandType,
    response_size: int,
    *,
    timeout: float | None,
) -> Future[tuple[int, bytes] | None]:
    if command_type is ExternalImuCommandType.TX:
        return self.send_raw(serial_command_id, payload, route="imu")
    if command_type is ExternalImuCommandType.RX:
        return self.receive_unsolicited_raw(
            serial_command_id,
            timeout=timeout,
            route="imu",
            decoder=lambda frame: _decode_external_command(frame, response_size),
        )
    return self.request_raw(
        serial_command_id,
        payload,
        timeout=timeout,
        route="imu",
        decoder=lambda frame: _decode_external_command(frame, response_size),
    )


def send_ext_imu_command(
    self: SimpleBGC,
    command_id: int,
    payload: bytes = b"",
    *,
    command_type: ExternalImuCommandType | int = ExternalImuCommandType.TX,
    response_size: int | None = None,
    timeout: float | None = 1.0,
) -> Future[tuple[int, bytes] | None]:
    """Forward a raw packet to the external IMU, or await a packet from it."""

    payload, selected_type, response_size = _command_payload(payload, command_type, response_size)
    return _send_external_command(
        self,
        int(Command.CMD_EXT_IMU_CMD),
        bytes((_uint8(command_id, "command_id"),)) + payload,
        selected_type,
        response_size,
        timeout=timeout,
    )


def send_ext_sens_command(
    self: SimpleBGC,
    command_id: int,
    payload: bytes = b"",
    *,
    flags: ExternalSensorCommandFlag | int = ExternalSensorCommandFlag.LOW_PRIORITY,
    command_type: ExternalImuCommandType | int = ExternalImuCommandType.TX,
    response_size: int | None = None,
    timeout: float | None = 1.0,
) -> Future[tuple[int, bytes] | None]:
    """Forward a raw packet to the GPS/IMU external sensor."""

    if isinstance(flags, bool):
        raise ValueError("flags must be ExternalSensorCommandFlag")
    try:
        selected_flags = ExternalSensorCommandFlag(flags)
    except ValueError as error:
        raise ValueError("flags must be ExternalSensorCommandFlag") from error
    if int(selected_flags) & ~int(ExternalSensorCommandFlag.HIGH_PRIORITY):
        raise ValueError("flags contains unsupported external-sensor bits")
    payload, selected_type, response_size = _command_payload(payload, command_type, response_size)
    validated_command_id = _uint8(command_id, "command_id")
    return _send_external_command(
        self,
        int(Command.CMD_EXT_SENS_CMD),
        bytes((int(selected_flags), validated_command_id)) + payload,
        selected_type,
        response_size,
        timeout=timeout,
    )


def pack_ahrs_helper_mode(
    direction: AhrsHelperDirection | int = AhrsHelperDirection.GET,
    location: AhrsHelperLocation | int = AhrsHelperLocation.CAMERA_PLATFORM,
    correction: AhrsHelperCorrection | int = AhrsHelperCorrection.BOTH_VECTORS,
    translation: AhrsHelperTranslation | int = AhrsHelperTranslation.BOTH_VECTORS,
    reference: AhrsHelperReference | int = AhrsHelperReference.SAME_AS_FRAME_IMU,
    options: AhrsHelperOption | int = AhrsHelperOption.NONE,
) -> int:
    """Pack independent AHRS-helper selections into its 11-bit mode value."""

    try:
        direction = AhrsHelperDirection(direction)
        location = AhrsHelperLocation(location)
        correction = AhrsHelperCorrection(correction)
        translation = AhrsHelperTranslation(translation)
        reference = AhrsHelperReference(reference)
    except ValueError as error:
        raise ValueError("invalid AHRS helper mode field") from error
    if type(options) is bool or not isinstance(options, int) or int(options) & ~0x40C:
        raise ValueError("options contains unsupported AHRS helper flags")
    return int(direction | location | correction | translation | reference | int(options))


def _ahrs_helper_mode(value: object) -> int:
    if type(value) is not int or not 0 <= value <= 0x7FF:
        raise ValueError("mode must be an integer in range 0..2047")
    return value


def _pack_ahrs_helper(helper: object) -> bytes:
    if not isinstance(helper, AhrsHelper):
        raise TypeError("helper must be AhrsHelper")
    return struct.pack(
        "<6f",
        *_float_triplet(helper.z_vector, "z_vector"),
        *_float_triplet(helper.h_vector, "h_vector"),
    )


def _decode_ahrs_helper(frame: WireFrame) -> AhrsHelper:
    if len(frame.payload) != 24:
        raise ValueError(f"AHRS_HELPER response must contain 24 bytes, got {len(frame.payload)}")
    values = struct.unpack("<6f", frame.payload)
    return AhrsHelper(z_vector=values[:3], h_vector=values[3:])


def get_ahrs_helper(
    self: SimpleBGC, mode: int = 0, *, timeout: float | None = 1.0
) -> Future[AhrsHelper]:
    """Request the selected AHRS helper vectors."""

    mode = _ahrs_helper_mode(mode)
    if mode & int(AhrsHelperDirection.SET):
        raise ValueError("GET AHRS helper mode must not contain SET")
    return self.request_raw(
        int(Command.CMD_AHRS_HELPER),
        struct.pack("<H", mode),
        timeout=timeout,
        route="imu",
        decoder=_decode_ahrs_helper,
    )


def set_ahrs_helper(self: SimpleBGC, helper: AhrsHelper, mode: int = 1) -> Future[None]:
    """Set AHRS helper vectors without waiting for an RX response."""

    mode = _ahrs_helper_mode(mode)
    if not mode & int(AhrsHelperDirection.SET):
        raise ValueError("SET AHRS helper mode must contain SET")
    return self.send_raw(
        int(Command.CMD_AHRS_HELPER),
        struct.pack("<H", mode) + _pack_ahrs_helper(helper),
        route="imu",
    )


def correction_gyro(self: SimpleBGC, correction: GyroCorrection) -> Future[None]:
    """Send a manual zero-bias correction to the main or frame gyroscope."""

    if not isinstance(correction, GyroCorrection):
        raise TypeError("correction must be GyroCorrection")
    try:
        imu_type = ImuType(correction.imu_type)
    except ValueError as error:
        raise ValueError("imu_type must be ImuType.MAIN or ImuType.FRAME") from error
    if imu_type not in (ImuType.MAIN, ImuType.FRAME):
        raise ValueError("imu_type must be ImuType.MAIN or ImuType.FRAME")
    payload = struct.pack(
        "<B4h",
        int(imu_type) - 1,
        *_int16_triplet(correction.zero_correction, "zero_correction"),
        _int16(correction.zero_heading_correction, "zero_heading_correction"),
    )
    return self.send_raw(int(Command.CMD_GYRO_CORRECTION), payload, route="imu")


def _pack_helper_data(data: object) -> bytes:
    if not isinstance(data, HelperData):
        raise TypeError("data must be HelperData")
    return struct.pack(
        "<5h",
        *_int16_triplet(data.frame_acceleration, "frame_acceleration"),
        _int16(data.frame_angle_roll, "frame_angle_roll"),
        _int16(data.frame_angle_pitch, "frame_angle_pitch"),
    )


def provide_helper_data(self: SimpleBGC, data: HelperData) -> Future[None]:
    """Send legacy AHRS helper data (firmware before 2.60)."""

    return self.send_raw(int(Command.CMD_HELPER_DATA), _pack_helper_data(data), route="imu")


def _pack_helper_data_ext(data: object) -> bytes:
    if not isinstance(data, HelperDataExt):
        raise TypeError("data must be HelperDataExt")
    try:
        flags = HelperDataFlag(data.flags)
    except ValueError as error:
        raise ValueError("flags must be HelperDataFlag") from error
    if int(flags) & ~0xC3:
        raise ValueError("flags contains unsupported helper-data flags")
    return struct.pack(
        "<5hB3hhB",
        *_int16_triplet(data.frame_acceleration, "frame_acceleration"),
        _int16(data.frame_angle_roll, "frame_angle_roll"),
        _int16(data.frame_angle_pitch, "frame_angle_pitch"),
        int(flags),
        *_int16_triplet(data.frame_speed, "frame_speed"),
        _int16(data.frame_heading, "frame_heading"),
        0,
    )


def provide_helper_data_ext(self: SimpleBGC, data: HelperDataExt) -> Future[None]:
    """Send extended AHRS helper data (firmware 2.60+)."""

    return self.send_raw(int(Command.CMD_HELPER_DATA), _pack_helper_data_ext(data), route="imu")
