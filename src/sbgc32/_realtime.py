"""Realtime and angle response conversion."""

from __future__ import annotations

from os import error
import struct
import ctypes
from types import MappingProxyType

from sbgc32._serial_api_library import NativeDataStreamInterval, NativeDebugVarInfo3

from collections.abc import Sequence

from ._control import make_confirmation
from .native import NativeError
from .types import (
    Angles, AnglesExt, Axis3, AxisGAE, AxisRealtimeData, DataStreamCommand, DataStreamConfig,
    RealtimeData3, RealtimeData4, RealtimeDataCustom, RealtimeDataCustomFlag,
    CommandConfirmation, ControlQuatMode, ControlQuatStatus, ControlQuatStatusFlag,
    DebugVarInfo, ImuType, SelectImuAction,
)


def get_angles(self) -> Angles:
    self._ensure_open()
    result = self._native.get_angles(self._device)
    return Angles(
        imu=Axis3(result.imu.roll, result.imu.pitch, result.imu.yaw),
        target=Axis3(result.target.roll, result.target.pitch, result.target.yaw),
        target_speed=Axis3(result.target_speed.roll, result.target_speed.pitch, result.target_speed.yaw),
    )


def get_angles_ext(self) -> AnglesExt:
    self._ensure_open()
    result = self._native.get_angles_ext(self._device)
    return AnglesExt(axis_gae=tuple(AxisGAE(
        imu_angle=axis.imu_angle, target_angle=axis.target_angle,
        frame_cam_angle=axis.frame_cam_angle, reserved=bytes(axis.reserved),
    ) for axis in result.axis_gae))


def make_realtime_data_3(result) -> RealtimeData3:
    return RealtimeData3(
        axis_rtd=tuple(AxisRealtimeData(acc_data=axis.acc_data, gyro_data=axis.gyro_data) for axis in result.axis_rtd),
        serial_error_count=result.serial_error_count, system_error=result.system_error,
        system_sub_error=result.system_sub_error, reserved=bytes(result.reserved),
        rc_roll=result.rc_roll, rc_pitch=result.rc_pitch, rc_yaw=result.rc_yaw, rc_cmd=result.rc_cmd,
        ext_fc_roll=result.ext_fc_roll, ext_fc_pitch=result.ext_fc_pitch,
        imu_angle=tuple(result.imu_angle), frame_imu_angle=tuple(result.frame_imu_angle),
        target_angle=tuple(result.target_angle), cycle_time=result.cycle_time,
        i2c_error_count=result.i2c_error_count, error_code=result.error_code,
        bat_level=result.bat_level, rt_data_flags=result.rt_data_flags, cur_imu=result.cur_imu,
        cur_profile=result.cur_profile, motor_power=tuple(result.motor_power),
    )


def get_realtime_data(self) -> RealtimeData3:
    self._ensure_open()
    return make_realtime_data_3(self._native.get_realtime_data(self._device))


def get_realtime_data_3(self) -> RealtimeData3:
    self._ensure_open()
    return make_realtime_data_3(self._native.get_realtime_data_3(self._device))


def get_realtime_data_4(self) -> RealtimeData4:
    self._ensure_open()
    result = self._native.get_realtime_data_4(self._device)
    common = make_realtime_data_3(result)
    return RealtimeData4(
        **{name: getattr(common, name) for name in common.__dataclass_fields__},
        frame_cam_angle=tuple(result.frame_cam_angle), reserved1=result.reserved1,
        balance_error=tuple(result.balance_error), current=result.current, mag_data=tuple(result.mag_data),
        imu_temperature=result.imu_temperature, frame_imu_temperature=result.frame_imu_temperature,
        imu_g_error=result.imu_g_error, imu_h_error=result.imu_h_error, motor_out=tuple(result.motor_out),
        calib_mode=result.calib_mode, can_imu_ext_sens_error=result.can_imu_ext_sens_error,
        actual_angle=tuple(result.actual_angle), system_state_flags=result.system_state_flags,
        reserved2=bytes(result.reserved2),
    )


def realtime_data_custom_payload_size(flags: RealtimeDataCustomFlag) -> int:
    field_sizes = (6, 6, 6, 6, 6, 12, 24, 36, 6, 8, 26, 9, 12, 40, 20, 46, 6, 12, 12, 7, 13, 8, 8, 8, 8, 12, 6, 24)
    size = 2 + sum(size for bit, size in enumerate(field_sizes) if int(flags) & (1 << bit))
    if size > 0xFF:
        raise ValueError(f"selected realtime fields require {size} bytes; the protocol limit is 255")
    return size


