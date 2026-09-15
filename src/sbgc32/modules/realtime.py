"""Asynchronous realtime and diagnostic commands.

This module contains protocol payload encoders and decoders only. Text
presentation helpers deliberately live in :mod:`sbgc32.format`.
"""

from __future__ import annotations

import struct
from collections.abc import Sequence
from concurrent.futures import Future
from types import MappingProxyType
from typing import TYPE_CHECKING

from ..commands import Command
from ..protocol import WireFrame
from ..types import (
    Angles,
    AnglesExt,
    Axis3,
    AxisGAE,
    AxisRealtimeData,
    CommandConfirmation,
    ConfirmationStatus,
    ControlQuatMode,
    ControlQuatStatus,
    ControlQuatStatusFlag,
    DataStreamCommand,
    DataStreamConfig,
    DebugVarInfo,
    ImuType,
    RcInputSource,
    RealtimeData3,
    RealtimeData4,
    RealtimeDataCustom,
    RealtimeDataCustomFlag,
    SelectImuAction,
)

if TYPE_CHECKING:
    from ..device import SimpleBGC


_REALTIME_DATA_3_SIZE = 63
_REALTIME_DATA_4_SIZE = 124
_ANGLES_SIZE = 18
_ANGLES_EXT_SIZE = 54
# SerialAPI ``sbgcAxisGA_t`` physical-unit scales.  CMD_GET_ANGLES sends
# signed protocol integers, not degrees directly.
_ANGLE_DEGREES_PER_UNIT = 360.0 / 16384.0
_SPEED_DEGREES_PER_SECOND_PER_UNIT = 0.1220740379


def _payload_exact(frame: WireFrame, size: int, name: str) -> bytes:
    if len(frame.payload) != size:
        raise ValueError(f"{name} response must contain {size} bytes, got {len(frame.payload)}")
    return frame.payload


def decode_angles(frame: WireFrame) -> Angles:
    """Decode ``CMD_GET_ANGLES`` into degrees and degrees per second."""

    values = struct.unpack("<9h", _payload_exact(frame, _ANGLES_SIZE, "GET_ANGLES"))
    return Angles(
        imu=Axis3(
            values[0] * _ANGLE_DEGREES_PER_UNIT,
            values[3] * _ANGLE_DEGREES_PER_UNIT,
            values[6] * _ANGLE_DEGREES_PER_UNIT,
        ),
        target=Axis3(
            values[1] * _ANGLE_DEGREES_PER_UNIT,
            values[4] * _ANGLE_DEGREES_PER_UNIT,
            values[7] * _ANGLE_DEGREES_PER_UNIT,
        ),
        target_speed=Axis3(
            values[2] * _SPEED_DEGREES_PER_SECOND_PER_UNIT,
            values[5] * _SPEED_DEGREES_PER_SECOND_PER_UNIT,
            values[8] * _SPEED_DEGREES_PER_SECOND_PER_UNIT,
        ),
    )


def decode_angles_ext(frame: WireFrame) -> AnglesExt:
    """Decode one ``CMD_GET_ANGLES_EXT`` response."""

    payload = _payload_exact(frame, _ANGLES_EXT_SIZE, "GET_ANGLES_EXT")
    return AnglesExt(
        axis_gae=tuple(
            AxisGAE(*struct.unpack_from("<hhi10s", payload, offset))
            for offset in range(0, _ANGLES_EXT_SIZE, 18)
        )
    )


