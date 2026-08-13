from __future__ import annotations

import ctypes
import struct
from math import isfinite
from types import MappingProxyType
from time import sleep

from .commands import Command, ResponseCommand
from .native import NativeControlAxisConfig, NativeControlConfig, NativeError, NativeLibrary
from .types import (
    Angles,
    AnglesExt,
    AdjustableVariable,
    Axis3,
    AxisGAE,
    AxisRealtimeData,
    BoardInfo,
    BoardInfo3,
    ControlAxis,
    ControlAxisConfig,
    ControlConfig,
    ControlConfigFlag,
    ControlFlag,
    ControlMode,
    CommandConfirmation,
    ConfirmationStatus,
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


    def get_angles(self) -> Angles:
        """ Read IMU, angle, speed for axes3. """

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
        """ Extended meanings of get_angles, use axesGAE. """

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


    def motors_on(self) -> None:
        """ Start motors. Make sure the rig has
        enough clearance before calling it and that voltage is applied to the motors (not via the read port). """

        self._ensure_open()
        self._native.motors_on(self._device)


    def motors_off(self, mode: MotorsOffMode = MotorsOffMode.SAFE_STOP) -> None:
        """ Stop motors, using the selected stopping mode. Has 3 mode:
        NORMAL, BREAK and SAFE_STOP. SAFE_STOP is the default recommended by SerialAPI. Firmware before
        2.68b7 ignores the mode byte. """

        self._ensure_open()
        try:
            selected_mode = MotorsOffMode(mode)
        except ValueError as error:
            raise ValueError("mode must be a MotorsOffMode value (0, 1, or 2)") from error
        self._native.motors_off(self._device, int(selected_mode))


    def control(
        self,
        axes: tuple[ControlAxis, ControlAxis, ControlAxis],
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """ Send CMD_CONTROL for roll, pitch, and yaw in that order. """

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
            speeds.append(self._control_speed_to_units(axis.speed, mode))
            angles.append(self._control_angle_to_units(axis.angle, mode))

        confirmation = self._native.control(
            self._device,
            tuple(modes),
            tuple(speeds),
            tuple(angles),
            need_confirmation=need_confirmation,
        )
        if confirmation is None:
            return None

        return CommandConfirmation(
            command_id=confirmation.command_id,
            status=ConfirmationStatus(confirmation.status),
            command_data=confirmation.command_data,
            error_code=confirmation.error_code,
            error_data=bytes(confirmation.error_data),
        )

    def configure_control(
        self,
        config: ControlConfig | None = None,
        *,
        confirm_control: bool | None = None,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """ Apply CMD_CONTROL_CONFIG rules. """

        self._ensure_open()
        if config is None:
            config = ControlConfig()
        if not isinstance(config, ControlConfig):
            raise TypeError("config must be a ControlConfig")

        flags = self._validate_uint(config.flags, "flags", 0xFFFF)
        if confirm_control is not None:
            if type(confirm_control) is not bool:
                raise TypeError("confirm_control must be bool or None")
            if confirm_control:
                flags &= ~int(ControlConfigFlag.NO_CONFIRM)
            else:
                flags |= int(ControlConfigFlag.NO_CONFIRM)

        priorities = self._validate_int_tuple(
            config.channel_priorities, "channel_priorities", 5, 0xFF
        )
        if len(config.axes) != 3 or any(
            not isinstance(axis, ControlAxisConfig) for axis in config.axes
        ):
            raise TypeError("config.axes must contain ControlAxisConfig for roll, pitch, and yaw")
        native_axes = (NativeControlAxisConfig * 3)(
            *(
                NativeControlAxisConfig(
                    angle_lpf=self._validate_uint(axis.angle_lpf, "angle_lpf", 0xFF),
                    speed_lpf=self._validate_uint(axis.speed_lpf, "speed_lpf", 0xFF),
                    rc_lpf=self._validate_uint(axis.rc_lpf, "rc_lpf", 0xFF),
                    acceleration_limit=self._validate_uint(
                        axis.acceleration_limit, "acceleration_limit", 0xFFFF
                    ),
                    jerk_slope=self._validate_uint(axis.jerk_slope, "jerk_slope", 0xFF),
                )
                for axis in config.axes
            )
        )
        native_config = NativeControlConfig(
            timeout_ms=self._validate_uint(config.timeout_ms, "timeout_ms", 0xFFFF),
            channel_priorities=(ctypes.c_uint8 * 5)(*priorities),
            axis=native_axes,
            rc_expo_rate=self._validate_uint(config.rc_expo_rate, "rc_expo_rate", 0xFF),
            flags=flags,
            euler_order=self._validate_uint(config.euler_order, "euler_order", 0xFF),
        )
        return self._make_confirmation(
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
        """Alias for :meth:`configure_control`."""

        return self.configure_control(
            config,
            confirm_control=confirm_control,
            need_confirmation=need_confirmation,
        )

    @staticmethod
    def _validate_uint(value: object, name: str, maximum: int) -> int:
        if (not isinstance(value, int) or isinstance(value, bool) or
                not 0 <= value <= maximum):
            raise ValueError(f"{name} must be an integer in range 0..{maximum}")
        return int(value)

    @classmethod
    def _validate_int_tuple(
        cls, values: object, name: str, length: int, maximum: int
    ) -> tuple[int, ...]:
        if not isinstance(values, tuple) or len(values) != length:
            raise ValueError(f"{name} must be a tuple with {length} entries")
        return tuple(cls._validate_uint(value, name, maximum) for value in values)


    def get_adj_vars(self, ids: object) -> tuple[AdjustableVariable, ...]:
        """ Read integer adjustable variables by their firmware IDs.

        Up to 40 distinct IDs are accepted in one request. Returned values are
        raw signed 32-bit values and preserve the requested ID order.
        """

        self._ensure_open()
        normalized_ids = self._normalize_adj_var_ids(ids)
        result = self._native.get_adj_vars(self._device, normalized_ids)
        return tuple(AdjustableVariable(id=item.id, value=item.value) for item in result)

    def get_adj_var(self, id: int) -> AdjustableVariable:
        """ Read one integer adjustable variable. """

        return self.get_adj_vars((id,))[0]

    def set_adj_vars(
        self,
        variables: object,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """ Set integer adjustable variables in RAM.

        This command can affect gimbal behavior immediately and is not retried.
        Values are not persisted across a reboot.
        """

        self._ensure_open()
        normalized_variables = self._normalize_adj_vars(variables)
        from .native import NativeAdjustableVariable

        confirmation = self._native.set_adj_vars(
            self._device,
            tuple(
                NativeAdjustableVariable(id=item.id, value=item.value)
                for item in normalized_variables
            ),
            need_confirmation=need_confirmation,
        )
        if confirmation is None:
            return None
        return CommandConfirmation(
            command_id=confirmation.command_id,
            status=ConfirmationStatus(confirmation.status),
            command_data=confirmation.command_data,
            error_code=confirmation.error_code,
            error_data=bytes(confirmation.error_data),
        )

    def set_adj_var(
        self, id: int, value: int, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """ Set one integer adjustable variable in RAM. """

        return self.set_adj_vars(
            (AdjustableVariable(id=id, value=value),),
            need_confirmation=need_confirmation,
        )

    def save_adj_vars(
        self, ids: object, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Persist selected adjustable variables to EEPROM with CMD_SAVE_PARAMS_3.

        The IDs identify values already changed with :meth:`set_adj_vars`.
        EEPROM writes are not retried because a failed exchange may still have
        committed the change. On controllers that do not send CMD_CONFIRM,
        keep ``need_confirmation`` set to its default ``False``.
        """

        self._ensure_open()
        normalized_ids = self._normalize_adj_var_ids(ids, maximum=102)
        return self._make_confirmation(
            self._native.save_adj_vars(
                self._device,
                normalized_ids,
                need_confirmation=need_confirmation,
            )
        )

    def save_all_adj_vars(
        self, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Persist all currently active adjustable variables to EEPROM.

        Prefer :meth:`save_adj_vars` when only a known subset was changed.
        """

        self._ensure_open()
        return self._make_confirmation(
            self._native.save_adj_vars(
                self._device,
                None,
                need_confirmation=need_confirmation,
            )
        )

    @staticmethod
    def _make_confirmation(
        confirmation: object,
    ) -> CommandConfirmation | None:
        if confirmation is None:
            return None
        return CommandConfirmation(
            command_id=confirmation.command_id,
            status=ConfirmationStatus(confirmation.status),
            command_data=confirmation.command_data,
            error_code=confirmation.error_code,
            error_data=bytes(confirmation.error_data),
        )

    @staticmethod
    def _normalize_adj_var_ids(ids: object, *, maximum: int = 40) -> tuple[int, ...]:
        try:
            values = tuple(ids)  # type: ignore[arg-type]
        except TypeError as error:
            raise TypeError("ids must be an iterable of adjustable-variable IDs") from error
        if not 1 <= len(values) <= maximum:
            raise ValueError(f"ids must contain from 1 to {maximum} entries")
        if any(type(id) is not int or not 0 <= id <= 0xFF for id in values):
            raise ValueError("each adjustable-variable ID must be an integer in range 0..255")
        if len(set(values)) != len(values):
            raise ValueError("adjustable-variable IDs must not repeat in one request")
        return values

    @classmethod
    def _normalize_adj_vars(cls, variables: object) -> tuple[AdjustableVariable, ...]:
        try:
            values = tuple(variables)  # type: ignore[arg-type]
        except TypeError as error:
            raise TypeError("variables must be an iterable of AdjustableVariable") from error
        if not 1 <= len(values) <= 40:
            raise ValueError("variables must contain from 1 to 40 entries")
        if any(not isinstance(item, AdjustableVariable) for item in values):
            raise TypeError("each item must be an AdjustableVariable")
        ids = cls._normalize_adj_var_ids(tuple(item.id for item in values))
        if any(type(item.value) is not int or not -0x80000000 <= item.value <= 0x7FFFFFFF for item in values):
            raise ValueError("each adjustable-variable value must be a signed 32-bit integer")
        # ``ids`` performs validation and duplicate detection; retain original order.
        return tuple(AdjustableVariable(id=id, value=item.value) for id, item in zip(ids, values))

    @staticmethod
    def _control_speed_to_units(speed_degrees_per_second: float, mode: int) -> int:
        """ Convert degrees/s to sbgcAxisC_t.speed. """
        scale = 1000.0 if mode & int(ControlFlag.HIGH_RES_SPEED) else 1 / 0.1220740379
        value = round(speed_degrees_per_second * scale)
        if not -0x8000 <= value <= 0x7FFF:
            raise ValueError(
                "axis speed is outside the range supported by CMD_CONTROL"
            )
        return value

    @staticmethod
    def _control_angle_to_units(angle_degrees: float, mode: int) -> int:
        """ Convert degrees to sbgcAxisC_t.angle, except raw RC modes. """
        control_mode = ControlMode(mode & 0x0F)
        if control_mode in (ControlMode.RC, ControlMode.RC_HIGH_RES):
            if not angle_degrees.is_integer():
                raise ValueError("RC mode requires an integral raw RC value in angle")
            value = int(angle_degrees)
        else:
            value = round(angle_degrees * 16384.0 / 360.0)
        if not -0x8000 <= value <= 0x7FFF:
            raise ValueError(
                "axis angle is outside the range supported by CMD_CONTROL"
            )
        return value


    def run_script(self, slot: int = 1, *, debug: bool = False) -> None:
        """ Launches the script from the selected slot, with or without debugging. """

        self._ensure_open()
        if not 1 <= slot <= self._script_slot_count:
            raise ValueError(f"slot must be in range 1..{self._script_slot_count}")
        self._native.run_script(self._device, 2 if debug else 1, slot - 1)
        self._debug_script_slot = slot if debug else None


    def stop_script(self, slot: int = 1) -> None:
        """ Stops the script """

        self._ensure_open()
        if not 1 <= slot <= self._script_slot_count:
            raise ValueError(f"slot must be in range 1..{self._script_slot_count}")
        self._native.run_script(self._device, 0, slot - 1)
        if self._debug_script_slot == slot:
            self._debug_script_slot = None

    def read_script_debug_info(self, timeout: float = 1.0) -> ScriptDebugInfo:
        """ Read debug info into a variable. Print that variable to see debug info. """

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
        """ Read legacy CMD_REALTIME_DATA (available on older firmware). """

        self._ensure_open()
        return self._make_realtime_data_3(self._native.get_realtime_data(self._device))


    def get_realtime_data_3(self) -> RealtimeData3:
        """ Read the 63-byte CMD_REALTIME_DATA_3 response. """

        self._ensure_open()
        return self._make_realtime_data_3(self._native.get_realtime_data_3(self._device))


    def get_realtime_data_4(self) -> RealtimeData4:
        """ Read the 124-byte CMD_REALTIME_DATA_4 response. """

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
        """ Request only the realtime fields selected by flags. """

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
        """ Reads board info into a variable. """

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


    def get_board_info_3(self) -> BoardInfo3:
        """ Reads extended parameters of board info into a variable. """

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
        | tuple[AdjustableVariable, ...]
        | CommandConfirmation
        | None
    ):
        """ Compatibility entry point for supported request and action commands. """

        if isinstance(command, ResponseCommand):
            raise ValueError(
                f"{command.name} is sent by the board and cannot be executed."
            )
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
        if command is Command.CMD_GET_ADJ_VARS_VAL:
            try:
                ids = kwargs.pop("ids")
            except KeyError as error:
                raise TypeError("CMD_GET_ADJ_VARS_VAL requires ids=(...)") from error
            if kwargs:
                names = ", ".join(kwargs)
                raise TypeError(f"CMD_GET_ADJ_VARS_VAL does not accept keyword arguments: {names}")
            return self.get_adj_vars(ids)
        if command is Command.CMD_SET_ADJ_VARS_VAL:
            try:
                variables = kwargs.pop("variables")
            except KeyError as error:
                raise TypeError(
                    "CMD_SET_ADJ_VARS_VAL requires variables=(AdjustableVariable(...), ...)"
                ) from error
            need_confirmation = kwargs.pop("need_confirmation", False)
            if kwargs:
                names = ", ".join(kwargs)
                raise TypeError(f"CMD_SET_ADJ_VARS_VAL does not accept keyword arguments: {names}")
            return self.set_adj_vars(
                variables, need_confirmation=need_confirmation
            )
        if command is Command.CMD_SAVE_PARAMS_3:
            ids = kwargs.pop("ids", None)
            all_active = kwargs.pop("all_active", False)
            need_confirmation = kwargs.pop("need_confirmation", False)
            if kwargs:
                names = ", ".join(kwargs)
                raise TypeError(f"CMD_SAVE_PARAMS_3 does not accept keyword arguments: {names}")
            if all_active:
                if ids is not None:
                    raise TypeError("CMD_SAVE_PARAMS_3 accepts either ids=... or all_active=True")
                return self.save_all_adj_vars(need_confirmation=need_confirmation)
            if ids is None:
                raise TypeError(
                    "CMD_SAVE_PARAMS_3 requires ids=(...) or all_active=True"
                )
            return self.save_adj_vars(ids, need_confirmation=need_confirmation)
        if command is Command.CMD_RUN_SCRIPT:
            return self.run_script(**kwargs)
        if command is Command.CMD_MOTORS_ON:
            return read(self.motors_on)
        if command is Command.CMD_MOTORS_OFF:
            return self.motors_off(**kwargs)
        if command is Command.CMD_CONTROL:
            try:
                axes = kwargs.pop("axes")
            except KeyError as error:
                raise TypeError("CMD_CONTROL requires axes=(roll, pitch, yaw)") from error
            need_confirmation = kwargs.pop("need_confirmation", False)
            if kwargs:
                names = ", ".join(kwargs)
                raise TypeError(f"CMD_CONTROL does not accept keyword arguments: {names}")
            return self.control(axes, need_confirmation=need_confirmation)
        if command is Command.CMD_CONTROL_CONFIG:
            config = kwargs.pop("config", None)
            confirm_control = kwargs.pop("confirm_control", None)
            need_confirmation = kwargs.pop("need_confirmation", False)
            if kwargs:
                names = ", ".join(kwargs)
                raise TypeError(f"CMD_CONTROL_CONFIG does not accept keyword arguments: {names}")
            return self.configure_control(
                config,
                confirm_control=confirm_control,
                need_confirmation=need_confirmation,
            )
        raise NotImplementedError(f"Command {command.name} is not implemented")


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
