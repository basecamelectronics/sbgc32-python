"""Realtime and angle response conversion."""

from __future__ import annotations

import struct
from types import MappingProxyType

from .native import NativeError
from .types import (
    Angles, AnglesExt, Axis3, AxisGAE, AxisRealtimeData,
    RealtimeData3, RealtimeData4, RealtimeDataCustom, RealtimeDataCustomFlag,
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