def parse_realtime_data_custom(flags: RealtimeDataCustomFlag, raw_payload: bytes) -> RealtimeDataCustom:
    timestamp_ms = struct.unpack_from("<H", raw_payload)[0]
    offset = 2
    fields: dict[RealtimeDataCustomFlag, object] = {}
    def read(format_string: str):
        nonlocal offset
        size = struct.calcsize(format_string)
        value = struct.unpack_from(format_string, raw_payload, offset)
        offset += size
        return value[0] if len(value) == 1 else value
    def read_bytes(size: int) -> bytes:
        nonlocal offset
        value = raw_payload[offset:offset + size]
        offset += size
        return value
    parsers = (lambda: read("<3h"), lambda: read("<3h"), lambda: read("<3h"), lambda: read("<3h"), lambda: read("<3h"), lambda: read("<6h"), lambda: read("<6f"), lambda: read("<18h"), lambda: read("<3h"), lambda: read("<hhf"), lambda: read_bytes(26), lambda: read_bytes(9), lambda: read("<3f"), lambda: read("<10f"), lambda: read("<10h"), lambda: read_bytes(46), lambda: read("<3h"), lambda: read("<3i"), lambda: read("<3i"), lambda: read("<3HB"), lambda: read_bytes(13), lambda: read_bytes(8), lambda: read_bytes(8), lambda: read_bytes(8), lambda: read("<4H"), lambda: read("<6h"), lambda: read("<3h"), lambda: read("<6i"))
    for bit, parser in enumerate(parsers):
        flag = RealtimeDataCustomFlag(1 << bit)
        if flags & flag:
            fields[flag] = parser()
    if offset != len(raw_payload):
        raise NativeError("REALTIME_DATA_CUSTOM response length does not match the requested flags.")
    return RealtimeDataCustom(flags=flags, timestamp_ms=timestamp_ms, fields=MappingProxyType(fields), raw_payload=raw_payload)


def get_realtime_data_custom(self, flags: RealtimeDataCustomFlag | int) -> RealtimeDataCustom:
    self._ensure_open()
    try:
        selected_flags = RealtimeDataCustomFlag(flags)
    except ValueError as error:
        raise ValueError("flags must contain only CMD_REALTIME_DATA_CUSTOM bits") from error
    if int(selected_flags) < 0 or int(selected_flags) & ~((1 << 28) - 1):
        raise ValueError("flags must contain only CMD_REALTIME_DATA_CUSTOM bits")
    raw_payload = self._native.get_realtime_data_custom(
        self._device, int(selected_flags), realtime_data_custom_payload_size(selected_flags)
    )
    return parse_realtime_data_custom(selected_flags, raw_payload)


_RC_VALUE_UNDEFINED = -32768
_RC_STANDARD_MAX = 500
_RC_HIGH_RES_MAX = 16384