def _decode_realtime_data_3_payload(payload: bytes) -> RealtimeData3:
    if len(payload) != _REALTIME_DATA_3_SIZE:
        raise ValueError(
            f"REALTIME_DATA_3 response must contain {_REALTIME_DATA_3_SIZE} bytes, "
            f"got {len(payload)}"
        )
    axis = struct.unpack_from("<6h", payload, 0)
    serial_error_count, system_error, system_sub_error = struct.unpack_from("<HHB", payload, 12)
    rc = struct.unpack_from("<6h", payload, 20)
    imu_angle = struct.unpack_from("<3h", payload, 32)
    frame_imu_angle = struct.unpack_from("<3h", payload, 38)
    target_angle = struct.unpack_from("<3h", payload, 44)
    cycle_time, i2c_error_count, error_code, bat_level, flags, imu, profile, *motor_power = (
        struct.unpack_from("<HHBHBBB3B", payload, 50)
    )
    return RealtimeData3(
        axis_rtd=(
            AxisRealtimeData(axis[0], axis[1]),
            AxisRealtimeData(axis[2], axis[3]),
            AxisRealtimeData(axis[4], axis[5]),
        ),
        serial_error_count=serial_error_count,
        system_error=system_error,
        system_sub_error=system_sub_error,
        reserved=payload[17:20],
        rc_roll=rc[0],
        rc_pitch=rc[1],
        rc_yaw=rc[2],
        rc_cmd=rc[3],
        ext_fc_roll=rc[4],
        ext_fc_pitch=rc[5],
        imu_angle=imu_angle,
        frame_imu_angle=frame_imu_angle,
        target_angle=target_angle,
        cycle_time=cycle_time,
        i2c_error_count=i2c_error_count,
        error_code=error_code,
        bat_level=bat_level,
        rt_data_flags=flags,
        cur_imu=imu,
        cur_profile=profile,
        motor_power=tuple(motor_power),
    )


def decode_realtime_data_3(frame: WireFrame) -> RealtimeData3:
    """Decode one 63-byte ``CMD_REALTIME_DATA_3`` response."""

    return _decode_realtime_data_3_payload(frame.payload)


def decode_realtime_data_4(frame: WireFrame) -> RealtimeData4:
    """Decode one 124-byte ``CMD_REALTIME_DATA_4`` response."""

    payload = _payload_exact(frame, _REALTIME_DATA_4_SIZE, "REALTIME_DATA_4")
    common = _decode_realtime_data_3_payload(payload[:_REALTIME_DATA_3_SIZE])
    frame_cam_angle = struct.unpack_from("<3h", payload, 63)
    balance_error = struct.unpack_from("<3h", payload, 70)
    current = struct.unpack_from("<H", payload, 76)[0]
    mag_data = struct.unpack_from("<3h", payload, 78)
    temperatures_and_errors = struct.unpack_from("<bbBB", payload, 84)
    motor_out = struct.unpack_from("<3h", payload, 88)
    calib_mode, can_imu_ext_sens_error = struct.unpack_from("<BB", payload, 94)
    actual_angle = struct.unpack_from("<3h", payload, 96)
    system_state_flags = struct.unpack_from("<I", payload, 102)[0]
    return RealtimeData4(
        **{field: getattr(common, field) for field in common.__dataclass_fields__},
        frame_cam_angle=frame_cam_angle,
        reserved1=payload[69],
        balance_error=balance_error,
        current=current,
        mag_data=mag_data,
        imu_temperature=temperatures_and_errors[0],
        frame_imu_temperature=temperatures_and_errors[1],
        imu_g_error=temperatures_and_errors[2],
        imu_h_error=temperatures_and_errors[3],
        motor_out=motor_out,
        calib_mode=calib_mode,
        can_imu_ext_sens_error=can_imu_ext_sens_error,
        actual_angle=actual_angle,
        system_state_flags=system_state_flags,
        reserved2=payload[106:124],
    )


def get_angles(self: SimpleBGC, *, timeout: float | None = 1.0) -> Future[Angles]:
    """Request IMU and target Euler angles in degrees, and speed in deg/s."""

    return self.request_raw(
        int(Command.CMD_GET_ANGLES), timeout=timeout, route="realtime", decoder=decode_angles
    )


def get_angles_ext(self: SimpleBGC, *, timeout: float | None = 1.0) -> Future[AnglesExt]:
    """Request raw extended angle records for all axes."""

    return self.request_raw(
        int(Command.CMD_GET_ANGLES_EXT),
        timeout=timeout,
        route="realtime",
        decoder=decode_angles_ext,
    )


def get_realtime_data(self: SimpleBGC, *, timeout: float | None = 1.0) -> Future[RealtimeData3]:
    """Request the legacy realtime-data layout."""

    return self.request_raw(
        int(Command.CMD_REALTIME_DATA),
        timeout=timeout,
        route="realtime",
        decoder=decode_realtime_data_3,
    )


