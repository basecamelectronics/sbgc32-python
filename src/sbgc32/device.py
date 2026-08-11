from __future__ import annotations

import struct
from types import MappingProxyType
from time import sleep

from .commands import Command
from .native import NativeError, NativeLibrary
from .types import (
    Angles,
    AnglesExt,
    Axis3,
    AxisGAE,
    AxisRealtimeData,
    BoardInfo,
    BoardInfo3,
    MotorsOffMode,
    RealtimeDataCustom,
    RealtimeDataCustomFlag,
    RealtimeData3,
    RealtimeData4,
    ScriptDebugInfo,
)


class SimpleBGC:

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        startup_delay: float = 1.0,
        script_slot_count: int = 10,
    ) -> None:
        if startup_delay < 0:
            raise ValueError("startup_delay must be non-negative")
        if not 1 <= script_slot_count <= 10:
            raise ValueError("script_slot_count must be in range 1..10")
        self._native = NativeLibrary()
        try:
            self._device = self._native.open(port, baudrate)
            sleep(startup_delay)
        except Exception:
            raise
        self._closed = False
        self._script_slot_count = script_slot_count
        self._debug_script_slot: int | None = None

    # Read IMU, angle, speed for axes3
    def get_angles(self) -> Angles:

        self._ensure_open()
        result = self._native.get_angles(self._device)

        return Angles(
            imu=Axis3(result.imu.roll, result.imu.pitch, result.imu.yaw),
            target=Axis3(result.target.roll, result.target.pitch, result.target.yaw),
            target_speed=Axis3(
                result.target_speed.roll,
                result.target_speed.pitch,
                result.target_speed.yaw,
            ),
        )

    def get_angles_ext(self) -> AnglesExt:
        self._ensure_open()
        result = self._native.get_angles_ext(self._device)
        return AnglesExt(
            axis_gae=tuple(
                AxisGAE(
                    imu_angle=axis.imu_angle,
                    target_angle=axis.target_angle,
                    frame_cam_angle=axis.frame_cam_angle,
                    reserved=bytes(axis.reserved),
                )
                for axis in result.axis_gae
            ),
        )

    def reset(
        self,
        delay_ms: int = 100,
        *,
        need_confirmation: bool = True,
        restore_state: bool = False,
        confirmation_timeout: float = 2.0,
        startup_delay: float = 5.0,
    ) -> None:
        self._ensure_open()
        if not 0 <= delay_ms <= 0xFFFF:
            raise ValueError("delay_ms must be in range 0..65535")
        if startup_delay < 0:
            raise ValueError("startup_delay must be non-negative")
        if confirmation_timeout <= 0:
            raise ValueError("confirmation_timeout must be positive")

        flags = 0
        if need_confirmation:
            flags |= 0x01  # RESET_FLAG_NEED_CONFIRMATION
        if restore_state:
            flags |= 0x02  # RESET_FLAG_RESTORE_STATE

        self._native.reset(self._device, flags, delay_ms)
        self._debug_script_slot = None
        try:
            sleep(delay_ms / 1000)
            if need_confirmation:
                self._native.expect_reset(self._device, confirmation_timeout)
        finally:
            # CMD_RESET leaves the board rebooting even if its notification is
            # lost, so always reset the host transport before returning.
            sleep(startup_delay)
            self._native.recover(self._device)

    def motors_on(self) -> None:
        """Send CMD_MOTORS_ON.

        The command can move a loaded gimbal immediately. Make sure the rig has
        enough clearance before calling it.
        """
        self._ensure_open()
        self._native.motors_on(self._device)

    def motors_off(self, mode: MotorsOffMode = MotorsOffMode.SAFE_STOP) -> None:
        """Send CMD_MOTORS_OFF using the selected stopping mode.

        ``SAFE_STOP`` is the default recommended by SerialAPI. Firmware before
        2.68b7 ignores the mode byte.
        """
        self._ensure_open()
        try:
            selected_mode = MotorsOffMode(mode)
        except ValueError as error:
            raise ValueError("mode must be a MotorsOffMode value (0, 1, or 2)") from error
        self._native.motors_off(self._device, int(selected_mode))

    def run_script(self, slot: int = 1, *, debug: bool = False) -> None:
        self._ensure_open()
        if not 1 <= slot <= self._script_slot_count:
            raise ValueError(f"slot must be in range 1..{self._script_slot_count}")
        self._native.run_script(self._device, 2 if debug else 1, slot - 1)
        self._debug_script_slot = slot if debug else None

    def stop_script(self, slot: int = 1) -> None:
        self._ensure_open()
        if not 1 <= slot <= self._script_slot_count:
            raise ValueError(f"slot must be in range 1..{self._script_slot_count}")
        self._native.run_script(self._device, 0, slot - 1)
        if self._debug_script_slot == slot:
            self._debug_script_slot = None

    def read_script_debug_info(self, timeout: float = 1.0) -> ScriptDebugInfo:
        self._ensure_open()
        if self._debug_script_slot is None:
            raise RuntimeError(
                "CMD_SCRIPT_DEBUG is not enabled. Start a script with "
                "run_script(slot=..., debug=True) before reading debug information."
            )
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        result = self._native.read_script_debug_info(self._device, timeout)
        return ScriptDebugInfo(
            current_command_counter=result.current_command_counter,
            error_code=result.error_code,
        )

    def get_realtime_data(self) -> RealtimeData3:
        """Read legacy CMD_REALTIME_DATA (available on older firmware)."""
        self._ensure_open()
        return self._make_realtime_data_3(self._native.get_realtime_data(self._device))

    def get_realtime_data_3(self) -> RealtimeData3:
        """Read the 63-byte CMD_REALTIME_DATA_3 response."""
        self._ensure_open()
        return self._make_realtime_data_3(self._native.get_realtime_data_3(self._device))

    def get_realtime_data_4(self) -> RealtimeData4:
        """Read the 124-byte CMD_REALTIME_DATA_4 response."""
        self._ensure_open()
        result = self._native.get_realtime_data_4(self._device)
        common = self._make_realtime_data_3(result)
        common_values = {
            name: getattr(common, name) for name in common.__dataclass_fields__
        }
        return RealtimeData4(
            **common_values,
            frame_cam_angle=tuple(result.frame_cam_angle),
            reserved1=result.reserved1,
            balance_error=tuple(result.balance_error),
            current=result.current,
            mag_data=tuple(result.mag_data),
            imu_temperature=result.imu_temperature,
            frame_imu_temperature=result.frame_imu_temperature,
            imu_g_error=result.imu_g_error,
            imu_h_error=result.imu_h_error,
            motor_out=tuple(result.motor_out),
            calib_mode=result.calib_mode,
            can_imu_ext_sens_error=result.can_imu_ext_sens_error,
            actual_angle=tuple(result.actual_angle),
            system_state_flags=result.system_state_flags,
            reserved2=bytes(result.reserved2),
        )

    def get_realtime_data_custom(
        self, flags: RealtimeDataCustomFlag | int
    ) -> RealtimeDataCustom:
        """Request only the realtime fields selected by ``flags``.

        The command is read-only. Its variable-length response is decoded in
        the exact order prescribed by the requested bit flags.
        """
        self._ensure_open()
        try:
            selected_flags = RealtimeDataCustomFlag(flags)
        except ValueError as error:
            raise ValueError("flags must contain only CMD_REALTIME_DATA_CUSTOM bits") from error
        if int(selected_flags) < 0 or int(selected_flags) & ~((1 << 28) - 1):
            raise ValueError("flags must contain only CMD_REALTIME_DATA_CUSTOM bits")

        payload_size = self._realtime_data_custom_payload_size(selected_flags)
        raw_payload = self._native.get_realtime_data_custom(
            self._device, int(selected_flags), payload_size
        )
        return self._parse_realtime_data_custom(selected_flags, raw_payload)

    @staticmethod
    def _realtime_data_custom_payload_size(flags: RealtimeDataCustomFlag) -> int:
        field_sizes = (
            6, 6, 6, 6, 6, 12, 24, 36, 6, 8, 26, 9, 12, 40, 20, 46,
            6, 12, 12, 7, 13, 8, 8, 8, 8, 12, 6, 24,
        )
        size = 2 + sum(size for bit, size in enumerate(field_sizes) if int(flags) & (1 << bit))
        if size > 0xFF:
            raise ValueError(
                f"selected realtime fields require {size} bytes; the protocol limit is 255"
            )
        return size

    @staticmethod
    def _parse_realtime_data_custom(
        flags: RealtimeDataCustomFlag, raw_payload: bytes
    ) -> RealtimeDataCustom:
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

        parsers = (
            lambda: read("<3h"), lambda: read("<3h"), lambda: read("<3h"),
            lambda: read("<3h"), lambda: read("<3h"), lambda: read("<6h"),
            lambda: read("<6f"), lambda: read("<18h"), lambda: read("<3h"),
            lambda: read("<hhf"), lambda: read_bytes(26), lambda: read_bytes(9),
            lambda: read("<3f"), lambda: read("<10f"), lambda: read("<10h"),
            lambda: read_bytes(46), lambda: read("<3h"), lambda: read("<3i"),
            lambda: read("<3i"), lambda: read("<3HB"), lambda: read_bytes(13),
            lambda: read_bytes(8), lambda: read_bytes(8), lambda: read_bytes(8),
            lambda: read("<4H"), lambda: read("<6h"), lambda: read("<3h"),
            lambda: read("<6i"),
        )
        for bit, parser in enumerate(parsers):
            flag = RealtimeDataCustomFlag(1 << bit)
            if flags & flag:
                fields[flag] = parser()
        if offset != len(raw_payload):
            raise NativeError(
                "REALTIME_DATA_CUSTOM response length does not match the requested flags."
            )
        return RealtimeDataCustom(
            flags=flags,
            timestamp_ms=timestamp_ms,
            fields=MappingProxyType(fields),
            raw_payload=raw_payload,
        )

    @staticmethod
    def _make_realtime_data_3(result) -> RealtimeData3:
        return RealtimeData3(
            axis_rtd=tuple(
                AxisRealtimeData(acc_data=axis.acc_data, gyro_data=axis.gyro_data)
                for axis in result.axis_rtd
            ),
            serial_error_count=result.serial_error_count,
            system_error=result.system_error,
            system_sub_error=result.system_sub_error,
            reserved=bytes(result.reserved),
            rc_roll=result.rc_roll,
            rc_pitch=result.rc_pitch,
            rc_yaw=result.rc_yaw,
            rc_cmd=result.rc_cmd,
            ext_fc_roll=result.ext_fc_roll,
            ext_fc_pitch=result.ext_fc_pitch,
            imu_angle=tuple(result.imu_angle),
            frame_imu_angle=tuple(result.frame_imu_angle),
            target_angle=tuple(result.target_angle),
            cycle_time=result.cycle_time,
            i2c_error_count=result.i2c_error_count,
            error_code=result.error_code,
            bat_level=result.bat_level,
            rt_data_flags=result.rt_data_flags,
            cur_imu=result.cur_imu,
            cur_profile=result.cur_profile,
            motor_power=tuple(result.motor_power),
        )


    def get_board_info(self) -> BoardInfo:
        self._ensure_open()
        result = self._native.get_board_info(self._device)
        return BoardInfo(
            board_ver=result.board_ver,
            firmware_ver=result.firmware_ver,
            state_flags=result.state_flags,
            board_features=result.board_features,
            connection_flag=result.connection_flag,
            firmware_extra_id=result.firmware_extra_id,
            board_features_ext=result.board_features_ext,
            main_imu_sensor_model=result.main_imu_sensor_model,
            frame_imu_sensor_model=result.frame_imu_sensor_model,
            build_number=result.build_number,
            base_firmware_ver=result.base_firmware_ver,
        )

    def get_boardInfo(self) -> BoardInfo:
        return self.get_board_info()

    def get_board_info_3(self) -> BoardInfo3:
        self._ensure_open()
        result = self._native.get_board_info_3(self._device)

        return BoardInfo3(
            device_id=bytes(result.device_id),
            mcu_id=bytes(result.mcu_id),
            eeprom_size=result.eeprom_size,
            script_slot_sizes=(
                result.script_slot_1_size,
                result.script_slot_2_size,
                result.script_slot_3_size,
                result.script_slot_4_size,
                result.script_slot_5_size,
                result.script_slot_6_size,
                result.script_slot_7_size,
                result.script_slot_8_size,
                result.script_slot_9_size,
                result.script_slot_10_size,
            ),
            profile_set_slots=result.profile_set_slots,
            profile_set_current=result.profile_set_current,
            flash_size_pages=result.flash_size,
            imu_calib_info=bytes(result.imu_calib_info),
            hardware_flags=result.hardware_flags,
            board_features_ext2=result.board_features_ext2,
            can_driver_main_limit=result.can_driver_main_limit,
            can_driver_aux_limit=result.can_driver_aux_limit,
            adjustable_variables_total=result.adjustable_variables_total,
        )


    # Compatibility entry point for supported request and action commands.
    def execute(
        self, command: Command | int, **kwargs
    ) -> (
        Angles
        | AnglesExt
        | BoardInfo
        | BoardInfo3
        | RealtimeData3
        | RealtimeData4
        | RealtimeDataCustom
        | None
    ):
        command = Command(command)

        def read(method):
            if kwargs:
                names = ", ".join(kwargs)
                raise TypeError(f"{command.name} does not accept keyword arguments: {names}")
            return method()

        if command is Command.CMD_GET_ANGLES:
            return read(self.get_angles)
        if command is Command.CMD_GET_ANGLES_EXT:
            return read(self.get_angles_ext)
        if command is Command.CMD_REALTIME_DATA:
            return read(self.get_realtime_data)
        if command is Command.CMD_REALTIME_DATA_3:
            return read(self.get_realtime_data_3)
        if command is Command.CMD_REALTIME_DATA_4:
            return read(self.get_realtime_data_4)
        if command is Command.CMD_REALTIME_DATA_CUSTOM:
            try:
                flags = kwargs.pop("flags")
            except KeyError as error:
                raise TypeError("CMD_REALTIME_DATA_CUSTOM requires flags=...") from error
            if kwargs:
                names = ", ".join(kwargs)
                raise TypeError(
                    f"CMD_REALTIME_DATA_CUSTOM does not accept keyword arguments: {names}"
                )
            return self.get_realtime_data_custom(flags)
        if command is Command.CMD_BOARD_INFO:
            return read(self.get_board_info)
        if command is Command.CMD_BOARD_INFO_3:
            return read(self.get_board_info_3)
        if command is Command.CMD_RUN_SCRIPT:
            return self.run_script(**kwargs)
        if command is Command.CMD_MOTORS_ON:
            return read(self.motors_on)
        if command is Command.CMD_MOTORS_OFF:
            return self.motors_off(**kwargs)
        raise NotImplementedError(f"Command {command.name} is not implemented")


    def close(self) -> None:
        if not self._closed:
            self._native.close(self._device)
            self._closed = True
            self._debug_script_slot = None


    def _ensure_open(self) -> None:
        if self._closed:
            raise NativeError("The SimpleBGC connection is already closed.")


    def __enter__(self) -> "SimpleBGC":
        self._ensure_open()
        return self


    def __exit__(self, exception_type, exception, traceback) -> None:
        self.close()
