from __future__ import annotations

from math import isfinite
from struct import pack, unpack

from ._service import format_table
from .types import (
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
    command_type = _command_type(command_type)
    if command_type is ExternalImuCommandType.TX:
        if response_size is not None:
            raise ValueError("response_size is only valid for RX or TX_RX commands")
        return payload, command_type, len(payload)
    if response_size is None:
        if command_type is ExternalImuCommandType.RX:
            raise ValueError("RX commands require response_size")
        response_size = len(payload)
    response_size = _uint8(response_size, "response_size")
    if response_size > 254:
        raise ValueError("response_size must not exceed 254")
    if command_type is ExternalImuCommandType.TX_RX and response_size != len(payload):
        raise ValueError("TX_RX requires response_size equal to the payload size")
    if command_type is ExternalImuCommandType.RX and payload:
        raise ValueError("RX commands must use an empty payload")
    return payload, command_type, response_size


def request_ext_imu_debug(self) -> ExternalImuDebugInfo:
    self._ensure_open()
    values = unpack("<7BHH2B13x12f", self._native.request_ext_imu_debug(self._device))
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


def send_ext_imu_command(
    self,
    command_id: int,
    payload: bytes = b"",
    *,
    command_type: ExternalImuCommandType | int = ExternalImuCommandType.TX,
    response_size: int | None = None,
) -> tuple[int, bytes] | None:
    self._ensure_open()
    payload, command_type, payload_size = _command_payload(payload, command_type, response_size)
    result = self._native.send_ext_imu_command(
        self._device,
        _uint8(command_id, "command_id"),
        payload,
        payload_size,
        int(command_type),
    )
    return None if command_type is ExternalImuCommandType.TX else result


def send_ext_sens_command(
    self,
    command_id: int,
    payload: bytes = b"",
    *,
    flags: ExternalSensorCommandFlag | int = ExternalSensorCommandFlag.LOW_PRIORITY,
    command_type: ExternalImuCommandType | int = ExternalImuCommandType.TX,
    response_size: int | None = None,
) -> tuple[int, bytes] | None:
    self._ensure_open()
    try:
        flags = ExternalSensorCommandFlag(flags)
    except ValueError as error:
        raise ValueError("flags must be ExternalSensorCommandFlag") from error
    payload, command_type, payload_size = _command_payload(payload, command_type, response_size)
    result = self._native.send_ext_sens_command(
        self._device,
        _uint8(command_id, "command_id"),
        payload,
        payload_size,
        int(flags),
        int(command_type),
    )
    return None if command_type is ExternalImuCommandType.TX else result


def format_ext_imu_debug(info: ExternalImuDebugInfo) -> str:
    if not isinstance(info, ExternalImuDebugInfo):
        raise TypeError("info must be ExternalImuDebugInfo")
    return format_table(
        ("Field", "Value"),
        (
            ("Main reference", str(info.main_imu_ref_src)),
            ("Frame reference", str(info.frame_imu_ref_src)),
            ("External IMU status", str(info.external_imu_status)),
            ("Packets received", str(info.packets_received)),
            ("Parse errors", str(info.parse_error_count)),
            ("Heading correction", str(info.external_heading_correction)),
            ("Attitude correction", str(info.external_attitude_correction)),
            (
                "Acceleration body",
                " ".join(f"{value:g}" for value in info.acceleration_body),
            ),
        ),
    )


def pack_ahrs_helper_mode(
    direction: AhrsHelperDirection | int = AhrsHelperDirection.GET,
    location: AhrsHelperLocation | int = AhrsHelperLocation.CAMERA_PLATFORM,
    correction: AhrsHelperCorrection | int = AhrsHelperCorrection.BOTH_VECTORS,
    translation: AhrsHelperTranslation | int = AhrsHelperTranslation.BOTH_VECTORS,
    reference: AhrsHelperReference | int = AhrsHelperReference.SAME_AS_FRAME_IMU,
    options: AhrsHelperOption | int = AhrsHelperOption.NONE,
) -> int:
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
    return pack(
        "<6f",
        *_float_triplet(helper.z_vector, "z_vector"),
        *_float_triplet(helper.h_vector, "h_vector"),
    )


def _unpack_ahrs_helper(data: bytes) -> AhrsHelper:
    values = unpack("<6f", data)
    return AhrsHelper(z_vector=values[:3], h_vector=values[3:])


def get_ahrs_helper(self, mode: int = 0) -> AhrsHelper:
    self._ensure_open()
    mode = _ahrs_helper_mode(mode)
    if mode & int(AhrsHelperDirection.SET):
        raise ValueError("GET AHRS helper mode must not contain SET")
    return _unpack_ahrs_helper(self._native.call_ahrs_helper(self._device, bytes(24), mode))


def set_ahrs_helper(self, helper: AhrsHelper, mode: int = 1) -> None:
    self._ensure_open()
    mode = _ahrs_helper_mode(mode)
    if not mode & int(AhrsHelperDirection.SET):
        raise ValueError("SET AHRS helper mode must contain SET")
    self._native.call_ahrs_helper(self._device, _pack_ahrs_helper(helper), mode)


def correction_gyro(self, correction: GyroCorrection) -> None:
    self._ensure_open()
    if not isinstance(correction, GyroCorrection):
        raise TypeError("correction must be GyroCorrection")
    try:
        imu_type = ImuType(correction.imu_type)
    except ValueError as error:
        raise ValueError("imu_type must be ImuType.MAIN or ImuType.FRAME") from error
    if imu_type not in (ImuType.MAIN, ImuType.FRAME):
        raise ValueError("imu_type must be ImuType.MAIN or ImuType.FRAME")
    self._native.correction_gyro(
        self._device,
        int(imu_type) - 1,
        _int16_triplet(correction.zero_correction, "zero_correction"),
        _int16(correction.zero_heading_correction, "zero_heading_correction"),
    )


def _pack_helper_data(data: HelperData) -> bytes:
    if not isinstance(data, HelperData):
        raise TypeError("data must be HelperData")
    return pack(
        "<5h",
        *_int16_triplet(data.frame_acceleration, "frame_acceleration"),
        _int16(data.frame_angle_roll, "frame_angle_roll"),
        _int16(data.frame_angle_pitch, "frame_angle_pitch"),
    )


def provide_helper_data(self, data: HelperData) -> None:
    self._ensure_open()
    self._native.provide_helper_data(self._device, _pack_helper_data(data))


def _pack_helper_data_ext(data: HelperDataExt) -> bytes:
    if not isinstance(data, HelperDataExt):
        raise TypeError("data must be HelperDataExt")
    try:
        flags = HelperDataFlag(data.flags)
    except ValueError as error:
        raise ValueError("flags must be HelperDataFlag") from error
    if int(flags) & ~0xC3:
        raise ValueError("flags contains unsupported helper-data flags")
    return pack(
        "<5hB3hhB",
        *_int16_triplet(data.frame_acceleration, "frame_acceleration"),
        _int16(data.frame_angle_roll, "frame_angle_roll"),
        _int16(data.frame_angle_pitch, "frame_angle_pitch"),
        int(flags),
        *_int16_triplet(data.frame_speed, "frame_speed"),
        _int16(data.frame_heading, "frame_heading"),
        0,
    )


def provide_helper_data_ext(self, data: HelperDataExt) -> None:
    self._ensure_open()
    self._native.provide_helper_data_ext(self._device, _pack_helper_data_ext(data))


def format_ahrs_helper(helper: AhrsHelper) -> str:
    if not isinstance(helper, AhrsHelper):
        raise TypeError("helper must be AhrsHelper")
    return format_table(
        ("Field", "Value"),
        (
            ("Z vector", " ".join(f"{value:g}" for value in helper.z_vector)),
            ("H vector", " ".join(f"{value:g}" for value in helper.h_vector)),
        ),
    )