def get_realtime_data_3(self: SimpleBGC, *, timeout: float | None = 1.0) -> Future[RealtimeData3]:
    """Request and asynchronously decode ``CMD_REALTIME_DATA_3``."""

    return self.request_raw(
        int(Command.CMD_REALTIME_DATA_3),
        timeout=timeout,
        route="realtime",
        decoder=decode_realtime_data_3,
    )


def get_realtime_data_4(self: SimpleBGC, *, timeout: float | None = 1.0) -> Future[RealtimeData4]:
    """Request and asynchronously decode ``CMD_REALTIME_DATA_4``."""

    return self.request_raw(
        int(Command.CMD_REALTIME_DATA_4),
        timeout=timeout,
        route="realtime",
        decoder=decode_realtime_data_4,
    )


_CUSTOM_FIELD_SIZES = (
    6,
    6,
    6,
    6,
    6,
    12,
    24,
    36,
    6,
    8,
    26,
    9,
    12,
    40,
    20,
    46,
    6,
    12,
    12,
    7,
    13,
    8,
    8,
    8,
    8,
    12,
    6,
    24,
)


def _coerce_custom_flags(flags: RealtimeDataCustomFlag | int) -> RealtimeDataCustomFlag:
    if isinstance(flags, bool):
        raise TypeError("flags must be RealtimeDataCustomFlag bits")
    try:
        selected = RealtimeDataCustomFlag(flags)
    except ValueError as error:
        raise ValueError("flags must contain only CMD_REALTIME_DATA_CUSTOM bits") from error
    if int(selected) < 0 or int(selected) & ~((1 << len(_CUSTOM_FIELD_SIZES)) - 1):
        raise ValueError("flags must contain only CMD_REALTIME_DATA_CUSTOM bits")
    return selected


def realtime_data_custom_payload_size(flags: RealtimeDataCustomFlag | int) -> int:
    """Return the response size, including the two-byte timestamp."""

    selected = _coerce_custom_flags(flags)
    size = 2 + sum(
        size for bit, size in enumerate(_CUSTOM_FIELD_SIZES) if int(selected) & (1 << bit)
    )
    if size > 0xFF:
        raise ValueError(f"selected realtime fields require {size} bytes; protocol limit is 255")
    return size


def parse_realtime_data_custom(
    flags: RealtimeDataCustomFlag | int, raw_payload: bytes
) -> RealtimeDataCustom:
    """Decode a ``CMD_REALTIME_DATA_CUSTOM`` payload for the requested flags."""

    selected = _coerce_custom_flags(flags)
    expected = realtime_data_custom_payload_size(selected)
    if len(raw_payload) != expected:
        raise ValueError(
            f"REALTIME_DATA_CUSTOM response must contain {expected} bytes, got {len(raw_payload)}"
        )
    timestamp_ms = struct.unpack_from("<H", raw_payload)[0]
    offset = 2
    fields: dict[RealtimeDataCustomFlag, object] = {}

    def read(format_string: str) -> object:
        nonlocal offset
        size = struct.calcsize(format_string)
        values = struct.unpack_from(format_string, raw_payload, offset)
        offset += size
        return values[0] if len(values) == 1 else values

    def read_bytes(size: int) -> bytes:
        nonlocal offset
        value = raw_payload[offset : offset + size]
        offset += size
        return value

    parsers = (
        lambda: read("<3h"),
        lambda: read("<3h"),
        lambda: read("<3h"),
        lambda: read("<3h"),
        lambda: read("<3h"),
        lambda: read("<6h"),
        lambda: read("<6f"),
        lambda: read("<18h"),
        lambda: read("<3h"),
        lambda: read("<hhf"),
        lambda: read_bytes(26),
        lambda: read_bytes(9),
        lambda: read("<3f"),
        lambda: read("<10f"),
        lambda: read("<10h"),
        lambda: read_bytes(46),
        lambda: read("<3h"),
        lambda: read("<3i"),
        lambda: read("<3i"),
        lambda: read("<3HB"),
        lambda: read_bytes(13),
        lambda: read_bytes(8),
        lambda: read_bytes(8),
        lambda: read_bytes(8),
        lambda: read("<4H"),
        lambda: read("<6h"),
        lambda: read("<3h"),
        lambda: read("<6i"),
    )
    for bit, parser in enumerate(parsers):
        flag = RealtimeDataCustomFlag(1 << bit)
        if selected & flag:
            fields[flag] = parser()
    return RealtimeDataCustom(selected, timestamp_ms, MappingProxyType(fields), raw_payload)