def _rc_value_to_standard(value: int) -> int | None:
    """Convert the firmware's high-resolution RC value to -500..500."""
    if value == _RC_VALUE_UNDEFINED:
        return None

    magnitude = (abs(value) * _RC_STANDARD_MAX + (_RC_HIGH_RES_MAX // 2)) // _RC_HIGH_RES_MAX
    return magnitude if value >= 0 else -magnitude


def read_rc_inputs(self, sources: object) -> tuple[int | None, ...]:
    """Read RC sources as standard -500..500 values; inactive inputs are None."""
    self._ensure_open()
    try:
        source_ids = tuple(sources)
    except TypeError as error:
        raise TypeError("Sources must be an iterable of RC source IDs") from error

    if not 1 <= len(source_ids) <= 42:
        raise ValueError("sources must contain from 1 to 42 items")
    if any(not isinstance(source, int) or not 0 <= source <= 255 for source in source_ids):
        raise ValueError("each RC source ID must be an integer in range 0..255")

    values = self._native.read_rc_inputs(self._device, source_ids)
    return tuple(_rc_value_to_standard(value) for value in values)


def _data_stream_config_to_native(config: DataStreamConfig) -> NativeDataStreamInterval:
    if not isinstance(config, DataStreamConfig):
        raise TypeError("Config must be a DataStreamConfig")

    if type(config.interval_ms) is not int or not 1 <= config.interval_ms <= 0xFFFF:
        raise ValueError("Interval_ms must be an integer in range 1...65535")

    if type(config.sync_to_data) is not bool:
        raise TypeError("Sync_to_data must be bool")

    if not isinstance(config.config, bytes) or len(config.config) > 8:
        raise ValueError("Config must contain from 0 to 8 bytes")

    return NativeDataStreamInterval(
        command_id=int(config.command),
        interval_ms=config.interval_ms,
        config=(ctypes.c_uint8 * 8).from_buffer_copy(config.config.ljust(8, b"\x00")),
        sync_to_data=config.sync_to_data,
    )

def start_data_stream(self, config: DataStreamConfig, *, need_confirmation: bool = False,) -> CommandConfirmation | None:
    self._ensure_open()
    native_config = _data_stream_config_to_native(config)

    return make_confirmation(self._native.start_data_stream(self._device, native_config, need_confirmation=need_confirmation, ))


def stop_data_stream(self, config: DataStreamConfig, *, need_confirmation: bool = False,) -> CommandConfirmation | None:
    self._ensure_open()
    native_config = _data_stream_config_to_native(config)

    return make_confirmation(self._native.stop_data_stream(self._device,native_config, need_confirmation=need_confirmation,))


def read_data_stream(self, config: DataStreamConfig, size: int | None = None,) -> bytes:
    self._ensure_open()

    if not isinstance(config, DataStreamConfig):
        raise TypeError("Config must be a DataStreamConfig")

    command = DataStreamCommand(config.command)

    match command:
        case DataStreamCommand.REALTIME_DATA_CUSTOM:
            if len(config.config) < 4:
                raise ValueError("REALTIME_DATA_CUSTOM stream config must contain four little-endian flag bytes")

            selected_flags = RealtimeDataCustomFlag(int.from_bytes(config.config[:4], byteorder="little"))

            if int(selected_flags) & ~((1 << 28) - 1):
                raise ValueError("REALTIME_DATA_CUSTOM stream config contains unsupported realtime-data flags")

            size = realtime_data_custom_payload_size(selected_flags)

        case DataStreamCommand.REALTIME_DATA_3:
            size = 63

        case DataStreamCommand.REALTIME_DATA_4:
            size = 124

        case DataStreamCommand.AHRS_HELPER:
            size = 26

        case DataStreamCommand.EVENT:
            size = 4

    if type(size) is not int or not 1 <= size <= 0xFF:
        raise ValueError("Payload_size must be an integer in range 1...255")

    return self._native.read_data_stream(self._device, int(config.command), size,)

_DEBUG_VAR_NAME_CAPACITY = 256
_DEBUG_VAR_REQUEST_CAPACITY = 0xFF


def _make_native_debug_var_info(count: int):
    """ Makes massive of C-struct and writable-buffer for names. """
    native_vars = (NativeDebugVarInfo3 * count)()
    name_buffers = [
        ctypes.create_string_buffer(_DEBUG_VAR_NAME_CAPACITY)
        for _ in range(count)
    ]

    for native_var, name_buffer in zip(native_vars, name_buffers):
        native_var.name = ctypes.cast(
            name_buffer,
            ctypes.POINTER(ctypes.c_char),
        )

    return native_vars, name_buffers


def decode_debug_value(raw_type: int, raw_value: int) -> int | float:
    """ Cast uint32 from native bridge to variable. """
    raw = raw_value.to_bytes(4, byteorder="little")

    match raw_type & 0x07:
        case 1:  # uint8
            return raw[0]
        case 2:  # int8
            return int.from_bytes(raw[:1], "little", signed=True)
        case 3:  # uint16
            return int.from_bytes(raw[:2], "little")
        case 4:  # int16
            return int.from_bytes(raw[:2], "little", signed=True)
        case 5:  # uint32
            return raw_value
        case 6:  # int32
            return int.from_bytes(raw, "little", signed=True)
        case 7:  # float32
            return struct.unpack("<f", raw)[0]

    raise NativeError(f"Unsupported DEBUG_VARS_3 type: 0x{raw_type:02X}")


def request_debug_var_info_3(self) -> tuple[DebugVarInfo, ...]:
    self._ensure_open()

    result: list[DebugVarInfo] = []
    start_index = 0

    while start_index < 0xFF:
        native_vars, name_buffers = _make_native_debug_var_info(_DEBUG_VAR_REQUEST_CAPACITY)

        self._native.request_debug_var_info_3(self._device, native_vars, start_index,)

        received = 0

        for native_var in native_vars:
            if native_var.name_length == 0:
                break

            name = ctypes.string_at(native_var.name, native_var.name_length,).decode("ascii", errors="replace")

            result.append(DebugVarInfo(index=start_index + received, name=name, raw_type=native_var.type,))
            received += 1

        del name_buffers

        if received == 0:
            break

        start_index += received

    return tuple(result)

def _make_debug_var_masks(selected_indexes: Sequence[int], variable_count: int,) -> tuple[int, ...]:
    if not selected_indexes:
        raise ValueError("Selected_indexes must not be empty")

    if any(type(index) is not int or not 0 <= index < variable_count for index in selected_indexes):
        raise ValueError("Each selected index must refer to a known debug variable")

    masks = [0] * (max(selected_indexes) // 32 + 1)

    for index in selected_indexes:
        masks[index // 32] |= 1 << (index % 32)

    return tuple(masks)


_DEBUG_VAR_TYPE_NAMES = {
    1: "uint8",
    2: "int8",
    3: "uint16",
    4: "int16",
    5: "uint32",
    6: "int32",
    7: "float32",
}


def format_debug_var_info_3(variables: Sequence[DebugVarInfo]) -> str:
    """Return a compact table suitable for displaying DEBUG_VARS_INFO_3."""
    variables = tuple(variables)

    if any(not isinstance(variable, DebugVarInfo) for variable in variables):
        raise TypeError("variables must contain DebugVarInfo instances")

    if not variables:
        return "DEBUG_VARS_INFO_3: no variables returned"

    rows: list[tuple[str, str, str, str]] = []

    for variable in variables:
        raw_type = variable.raw_type
        flags: list[str] = []

        match raw_type & 0x30:
            case 0x10:
                flags.append("ROLL")
            case 0x20:
                flags.append("PITCH")
            case 0x30:
                flags.append("YAW")

        if raw_type & 0x40:
            flags.append("ANGLE14")
        if raw_type & 0x80:
            flags.append("RESERVED")

        rows.append((
            str(variable.index),
            variable.name,
            _DEBUG_VAR_TYPE_NAMES.get(raw_type & 0x07, f"unknown (0x{raw_type:02X})"),
            ", ".join(flags) or "-",
        ))

    headers = ("IDX", "NAME", "TYPE", "FLAGS")
    widths = tuple(
        max(len(header), *(len(row[column]) for row in rows))
        for column, header in enumerate(headers)
    )

    def render(row: tuple[str, str, str, str]) -> str:
        return "  ".join(
            value.ljust(widths[column])
            for column, value in enumerate(row)
        ).rstrip()

    separator = "  ".join("-" * width for width in widths)
    return "\n".join((render(headers), separator, *(render(row) for row in rows)))


def print_debug_var_info_3(variables: Sequence[DebugVarInfo]) -> None:
    """Print DEBUG_VARS_INFO_3 in a readable table."""
    print(format_debug_var_info_3(variables))


def request_debug_var_values_3(self, variables: Sequence[DebugVarInfo], selected_indexes: Sequence[int] | None = None,) -> tuple[DebugVarInfo, ...]:
    self._ensure_open()

    variables = tuple(variables)
    if not variables:
        raise ValueError("Variables must not be empty")

    #if selected_indexes is not None:
    #    raise NotImplementedError("Masked DEBUG_VARS_3 is temporarily disabled: native parser is unsafe.")

    if tuple(variable.index for variable in variables) != tuple(range(len(variables))):
        raise ValueError("Variables must be a complete, index-ordered DEBUG_VARS_INFO_3 list")

    native_vars, name_buffers = _make_native_debug_var_info(len(variables))

    for native_var, variable in zip(native_vars, variables):
        native_var.type = variable.raw_type

    masks = (None 
             if selected_indexes is None 
             else _make_debug_var_masks(selected_indexes, len(variables)))

    self._native.request_debug_var_values_3(self._device, native_vars, masks,)

    selected = (range(len(variables))
        if selected_indexes is None
        else set(selected_indexes))

    result = []

    for index, (variable, native_var) in enumerate(zip(variables, native_vars)):
        if index not in selected:
            result.append(variable)
            continue

        raw_value = native_var.value
        result.append(DebugVarInfo(
            index=variable.index,
            name=variable.name,
            raw_type=variable.raw_type,
            raw_value=raw_value,
            value=decode_debug_value(variable.raw_type, raw_value),
        ))

    del name_buffers
    return tuple(result)


def select_imu_3(
    self,
    imu_type: ImuType | int,
    action: SelectImuAction | int = SelectImuAction.SIMPLE_SELECT,
    time_ms: int = 0,
    *,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    """Select an IMU or perform a CMD_SELECT_IMU_3 calibration action."""
    self._ensure_open()

    if isinstance(imu_type, bool):
        raise TypeError("imu_type must be an ImuType or integer")
    if isinstance(action, bool):
        raise TypeError("action must be a SelectImuAction or integer")
    if type(time_ms) is not int or not 0 <= time_ms <= 0xFFFF:
        raise ValueError("time_ms must be an integer in range 0...65535")

    try:
        selected_imu = ImuType(imu_type)
    except ValueError as error:
        raise ValueError("imu_type must be CURRENTLY_ACTIVE, MAIN, or FRAME") from error

    try:
        selected_action = SelectImuAction(action)
    except ValueError as error:
        raise ValueError("action must be a supported SelectImuAction") from error

    if selected_imu is ImuType.CURRENTLY_ACTIVE and selected_action is SelectImuAction.SIMPLE_SELECT:
        raise ValueError("CURRENTLY_ACTIVE is only valid with an extended IMU action")

    return make_confirmation(self._native.select_imu_3(
        self._device,
        int(selected_imu),
        int(selected_action),
        time_ms,
        need_confirmation=need_confirmation,
    ))


_CONTROL_QUAT_STATUS_FIELD_SIZES = (
    3,   # mode + flags
    16,  # target attitude
    16,  # setpoint attitude
    16,  # actual attitude
    6,   # target speed
    6,   # setpoint speed
    6,   # actual speed
    8,   # target packed attitude
    8,   # setpoint packed attitude
    8,   # actual packed attitude
)
_CONTROL_QUAT_STATUS_MASK = (1 << len(_CONTROL_QUAT_STATUS_FIELD_SIZES)) - 1


def control_quat_status_payload_size(flags: ControlQuatStatusFlag | int) -> int:
    selected = int(flags)
    if selected & ~_CONTROL_QUAT_STATUS_MASK:
        raise ValueError("flags contain unsupported CONTROL_QUAT_STATUS bits")

    size = sum(
        field_size
        for bit, field_size in enumerate(_CONTROL_QUAT_STATUS_FIELD_SIZES)
        if selected & (1 << bit)
    )
    if size == 0:
        raise ValueError("flags must select at least one CONTROL_QUAT_STATUS field")
    return size


def get_control_quat_status(
    self,
    flags: ControlQuatStatusFlag | int,
) -> ControlQuatStatus:
    """Read selected CMD_CONTROL_QUAT_STATUS fields (firmware 2.73+)."""
    self._ensure_open()

    try:
        selected = ControlQuatStatusFlag(flags)
    except ValueError as error:
        raise ValueError("flags must be CONTROL_QUAT_STATUS bits") from error

    payload_size = control_quat_status_payload_size(selected)
    raw_payload = self._native.control_quat_status(
        self._device,
        int(selected),
        payload_size,
    )

    offset = 0

    def read(format_string: str):
        nonlocal offset
        size = struct.calcsize(format_string)
        value = struct.unpack_from(format_string, raw_payload, offset)
        offset += size
        return value[0] if len(value) == 1 else value

    def read_bytes(size: int) -> bytes:
        nonlocal offset
        value = raw_payload[offset:offset + size]
        offset += size
        return value

    values: dict[str, object] = {}

    if selected & ControlQuatStatusFlag.MODE_AND_FLAGS:
        raw_mode = read("<B")
        try:
            values["mode"] = ControlQuatMode(raw_mode)
        except ValueError:
            values["mode"] = raw_mode
        values["control_flags"] = read("<H")

    if selected & ControlQuatStatusFlag.TARGET_ATTITUDE:
        values["target_attitude"] = read("<4f")
    if selected & ControlQuatStatusFlag.SETPOINT_ATTITUDE:
        values["setpoint_attitude"] = read("<4f")
    if selected & ControlQuatStatusFlag.ACTUAL_ATTITUDE:
        values["actual_attitude"] = read("<4f")
    if selected & ControlQuatStatusFlag.TARGET_SPEED:
        values["target_speed_raw"] = read("<3h")
    if selected & ControlQuatStatusFlag.SETPOINT_SPEED:
        values["setpoint_speed_raw"] = read("<3h")
    if selected & ControlQuatStatusFlag.ACTUAL_SPEED:
        values["actual_speed_raw"] = read("<3h")
    if selected & ControlQuatStatusFlag.TARGET_ATTITUDE_PACKED:
        values["target_attitude_packed"] = read_bytes(8)
    if selected & ControlQuatStatusFlag.SETPOINT_ATTITUDE_PACKED:
        values["setpoint_attitude_packed"] = read_bytes(8)
    if selected & ControlQuatStatusFlag.ACTUAL_ATTITUDE_PACKED:
        values["actual_attitude_packed"] = read_bytes(8)

    if offset != len(raw_payload):
        raise NativeError("CONTROL_QUAT_STATUS response length does not match the requested flags")

    return ControlQuatStatus(
        requested_fields=selected,
        raw_payload=raw_payload,
        **values,
    )