def get_realtime_data_custom(
    self: SimpleBGC, flags: RealtimeDataCustomFlag | int, *, timeout: float | None = 1.0
) -> Future[RealtimeDataCustom]:
    """Request selected realtime fields and decode them in the realtime worker."""

    selected = _coerce_custom_flags(flags)
    realtime_data_custom_payload_size(selected)
    return self.request_raw(
        int(Command.CMD_REALTIME_DATA_CUSTOM),
        struct.pack("<I", int(selected)),
        timeout=timeout,
        route="realtime",
        decoder=lambda frame: parse_realtime_data_custom(selected, frame.payload),
    )


_RC_VALUE_UNDEFINED = -32768
_RC_STANDARD_MAX = 500
_RC_HIGH_RES_MAX = 16384


def _rc_value_to_standard(value: int) -> int | None:
    """Convert firmware high-resolution RC units to standard -500..500."""

    if value == _RC_VALUE_UNDEFINED:
        return None
    magnitude = (abs(value) * _RC_STANDARD_MAX + (_RC_HIGH_RES_MAX // 2)) // _RC_HIGH_RES_MAX
    return magnitude if value >= 0 else -magnitude


def _rc_source_ids(sources: object) -> tuple[int, ...]:
    try:
        source_ids = tuple(sources)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("sources must be an iterable of RC source IDs") from error
    if not 1 <= len(source_ids) <= 42:
        raise ValueError("sources must contain from 1 to 42 items")
    if any(
        isinstance(source, bool) or not isinstance(source, int) or not 0 <= source <= 0xFF
        for source in source_ids
    ):
        raise ValueError("each RC source ID must be an integer in range 0..255")
    return source_ids


def decode_rc_inputs(frame: WireFrame, count: int) -> tuple[int | None, ...]:
    """Decode ``CMD_READ_RC_INPUTS`` values for ``count`` requested sources."""

    values = struct.unpack(f"<{count}h", _payload_exact(frame, count * 2, "READ_RC_INPUTS"))
    return tuple(_rc_value_to_standard(value) for value in values)


def read_rc_inputs(
    self: SimpleBGC, sources: Sequence[RcInputSource | int], *, timeout: float | None = 1.0
) -> Future[tuple[int | None, ...]]:
    """Read RC sources as standard -500..500 values; inactive values are ``None``."""

    source_ids = _rc_source_ids(sources)
    return self.request_raw(
        int(Command.CMD_READ_RC_INPUTS),
        struct.pack("<H", 0) + bytes(source_ids),
        timeout=timeout,
        route="realtime",
        decoder=lambda frame: decode_rc_inputs(frame, len(source_ids)),
    )


_CONTROL_QUAT_STATUS_FIELD_SIZES = (3, 16, 16, 16, 6, 6, 6, 8, 8, 8)
_CONTROL_QUAT_STATUS_MASK = (1 << len(_CONTROL_QUAT_STATUS_FIELD_SIZES)) - 1


def _coerce_control_quat_flags(flags: ControlQuatStatusFlag | int) -> ControlQuatStatusFlag:
    if isinstance(flags, bool):
        raise TypeError("flags must be ControlQuatStatusFlag bits")
    try:
        selected = ControlQuatStatusFlag(flags)
    except ValueError as error:
        raise ValueError("flags must be CONTROL_QUAT_STATUS bits") from error
    if int(selected) & ~_CONTROL_QUAT_STATUS_MASK:
        raise ValueError("flags contain unsupported CONTROL_QUAT_STATUS bits")
    if not selected:
        raise ValueError("flags must select at least one CONTROL_QUAT_STATUS field")
    return selected


def control_quat_status_payload_size(flags: ControlQuatStatusFlag | int) -> int:
    """Return the expected byte length of a quaternion-status payload."""

    selected = _coerce_control_quat_flags(flags)
    return sum(
        size
        for bit, size in enumerate(_CONTROL_QUAT_STATUS_FIELD_SIZES)
        if int(selected) & (1 << bit)
    )


def decode_control_quat_status(
    frame: WireFrame, flags: ControlQuatStatusFlag | int
) -> ControlQuatStatus:
    """Decode a raw ``CMD_CONTROL_QUAT_STATUS`` response.

    The board echoes the requested 16-bit flags before the selected fields.
    """

    selected = _coerce_control_quat_flags(flags)
    expected = 2 + control_quat_status_payload_size(selected)
    payload = _payload_exact(frame, expected, "CONTROL_QUAT_STATUS")
    echoed_flags = struct.unpack_from("<H", payload)[0]
    if echoed_flags != int(selected):
        raise ValueError("CONTROL_QUAT_STATUS response flags do not match the request")
    offset = 2
    values: dict[str, object] = {}

    def read(format_string: str) -> object:
        nonlocal offset
        size = struct.calcsize(format_string)
        result = struct.unpack_from(format_string, payload, offset)
        offset += size
        return result[0] if len(result) == 1 else result

    def read_bytes(size: int) -> bytes:
        nonlocal offset
        result = payload[offset : offset + size]
        offset += size
        return result

    if selected & ControlQuatStatusFlag.MODE_AND_FLAGS:
        raw_mode = read("<B")
        try:
            values["mode"] = ControlQuatMode(raw_mode)
        except ValueError:
            values["mode"] = raw_mode
        values["control_flags"] = read("<H")
    for flag, name, parser in (
        (ControlQuatStatusFlag.TARGET_ATTITUDE, "target_attitude", lambda: read("<4f")),
        (ControlQuatStatusFlag.SETPOINT_ATTITUDE, "setpoint_attitude", lambda: read("<4f")),
        (ControlQuatStatusFlag.ACTUAL_ATTITUDE, "actual_attitude", lambda: read("<4f")),
        (ControlQuatStatusFlag.TARGET_SPEED, "target_speed_raw", lambda: read("<3h")),
        (ControlQuatStatusFlag.SETPOINT_SPEED, "setpoint_speed_raw", lambda: read("<3h")),
        (ControlQuatStatusFlag.ACTUAL_SPEED, "actual_speed_raw", lambda: read("<3h")),
        (
            ControlQuatStatusFlag.TARGET_ATTITUDE_PACKED,
            "target_attitude_packed",
            lambda: read_bytes(8),
        ),
        (
            ControlQuatStatusFlag.SETPOINT_ATTITUDE_PACKED,
            "setpoint_attitude_packed",
            lambda: read_bytes(8),
        ),
        (
            ControlQuatStatusFlag.ACTUAL_ATTITUDE_PACKED,
            "actual_attitude_packed",
            lambda: read_bytes(8),
        ),
    ):
        if selected & flag:
            values[name] = parser()
    return ControlQuatStatus(selected, raw_payload=payload, **values)


def get_control_quat_status(
    self: SimpleBGC, flags: ControlQuatStatusFlag | int, *, timeout: float | None = 1.0
) -> Future[ControlQuatStatus]:
    """Request selected quaternion-control status fields (firmware 2.73+)."""

    selected = _coerce_control_quat_flags(flags)
    return self.request_raw(
        int(Command.CMD_CONTROL_QUAT_STATUS),
        struct.pack("<I", int(selected)),
        timeout=timeout,
        route="realtime",
        decoder=lambda frame: decode_control_quat_status(frame, selected),
    )


def decode_debug_value(raw_type: int, raw_value: int) -> int | float:
    """Decode one four-byte DEBUG_VARS_3 value according to its type tag."""

    raw = raw_value.to_bytes(4, byteorder="little")
    match raw_type & 0x07:
        case 1:
            return raw[0]
        case 2:
            return int.from_bytes(raw[:1], "little", signed=True)
        case 3:
            return int.from_bytes(raw[:2], "little")
        case 4:
            return int.from_bytes(raw[:2], "little", signed=True)
        case 5:
            return raw_value
        case 6:
            return int.from_bytes(raw, "little", signed=True)
        case 7:
            return struct.unpack("<f", raw)[0]
    raise TypeError(f"Unsupported DEBUG_VARS_3 type: 0x{raw_type:02X}")


def _debug_value_size(raw_type: int) -> int:
    """Return the encoded byte width of one DEBUG_VARS_3 type tag."""

    match raw_type & 0x07:
        case 1 | 2:
            return 1
        case 3 | 4:
            return 2
        case 5 | 6 | 7:
            return 4
    raise TypeError(f"Unsupported DEBUG_VARS_3 type: 0x{raw_type:02X}")


def _make_debug_var_masks(selected_indexes: Sequence[int], variable_count: int) -> tuple[int, ...]:
    """Build little-endian 32-bit selection masks for DEBUG_VARS_3."""

    if not selected_indexes:
        raise ValueError("selected_indexes must not be empty")
    if any(type(index) is not int or not 0 <= index < variable_count for index in selected_indexes):
        raise ValueError("each selected index must refer to a known debug variable")
    masks = [0] * (max(selected_indexes) // 32 + 1)
    for index in selected_indexes:
        masks[index // 32] |= 1 << (index % 32)
    return tuple(masks)


def _data_stream_command_id(command: DataStreamCommand | int) -> int:
    if isinstance(command, bool) or not isinstance(command, int):
        raise TypeError("command must be a DataStreamCommand or integer")
    if not 0 <= command <= 0xFF:
        raise ValueError("command must be an integer in range 0..255")
    return int(command)


def _encode_data_stream_config(
    config: DataStreamConfig, *, interval_ms: int | None = None
) -> bytes:
    if not isinstance(config, DataStreamConfig):
        raise TypeError("config must be a DataStreamConfig")
    interval = config.interval_ms if interval_ms is None else interval_ms
    if type(interval) is not int or not 0 <= interval <= 0xFFFF:
        raise ValueError("interval_ms must be an integer in range 0..65535")
    if interval_ms is None and interval == 0:
        raise ValueError("config.interval_ms must be in range 1..65535")
    if type(config.sync_to_data) is not bool:
        raise TypeError("config.sync_to_data must be bool")
    if not isinstance(config.config, bytes) or len(config.config) > 8:
        raise ValueError("config.config must contain from 0 to 8 bytes")
    return struct.pack(
        "<BH8sB9s",
        _data_stream_command_id(config.command),
        interval,
        config.config.ljust(8, b"\x00"),
        config.sync_to_data,
        b"\x00" * 9,
    )


def decode_confirmation(frame: WireFrame) -> CommandConfirmation:
    """Decode CMD_CONFIRM or CMD_ERROR for a requested SerialAPI command."""

    if not frame.payload:
        raise ValueError("CMD_CONFIRM/CMD_ERROR response has no command ID")
    command_id = frame.payload[0]
    if frame.command_id == 67:
        if len(frame.payload) > 3:
            raise ValueError("CMD_CONFIRM response may contain at most two data bytes")
        return CommandConfirmation(
            command_id=command_id,
            status=ConfirmationStatus.RECEIVED,
            command_data=int.from_bytes(frame.payload[1:], "little"),
            error_code=0,
            error_data=b"",
        )
    if frame.command_id == 255:
        if len(frame.payload) < 2:
            raise ValueError("CMD_ERROR response has no error code")
        return CommandConfirmation(
            command_id=command_id,
            status=ConfirmationStatus.ERROR,
            command_data=0,
            error_code=frame.payload[1],
            error_data=frame.payload[2:],
        )
    raise ValueError(f"expected CMD_CONFIRM or CMD_ERROR, got command {frame.command_id}")


def _stream_result_size(config: DataStreamConfig, size: int | None) -> int:
    command_id = _data_stream_command_id(config.command)
    known = DataStreamCommand._value2member_map_.get(command_id)
    if known is DataStreamCommand.REALTIME_DATA_CUSTOM:
        if len(config.config) < 4:
            raise ValueError("REALTIME_DATA_CUSTOM stream config must contain four flag bytes")
        size = realtime_data_custom_payload_size(int.from_bytes(config.config[:4], "little"))
    elif known is DataStreamCommand.REALTIME_DATA_3:
        size = _REALTIME_DATA_3_SIZE
    elif known is DataStreamCommand.REALTIME_DATA_4:
        size = _REALTIME_DATA_4_SIZE
    elif known is DataStreamCommand.AHRS_HELPER:
        size = 26
    elif known is DataStreamCommand.EVENT:
        size = 4
    if type(size) is not int or not 1 <= size <= 0xFF:
        raise ValueError("size must be an integer in range 1..255 for this stream")
    return size


def start_data_stream(
    self: SimpleBGC,
    config: DataStreamConfig,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Start a periodic data stream without blocking the calling thread."""

    payload = _encode_data_stream_config(config)
    if need_confirmation:
        return self.request_raw(
            int(Command.CMD_DATA_STREAM_INTERVAL),
            payload,
            timeout=timeout,
            route="realtime",
            decoder=decode_confirmation,
        )
    return self.send_raw(int(Command.CMD_DATA_STREAM_INTERVAL), payload, route="realtime")


def stop_data_stream(
    self: SimpleBGC,
    config: DataStreamConfig,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Stop a periodic data stream without blocking the calling thread."""

    payload = _encode_data_stream_config(config, interval_ms=0)
    if need_confirmation:
        return self.request_raw(
            int(Command.CMD_DATA_STREAM_INTERVAL),
            payload,
            timeout=timeout,
            route="realtime",
            decoder=decode_confirmation,
        )
    return self.send_raw(int(Command.CMD_DATA_STREAM_INTERVAL), payload, route="realtime")


def read_data_stream(
    self: SimpleBGC,
    config: DataStreamConfig,
    size: int | None = None,
    *,
    timeout: float | None = 1.0,
) -> Future[bytes]:
    """Return a Future for the next unmatched packet of a configured stream."""

    _encode_data_stream_config(config)
    command_id = _data_stream_command_id(config.command)
    expected_size = _stream_result_size(config, size)
    return self.receive_unsolicited_raw(
        command_id,
        timeout=timeout,
        route="realtime",
        decoder=lambda frame: _payload_exact(frame, expected_size, "data stream"),
    )


def _parse_debug_var_info(frame: WireFrame, start_index: int) -> tuple[DebugVarInfo, ...]:
    if not frame.payload:
        raise ValueError("DEBUG_VARS_INFO_3 response is empty")
    count = frame.payload[0]
    offset = 1
    result: list[DebugVarInfo] = []
    for index in range(count):
        if offset >= len(frame.payload):
            raise ValueError("DEBUG_VARS_INFO_3 response ended before all variables")
        name_length = frame.payload[offset]
        offset += 1
        if offset + name_length + 3 > len(frame.payload):
            raise ValueError("DEBUG_VARS_INFO_3 contains a truncated variable record")
        name = frame.payload[offset : offset + name_length].decode("ascii", errors="replace")
        offset += name_length
        raw_type = frame.payload[offset]
        offset += 3  # type plus two reserved bytes
        result.append(DebugVarInfo(start_index + index, name, raw_type))
    if offset != len(frame.payload):
        raise ValueError("DEBUG_VARS_INFO_3 response has trailing bytes")
    return tuple(result)


def request_debug_var_info_3(
    self: SimpleBGC, *, timeout: float | None = 1.0
) -> Future[tuple[DebugVarInfo, ...]]:
    """Fetch all paged DEBUG_VARS_INFO_3 records (firmware 2.72+)."""

    result: Future[tuple[DebugVarInfo, ...]] = Future()
    collected: list[DebugVarInfo] = []

    def request_page(start_index: int) -> None:
        if result.cancelled():
            return
        page = self.request_raw(
            int(Command.CMD_DEBUG_VARS_INFO_3),
            bytes((start_index,)),
            timeout=timeout,
            route="realtime",
            decoder=lambda frame: _parse_debug_var_info(frame, start_index),
        )

        def continue_pages(completed: Future[tuple[DebugVarInfo, ...]]) -> None:
            if result.done():
                return
            try:
                records = completed.result()
            except BaseException as error:
                result.set_exception(error)
                return
            collected.extend(records)
            next_index = start_index + len(records)
            if not records or next_index >= 0xFF:
                result.set_result(tuple(collected))
            else:
                request_page(next_index)

        page.add_done_callback(continue_pages)

    request_page(0)
    return result


def _decode_debug_var_values(
    frame: WireFrame,
    variables: tuple[DebugVarInfo, ...],
    selected_indexes: tuple[int, ...],
    masks: tuple[int, ...] | None,
) -> tuple[DebugVarInfo, ...]:
    payload = frame.payload
    offset = 0
    selected = tuple(range(len(variables))) if masks is None else selected_indexes
    if masks is not None:
        expected_masks_size = len(masks) * 4
        if len(payload) < expected_masks_size:
            raise ValueError("DEBUG_VARS_3 response is missing echoed masks")
        echoed = struct.unpack_from(f"<{len(masks)}I", payload)
        if echoed != masks:
            raise ValueError("DEBUG_VARS_3 response masks do not match the request")
        offset = expected_masks_size
    values: dict[int, int] = {}
    for index in selected:
        size = _debug_value_size(variables[index].raw_type)
        if offset + size > len(payload):
            raise ValueError("DEBUG_VARS_3 response ended before all selected values")
        values[index] = int.from_bytes(payload[offset : offset + size].ljust(4, b"\x00"), "little")
        offset += size
    if offset != len(payload):
        raise ValueError("DEBUG_VARS_3 response has trailing bytes")
    return tuple(
        variable
        if index not in values
        else DebugVarInfo(
            variable.index,
            variable.name,
            variable.raw_type,
            values[index],
            decode_debug_value(variable.raw_type, values[index]),
        )
        for index, variable in enumerate(variables)
    )


def request_debug_var_values_3(
    self: SimpleBGC,
    variables: Sequence[DebugVarInfo],
    selected_indexes: Sequence[int] | None = None,
    *,
    timeout: float | None = 1.0,
) -> Future[tuple[DebugVarInfo, ...]]:
    """Request DEBUG_VARS_3 values for every variable or a selected subset."""

    known = tuple(variables)
    if not known:
        raise ValueError("variables must not be empty")
    if tuple(variable.index for variable in known) != tuple(range(len(known))):
        raise ValueError("variables must be a complete, index-ordered DEBUG_VARS_INFO_3 list")
    selected = tuple(range(len(known))) if selected_indexes is None else tuple(selected_indexes)
    masks = None if selected_indexes is None else _make_debug_var_masks(selected, len(known))
    payload = b"" if masks is None else struct.pack(f"<{len(masks)}I", *masks)
    return self.request_raw(
        int(Command.CMD_DEBUG_VARS_3),
        payload,
        timeout=timeout,
        route="realtime",
        decoder=lambda frame: _decode_debug_var_values(frame, known, selected, masks),
    )


def select_imu_3(
    self: SimpleBGC,
    imu_type: ImuType | int,
    action: SelectImuAction | int = SelectImuAction.SIMPLE_SELECT,
    time_ms: int = 0,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Select an IMU or initiate a ``CMD_SELECT_IMU_3`` calibration action."""

    if isinstance(imu_type, bool) or isinstance(action, bool):
        raise TypeError("imu_type and action must be enum values or integers")
    if type(time_ms) is not int or not 0 <= time_ms <= 0xFFFF:
        raise ValueError("time_ms must be an integer in range 0..65535")
    try:
        selected_imu = ImuType(imu_type)
        selected_action = SelectImuAction(action)
    except ValueError as error:
        raise ValueError("imu_type or action is unsupported") from error
    if (
        selected_imu is ImuType.CURRENTLY_ACTIVE
        and selected_action is SelectImuAction.SIMPLE_SELECT
    ):
        raise ValueError("CURRENTLY_ACTIVE is only valid with an extended IMU action")
    payload = (
        bytes((int(selected_imu),))
        if selected_action is SelectImuAction.SIMPLE_SELECT
        else struct.pack("<BBH7s", int(selected_imu), int(selected_action), time_ms, b"\x00" * 7)
    )
    if need_confirmation:
        return self.request_raw(
            int(Command.CMD_SELECT_IMU_3),
            payload,
            timeout=timeout,
            route="realtime",
            decoder=decode_confirmation,
        )
    return self.send_raw(int(Command.CMD_SELECT_IMU_3), payload, route="realtime")
