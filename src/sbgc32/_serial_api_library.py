from __future__ import annotations

import ctypes
import stat
import sys
from enum import IntEnum
from pathlib import Path


class NativeError(RuntimeError):
    """Error returned by the native SimpleBGC bridge."""


class NativeStatus(IntEnum):
    OK = 0
    ERROR = -1
    INVALID_ARGUMENT = -2
    NOT_CONNECTED = -3
    OPEN_FAILED = -4
    COMMUNICATION_ERROR = -5
    MODULE_DISABLED = -6
    CONFIRMATION_DISABLED = -7


class NativeAxis3(ctypes.Structure):
    _fields_ = [
        ("roll", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("yaw", ctypes.c_float),
    ]


class NativeAngles(ctypes.Structure):
    _fields_ = [
        ("imu", NativeAxis3),
        ("target", NativeAxis3),
        ("target_speed", NativeAxis3),
    ]


class NativeAxisGAE(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("imu_angle", ctypes.c_int16),
        ("target_angle", ctypes.c_int16),
        ("frame_cam_angle", ctypes.c_int32),
        ("reserved", ctypes.c_uint8 * 10),
    ]


class NativeAnglesExt(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("axis_gae", NativeAxisGAE * 3),
    ]


class NativeScriptDebugInfo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("current_command_counter", ctypes.c_uint16),
        ("error_code", ctypes.c_uint8),
    ]


class NativeAutoPid(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("profile_id", ctypes.c_uint8),
        ("config_flags", ctypes.c_uint8),
        ("gain_vs_stability", ctypes.c_uint8),
        ("momentum", ctypes.c_uint8),
        ("action", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 14),
    ]


class NativeAutoPid2Axis(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("axis_flags", ctypes.c_uint8),
        ("gain", ctypes.c_uint8),
        ("stimulus_gain", ctypes.c_uint16),
        ("effective_frequency", ctypes.c_uint8),
        ("problem_frequency", ctypes.c_uint8),
        ("problem_margin", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 6),
    ]


class NativeAutoPid2(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("action", ctypes.c_uint8),
        ("command_flags", ctypes.c_uint16),
        ("reserved1", ctypes.c_uint8 * 8),
        ("config_version", ctypes.c_uint8),
        ("axis", NativeAutoPid2Axis * 3),
        ("general_flags", ctypes.c_uint16),
        ("reserved3", ctypes.c_uint8),
        ("test_frequency_from", ctypes.c_uint8),
        ("test_frequency_to", ctypes.c_uint8),
        ("multi_position_flags", ctypes.c_uint8),
        ("multi_position_angle", ctypes.c_int8 * 4),
        ("reserved4", ctypes.c_uint8 * 12),
    ]


class NativeAutoPidAxisState(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("tracking_error", ctypes.c_float),
        ("reserved", ctypes.c_uint8 * 6),
    ]


class NativeAutoPidState(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("p", ctypes.c_uint8 * 3),
        ("i", ctypes.c_uint8 * 3),
        ("d", ctypes.c_uint8 * 3),
        ("lpf_frequency", ctypes.c_uint16 * 3),
        ("iteration_count", ctypes.c_uint16),
        ("axis", NativeAutoPidAxisState * 3),
        ("reserved", ctypes.c_uint8 * 10),
    ]


class NativeSyncMotors(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("axis", ctypes.c_uint8),
        ("power", ctypes.c_uint8),
        ("time_ms", ctypes.c_uint16),
        ("angle", ctypes.c_uint16),
    ]


class NativeStateVars(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("step_signal_vars", ctypes.c_uint8 * 6),
        ("sub_error", ctypes.c_uint8),
        ("max_acc", ctypes.c_uint8),
        ("work_time", ctypes.c_uint32),
        ("startup_count", ctypes.c_uint16),
        ("max_current", ctypes.c_uint16),
        ("imu_temp_min", ctypes.c_uint8),
        ("imu_temp_max", ctypes.c_uint8),
        ("mcu_temp_min", ctypes.c_uint8),
        ("mcu_temp_max", ctypes.c_uint8),
        ("shock_count", ctypes.c_uint8 * 4),
        ("energy_time", ctypes.c_uint32),
        ("energy", ctypes.c_float),
        ("avg_current_time", ctypes.c_uint32),
        ("avg_current", ctypes.c_float),
        ("reserved", ctypes.c_uint8 * 152),
    ]


class NativeConfirmation(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("command_id", ctypes.c_uint8),
        ("status", ctypes.c_uint8),
        ("command_data", ctypes.c_uint16),
        ("error_code", ctypes.c_uint8),
        ("error_data", ctypes.c_uint8 * 4),
    ]


class NativeDataStreamInterval(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("command_id", ctypes.c_uint8),
        ("interval_ms", ctypes.c_uint16),
        ("config", ctypes.c_uint8 * 8),
        ("sync_to_data", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 9),
    ]
	
    
class NativeDebugVarInfo3(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("name_length", ctypes.c_uint8), 
        ("name", ctypes.POINTER(ctypes.c_char)),
        ("type", ctypes.c_int),
        ("value", ctypes.c_uint32),
    ]


class NativeDebugVarValues3(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("debug_var_info_3", ctypes.POINTER(NativeDebugVarInfo3)),
        ("mask", ctypes.POINTER(ctypes.c_uint32)),
        ("mask_count", ctypes.c_uint8),
    ]


class NativeAdjustableVariable(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_uint8),
        ("value", ctypes.c_int32),
    ]


class NativeControlAxisConfig(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("angle_lpf", ctypes.c_uint8),
        ("speed_lpf", ctypes.c_uint8),
        ("rc_lpf", ctypes.c_uint8),
        ("acceleration_limit", ctypes.c_uint16),
        ("jerk_slope", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8),
    ]


class NativeControlConfig(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("timeout_ms", ctypes.c_uint16),
        ("channel_priorities", ctypes.c_uint8 * 5),
        ("axis", NativeControlAxisConfig * 3),
        ("rc_expo_rate", ctypes.c_uint8),
        ("flags", ctypes.c_uint16),
        ("euler_order", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 9),
    ]


class NativeAxisRealtimeData(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("acc_data", ctypes.c_int16),
        ("gyro_data", ctypes.c_int16),
    ]


class NativeRealtimeData(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("axis_rtd", NativeAxisRealtimeData * 3),
        ("serial_error_count", ctypes.c_uint16),
        ("system_error", ctypes.c_uint16),
        ("system_sub_error", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("rc_roll", ctypes.c_int16),
        ("rc_pitch", ctypes.c_int16),
        ("rc_yaw", ctypes.c_int16),
        ("rc_cmd", ctypes.c_int16),
        ("ext_fc_roll", ctypes.c_int16),
        ("ext_fc_pitch", ctypes.c_int16),
        ("imu_angle", ctypes.c_int16 * 3),
        ("frame_imu_angle", ctypes.c_int16 * 3),
        ("target_angle", ctypes.c_int16 * 3),
        ("cycle_time", ctypes.c_uint16),
        ("i2c_error_count", ctypes.c_uint16),
        ("error_code", ctypes.c_uint8),
        ("bat_level", ctypes.c_uint16),
        ("rt_data_flags", ctypes.c_uint8),
        ("cur_imu", ctypes.c_uint8),
        ("cur_profile", ctypes.c_uint8),
        ("motor_power", ctypes.c_uint8 * 3),
        ("frame_cam_angle", ctypes.c_int16 * 3),
        ("reserved1", ctypes.c_uint8),
        ("balance_error", ctypes.c_int16 * 3),
        ("current", ctypes.c_uint16),
        ("mag_data", ctypes.c_int16 * 3),
        ("imu_temperature", ctypes.c_int8),
        ("frame_imu_temperature", ctypes.c_int8),
        ("imu_g_error", ctypes.c_uint8),
        ("imu_h_error", ctypes.c_uint8),
        ("motor_out", ctypes.c_int16 * 3),
        ("calib_mode", ctypes.c_uint8),
        ("can_imu_ext_sens_error", ctypes.c_uint8),
        ("actual_angle", ctypes.c_int16 * 3),
        ("system_state_flags", ctypes.c_uint32),
        ("reserved2", ctypes.c_uint8 * 18),
    ]


class NativeBoardInfo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("board_ver", ctypes.c_uint8),
        ("firmware_ver", ctypes.c_uint16),
        ("state_flags", ctypes.c_uint8),
        ("board_features", ctypes.c_uint16),
        ("connection_flag", ctypes.c_uint8),
        ("firmware_extra_id", ctypes.c_uint32),
        ("board_features_ext", ctypes.c_uint16),
        ("main_imu_sensor_model", ctypes.c_uint8),
        ("frame_imu_sensor_model", ctypes.c_uint8),
        ("build_number", ctypes.c_uint8),
        ("base_firmware_ver", ctypes.c_uint16),
    ]


class NativeBoardInfo3(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("device_id", ctypes.c_uint8 * 9),
        ("mcu_id", ctypes.c_uint8 * 12),
        ("eeprom_size", ctypes.c_uint32),

        ("script_slot_1_size", ctypes.c_uint16),
        ("script_slot_2_size", ctypes.c_uint16),
        ("script_slot_3_size", ctypes.c_uint16),
        ("script_slot_4_size", ctypes.c_uint16),
        ("script_slot_5_size", ctypes.c_uint16),

        ("profile_set_slots", ctypes.c_uint8),
        ("profile_set_current", ctypes.c_uint8),
        ("flash_size", ctypes.c_uint8),
        ("imu_calib_info", ctypes.c_uint8 * 2),

        ("script_slot_6_size", ctypes.c_uint16),
        ("script_slot_7_size", ctypes.c_uint16),
        ("script_slot_8_size", ctypes.c_uint16),
        ("script_slot_9_size", ctypes.c_uint16),
        ("script_slot_10_size", ctypes.c_uint16),

        ("hardware_flags", ctypes.c_uint16),
        ("board_features_ext2", ctypes.c_uint32),
        ("can_driver_main_limit", ctypes.c_uint8),
        ("can_driver_aux_limit", ctypes.c_uint8),
        ("adjustable_variables_total", ctypes.c_uint8),
    ]


def _library_name(stem: str = "sbgc_python") -> str:
    if sys.platform == "win32":
        return f"{stem}.dll"
    if sys.platform == "darwin":
        return f"lib{stem}.dylib"
    return f"lib{stem}.so"


class SerialApiLibrary:

    def __init__(
        self,
        library_path: str | Path | None = None,
        *,
        library_stem: str = "sbgc_python",
    ) -> None:
        if library_path is None:
            library_path = Path(__file__).parent / "_native" / _library_name(library_stem)

        try:
            self._library = ctypes.CDLL(str(library_path))
        except OSError as error:
            raise NativeError(
                f"Native SimpleBGC library was not found at {library_path}. "
                "Build it with CMake before using the package."
            ) from error

        self._configure_functions()

    def _configure_functions(self) -> None:
        lib = self._library
        lib.sbgc_py_close.argtypes = [ctypes.c_void_p]
        lib.sbgc_py_close.restype = None
        lib.sbgc_py_recover.argtypes = [ctypes.c_void_p]
        lib.sbgc_py_recover.restype = ctypes.c_int


        lib.sbgc_py_get_angles.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAngles)
        ]
        lib.sbgc_py_get_angles.restype = ctypes.c_int


        lib.sbgc_py_get_angles_ext.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAnglesExt)
        ]
        lib.sbgc_py_get_angles_ext.restype = ctypes.c_int


        lib.sbgc_py_get_board_info.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeBoardInfo),
        ]
        lib.sbgc_py_get_board_info.restype = ctypes.c_int


        lib.sbgc_py_get_board_info_3.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeBoardInfo3),
        ]
        lib.sbgc_py_get_board_info_3.restype = ctypes.c_int


        lib.sbgc_py_reset.argtypes = [ctypes.c_void_p, ctypes.c_uint8, ctypes.c_uint16]
        lib.sbgc_py_reset.restype = ctypes.c_int
        lib.sbgc_py_expect_reset.argtypes = [ctypes.c_void_p]
        lib.sbgc_py_expect_reset.restype = ctypes.c_int


        lib.sbgc_py_motors_on.argtypes = [ctypes.c_void_p]
        lib.sbgc_py_motors_on.restype = ctypes.c_int


        lib.sbgc_py_motors_off.argtypes = [ctypes.c_void_p, ctypes.c_uint8]
        lib.sbgc_py_motors_off.restype = ctypes.c_int


        lib.sbgc_py_play_beeper.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint16,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint16),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_play_beeper.restype = ctypes.c_int


        lib.sbgc_py_execute_menu.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_execute_menu.restype = ctypes.c_int


        lib.sbgc_py_control.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_int16),
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_control.restype = ctypes.c_int


        lib.sbgc_py_control_config.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeControlConfig),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_control_config.restype = ctypes.c_int


        lib.sbgc_py_get_adj_vars.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
            ctypes.POINTER(NativeAdjustableVariable),
        ]
        lib.sbgc_py_get_adj_vars.restype = ctypes.c_int


        lib.sbgc_py_set_adj_vars.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAdjustableVariable),
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_set_adj_vars.restype = ctypes.c_int


        lib.sbgc_py_save_adj_vars.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_save_adj_vars.restype = ctypes.c_int


        lib.sbgc_py_run_script.argtypes = [ctypes.c_void_p, ctypes.c_uint8, ctypes.c_uint8]
        lib.sbgc_py_run_script.restype = ctypes.c_int
        lib.sbgc_py_read_script_debug_info.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeScriptDebugInfo),
        ]
        lib.sbgc_py_read_script_debug_info.restype = ctypes.c_int


        lib.sbgc_py_tune_auto_pid.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(NativeAutoPid), ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_tune_auto_pid.restype = ctypes.c_int


        lib.sbgc_py_break_auto_pid.argtypes = [
            ctypes.c_void_p, ctypes.c_uint8, ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_break_auto_pid.restype = ctypes.c_int


        lib.sbgc_py_tune_auto_pid2.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(NativeAutoPid2), ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_tune_auto_pid2.restype = ctypes.c_int


        lib.sbgc_py_read_auto_pid_state.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(NativeAutoPidState),
        ]
        lib.sbgc_py_read_auto_pid_state.restype = ctypes.c_int


        lib.sbgc_py_synchronize_motors.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(NativeSyncMotors), ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_synchronize_motors.restype = ctypes.c_int


        lib.sbgc_py_request_motor_state.argtypes = [
            ctypes.c_void_p, ctypes.c_uint8, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint16,
        ]
        lib.sbgc_py_request_motor_state.restype = ctypes.c_int


        lib.sbgc_py_read_motor_state.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint16,
        ]
        lib.sbgc_py_read_motor_state.restype = ctypes.c_int


        lib.sbgc_py_set_boot_mode.argtypes = [
            ctypes.c_void_p, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint16,
        ]
        lib.sbgc_py_set_boot_mode.restype = ctypes.c_int


        lib.sbgc_py_write_state_vars.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(NativeStateVars), ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_write_state_vars.restype = ctypes.c_int


        lib.sbgc_py_read_state_vars.argtypes = [ctypes.c_void_p, ctypes.POINTER(NativeStateVars)]
        lib.sbgc_py_read_state_vars.restype = ctypes.c_int


        lib.sbgc_py_set_debug_port.argtypes = [
            ctypes.c_void_p, ctypes.c_uint8, ctypes.c_uint32, ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_set_debug_port.restype = ctypes.c_int


        lib.sbgc_py_read_debug_port.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint16,
        ]
        lib.sbgc_py_read_debug_port.restype = ctypes.c_int


        lib.sbgc_py_set_api_virtual_channels.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_set_api_virtual_channels.restype = ctypes.c_int


        lib.sbgc_py_get_realtime_data_3.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeRealtimeData),
        ]
        lib.sbgc_py_get_realtime_data_3.restype = ctypes.c_int


        lib.sbgc_py_get_realtime_data_4.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeRealtimeData),
        ]
        lib.sbgc_py_get_realtime_data_4.restype = ctypes.c_int


        lib.sbgc_py_get_realtime_data_custom.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_get_realtime_data_custom.restype = ctypes.c_int


        lib.sbgc_py_read_rc_inputs.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_int16),
        ]
        lib.sbgc_py_read_rc_inputs.restype = ctypes.c_int


        lib.sbgc_py_start_data_stream.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeDataStreamInterval),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_start_data_stream.restype = ctypes.c_int


        lib.sbgc_py_stop_data_stream.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeDataStreamInterval),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_stop_data_stream.restype = ctypes.c_int


        lib.sbgc_py_read_data_stream.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_read_data_stream.restype = ctypes.c_int


        lib.sbgc_py_request_debug_var_info_3.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeDebugVarInfo3),
            ctypes.c_uint8,
            ctypes.c_uint8,
        ]
        lib.sbgc_py_request_debug_var_info_3.restype = ctypes.c_int


        lib.sbgc_py_request_debug_var_values_3.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeDebugVarValues3),
        ]
        lib.sbgc_py_request_debug_var_values_3.restype = ctypes.c_int


        lib.sbgc_py_select_imu_3.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint16,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_select_imu_3.restype = ctypes.c_int


        lib.sbgc_py_control_quat_status.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_control_quat_status.restype = ctypes.c_int


    def open_native (self, port: str, baudrate: int) -> int:
        if not isinstance(port, str) or not port:
            raise ValueError("Port must be a non-empty string.")
        if not 1 <= baudrate <= 0xFFFFFFFF:
            raise ValueError("Baudrate must be in range 1..4294967295")

        handle = self._library.sbgc_py_open_com(port.encode("ascii"), baudrate)

        if not handle:
            raise NativeError(f"Cannot open {port} at {baudrate} baud.")

        return int(handle)

    def close(self, device: int) -> None:
        self._library.sbgc_py_close(device)

    def recover(self, device: int) -> None:
        status = self._library.sbgc_py_recover(device)
        if status != NativeStatus.OK:
            raise NativeError(f"Cannot recover the SimpleBGC connection (native status {status}).")

    def reset(self, device: int, flags: int, delay_ms: int) -> None:
        status = self._library.sbgc_py_reset(device, flags, delay_ms)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "RESET is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"RESET transmission failed with native status {status}."
        )

    def expect_reset(self, device: int, timeout: float) -> None:
        status = self._library.sbgc_py_expect_reset(device)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "RESET confirmation is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"RESET confirmation was not received in the native Serial API (native status {status})."
        )

    def motors_on(self, device: int) -> None:
        status = self._library.sbgc_py_motors_on(device)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "MOTORS_ON is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"MOTORS_ON failed with native status {status}."
        )

    def motors_off(self, device: int, mode: int) -> None:
        status = self._library.sbgc_py_motors_off(device, mode)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "MOTORS_OFF is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"MOTORS_OFF failed with native status {status}."
        )

    def play_beeper(
        self,
        device: int,
        mode: int,
        note_length: int,
        decay_factor: int,
        notes_hz: tuple[int, ...],
    ) -> None:
        notes = (ctypes.c_uint16 * len(notes_hz))(*notes_hz) if notes_hz else None
        status = self._library.sbgc_py_play_beeper(
            device,
            mode,
            note_length,
            decay_factor,
            notes,
            len(notes_hz),
        )
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "BEEP_SOUND is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"BEEP_SOUND failed with native status {status}."
        )


    def set_api_virtual_channels(self, device: int, values: tuple[int, ...],) -> None:
        count = len(values)
        native_values = (ctypes.c_int16 * count)(*values)

        status = self._library.sbgc_py_set_api_virtual_channels(device, native_values, count,)

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "API virtual channels are unavailable: "
                "SBGC_CONTROL_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            "API virtual-channel update failed in the native Serial API "
            f"with native status {status}."
        )


    def execute_menu(
        self, device: int, menu_command: int, *, need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_execute_menu(
            device,
            menu_command,
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )
        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "EXECUTE_MENU is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "EXECUTE_MENU confirmation is unavailable: SBGC_NEED_CONFIRM_CMD "
                "is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"EXECUTE_MENU failed with native status {status}."
        )

    def control(
        self, device: int, modes: tuple[int, int, int], speeds: tuple[int, int, int],
        angles: tuple[int, int, int], *, need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        native_modes = (ctypes.c_uint8 * 3)(*modes)
        native_speeds = (ctypes.c_int16 * 3)(*speeds)
        native_angles = (ctypes.c_int16 * 3)(*angles)
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_control(
            device,
            native_modes,
            native_speeds,
            native_angles,
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )

        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "CONTROL confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is "
                "disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "CONTROL is unavailable: SBGC_CONTROL_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        # Never retry a control command. A failed status can still mean the
        # board received it and a duplicate may cause an unintended movement.
        raise NativeError(
            f"CONTROL failed with native status {status}."
        )

    def control_config(
        self,
        device: int,
        config: NativeControlConfig,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_control_config(
            device,
            ctypes.byref(config),
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )
        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "CONTROL_CONFIG confirmation is unavailable: SBGC_NEED_CONFIRM_CMD "
                "is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "CONTROL_CONFIG is unavailable: SBGC_CONTROL_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"CONTROL_CONFIG failed with native status {status}."
        )

    def get_adj_vars(
        self, device: int, ids: tuple[int, ...]
    ) -> tuple[NativeAdjustableVariable, ...]:
        native_ids = (ctypes.c_uint8 * len(ids))(*ids)
        result = (NativeAdjustableVariable * len(ids))()
        status = self._library.sbgc_py_get_adj_vars(
            device, native_ids, len(ids), result
        )
        if status == NativeStatus.OK:
            return tuple(result)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_ADJ_VARS_VAL is unavailable: SBGC_ADJVAR_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"GET_ADJ_VARS_VAL failed in the native Serial API with native status {status}."
        )

    def set_adj_vars(
        self,
        device: int,
        variables: tuple[NativeAdjustableVariable, ...],
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        native_variables = (NativeAdjustableVariable * len(variables))(*variables)
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_set_adj_vars(
            device,
            native_variables,
            len(variables),
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )
        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "SET_ADJ_VARS_VAL confirmation is unavailable: SBGC_NEED_CONFIRM_CMD "
                "is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "SET_ADJ_VARS_VAL is unavailable: SBGC_ADJVAR_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        # A failed status can still mean the board applied the new value.
        # Retrying could write the parameter twice, so it is deliberately avoided.
        raise NativeError(
            f"SET_ADJ_VARS_VAL failed with native status {status}."
        )

    def save_adj_vars(
        self,
        device: int,
        ids: tuple[int, ...] | None,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        native_ids = (ctypes.c_uint8 * len(ids))(*ids) if ids is not None else None
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_save_adj_vars(
            device,
            native_ids,
            len(ids) if ids is not None else 0,
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )
        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "SAVE_PARAMS_3 confirmation is unavailable: SBGC_NEED_CONFIRM_CMD "
                "is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "SAVE_PARAMS_3 is unavailable: SBGC_ADJVAR_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        # The board can have already committed the EEPROM write even when a
        # transport error is reported. Never retry it automatically.
        raise NativeError(
            f"SAVE_PARAMS_3 failed with native status {status}."
        )

    def run_script(self, device: int, mode: int, slot: int) -> None:
        status = self._library.sbgc_py_run_script(device, mode, slot)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "RUN_SCRIPT is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"RUN_SCRIPT failed with native status {status}."
        )

    def read_script_debug_info(self, device: int, timeout: float) -> NativeScriptDebugInfo:
        result = NativeScriptDebugInfo()
        status = self._library.sbgc_py_read_script_debug_info(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "SCRIPT_DEBUG is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        raise NativeError(
            f"SCRIPT_DEBUG was not received in the native Serial API (native status {status})."
        )

    def _service_confirmation(
        self, command: str, function: object, *args: object, need_confirmation: bool,
    ) -> NativeConfirmation | None:
        confirmation = NativeConfirmation() if need_confirmation else None
        status = function(
            *args,
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )
        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                f"{command} confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled "
                "in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(f"{command} is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h.")
        raise NativeError(f"{command} failed in the native Serial API with native status {status}.")

    def tune_auto_pid(
        self, device: int, config: NativeAutoPid, *, need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "AUTO_PID", self._library.sbgc_py_tune_auto_pid,
            device, ctypes.byref(config), need_confirmation=need_confirmation,
        )

    def break_auto_pid(
        self, device: int, *, need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "AUTO_PID", self._library.sbgc_py_break_auto_pid,
            device, need_confirmation=need_confirmation,
        )

    def tune_auto_pid2(
        self, device: int, config: NativeAutoPid2, *, need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "AUTO_PID2", self._library.sbgc_py_tune_auto_pid2,
            device, ctypes.byref(config), need_confirmation=need_confirmation,
        )

    def read_auto_pid_state(self, device: int) -> NativeAutoPidState:
        result = NativeAutoPidState()
        status = self._library.sbgc_py_read_auto_pid_state(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError("AUTO_PID state is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h.")
        raise NativeError(f"AUTO_PID state read failed in the native Serial API with native status {status}.")

    def synchronize_motors(
        self, device: int, config: NativeSyncMotors, *, need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "SYNC_MOTORS", self._library.sbgc_py_synchronize_motors,
            device, ctypes.byref(config), need_confirmation=need_confirmation,
        )

    def request_motor_state(
        self, device: int, motor_id: int, data_set: int, size: int,
    ) -> bytes:
        result = (ctypes.c_uint8 * size)()
        status = self._library.sbgc_py_request_motor_state(
            device, motor_id, data_set, result, size,
        )
        if status == NativeStatus.OK:
            return bytes(result)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError("EXT_MOTORS_STATE is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h.")
        raise NativeError(f"EXT_MOTORS_STATE request failed in the native Serial API with native status {status}.")

    def read_motor_state(self, device: int, size: int) -> bytes:
        result = (ctypes.c_uint8 * size)()
        status = self._library.sbgc_py_read_motor_state(device, result, size)
        if status == NativeStatus.OK:
            return bytes(result)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError("EXT_MOTORS_STATE is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h.")
        raise NativeError(f"EXT_MOTORS_STATE read failed in the native Serial API with native status {status}.")

    def set_boot_mode(self, device: int, *, extended: bool, need_confirmation: bool, delay_ms: int) -> None:
        status = self._library.sbgc_py_set_boot_mode(device, extended, need_confirmation, delay_ms)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError("BOOT_MODE_3 is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h.")
        raise NativeError(f"BOOT_MODE_3 failed in the native Serial API with native status {status}.")

    def write_state_vars(
        self, device: int, state: NativeStateVars, *, need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "WRITE_STATE_VARS", self._library.sbgc_py_write_state_vars,
            device, ctypes.byref(state), need_confirmation=need_confirmation,
        )

    def read_state_vars(self, device: int) -> NativeStateVars:
        result = NativeStateVars()
        status = self._library.sbgc_py_read_state_vars(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError("READ_STATE_VARS is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h.")
        raise NativeError(f"READ_STATE_VARS failed in the native Serial API with native status {status}.")

    def set_debug_port(
        self, device: int, action: int, filter: int, *, need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "SET_DEBUG_PORT", self._library.sbgc_py_set_debug_port,
            device, action, filter, need_confirmation=need_confirmation,
        )

    def read_debug_port(self, device: int) -> tuple[int, int, int, bytes]:
        time_ms = ctypes.c_uint16()
        port_and_direction = ctypes.c_uint8()
        command_id = ctypes.c_uint8()
        payload = (ctypes.c_uint8 * 255)()
        status = self._library.sbgc_py_read_debug_port(
            device, ctypes.byref(time_ms), ctypes.byref(port_and_direction),
            ctypes.byref(command_id), payload, len(payload),
        )
        if status == NativeStatus.OK:
            return time_ms.value, port_and_direction.value, command_id.value, bytes(payload)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError("SET_DEBUG_PORT is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h.")
        raise NativeError(
            "No CMD_SET_DEBUG_PORT debug record arrived on the current serial connection "
            f"before the native SerialAPI timeout (native status {status})."
        )

    def get_realtime_data_3(self, device: int) -> NativeRealtimeData:
        return self._get_realtime_data(device, 3)

    def get_realtime_data_4(self, device: int) -> NativeRealtimeData:
        return self._get_realtime_data(device, 4)

    def get_realtime_data(self, device: int) -> NativeRealtimeData:
        return self.get_realtime_data_3(device)

    def get_realtime_data_custom(self, device: int, flags: int, payload_size: int) -> bytes:
        if not 2 <= payload_size <= 0xFF:
            raise ValueError("payload_size must be in range 2..255")
        result = (ctypes.c_uint8 * (payload_size + 4))()
        status = self._library.sbgc_py_get_realtime_data_custom(
            device, flags, result, payload_size
        )
        if status == NativeStatus.OK:
            return bytes(result[4:])
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "REALTIME_DATA_CUSTOM is unavailable: SBGC_REALTIME_MODULE is "
                "disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"REALTIME_DATA_CUSTOM failed in the native Serial API with native status {status}."
        )

    def _get_realtime_data(self, device: int, version: int) -> NativeRealtimeData:
        result = NativeRealtimeData()
        function = (
            self._library.sbgc_py_get_realtime_data_3
            if version == 3
            else self._library.sbgc_py_get_realtime_data_4
        )
        status = function(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                f"REALTIME_DATA_{version} is unavailable: SBGC_REALTIME_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        raise NativeError(
            f"REALTIME_DATA_{version} failed in the native Serial API with native status {status}."
        )


    def read_rc_inputs(self, device: int, sources: tuple[int, ...]) -> tuple[int, ...]:
        count = len(sources)
        if not 1 <= count <= 42:
            raise ValueError("sources must contain between 1 and 42 elements.")

        source_buffer = (ctypes.c_uint8 * count)(*sources)
        value_buffer = (ctypes.c_int16 * count)()

        status = self._library.sbgc_py_read_rc_inputs(device, source_buffer, count, value_buffer)

        if status == NativeStatus.OK:
            return tuple(value_buffer)

        raise NativeError(f"READ_RC_INPUTS failed in the native Serial API with native status {status}.")

    def _update_data_stream(self, function: object, device: int, config: NativeDataStreamInterval,
        *, need_confirmation: bool, ) -> NativeConfirmation | None:

        confirmation = NativeConfirmation() if need_confirmation else None

        status = function(
            device,
            ctypes.byref(config),
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        ) 

        if status == NativeStatus.OK:
            return confirmation

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError("DATA_STREAM is unavailable: SBGC_REALTIME_MODULE is disabled "
                              "in serialAPI_Config.h.")

        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError("DATA_STREAM confirmation is unavailable: "
                                "SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h.")

        raise NativeError(f"DATA_STREAM failed in the native Serial API with native status {status}.")


    def start_data_stream(self, device: int, config: NativeDataStreamInterval,
        *, need_confirmation: bool = False, ) -> NativeConfirmation | None:
        """ todo """
        return self._update_data_stream(self._library.sbgc_py_start_data_stream, device, config, need_confirmation=need_confirmation,)


    def stop_data_stream(self, device: int, config: NativeDataStreamInterval,
        *, need_confirmation: bool = False, ) -> NativeConfirmation | None:
        """ todo """
        return self._update_data_stream(self._library.sbgc_py_stop_data_stream, device, config, need_confirmation=need_confirmation,)

    def request_debug_var_info_3(self, device: int, variables, start_index: int = 0,) -> None:
        """ todo """
        if not 0 <= start_index <= 0xFF:
            raise ValueError("start_index must be in range 0...255")

        count = len(variables)
        if not 1 <= count <= 0xFF:
            raise ValueError("variables must contain from 1 to 255 items")

        status = self._library.sbgc_py_request_debug_var_info_3(device, variables, start_index, count)

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError("DEBUG_VAR_INFO_3 is unavailable: SBGC_REALTIME_MODULE is disabled "
                              "in serialAPI_Config.h.")

        raise NativeError(f"DEBUG_VAR_INFO_3 failed in the native Serial API with native status {status}.")


    def request_debug_var_values_3(self, device: int, variables, masks: tuple[int, ...] | None = None) -> None:
        """ todo """
        if len(variables) == 0:
            raise ValueError("Variables must not be empty")

        mask_array = None
        if masks is not None:
            if not masks:
                raise ValueError("Masks must be None or contain at least one word")
            if any(type(mask) is not int or not 0 <= mask <= 0xFFFF_FFFF for mask in masks):
                raise ValueError("Each mask must be an unsigned 32-bit integer")

            mask_array = (ctypes.c_uint32 * len(masks))(*masks)

        request = NativeDebugVarValues3(
            debug_var_info_3=ctypes.cast(variables, ctypes.POINTER(NativeDebugVarInfo3),),
            mask=
            (
                ctypes.cast(mask_array, ctypes.POINTER(ctypes.c_uint32))
                if mask_array is not None else None
            ),
            mask_count=0 if mask_array is None else len(mask_array),
        )

        status = self._library.sbgc_py_request_debug_var_values_3(device, ctypes.byref(request))

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError("DEBUG_VAR_VALUES_3 is unavailable: SBGC_REALTIME_MODULE is disabled "
                              "in serialAPI_Config.h.")

        raise NativeError(f"DEBUG_VAR_VALUES_3 failed in the native Serial API with native status {status}.")


    def select_imu_3(
        self, device: int, imu_type: int, action: int, time_ms: int,
        *, need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_select_imu_3(
            device,
            imu_type,
            action,
            time_ms,
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )

        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError("SELECT_IMU_3 is unavailable: SBGC_REALTIME_MODULE is disabled in serialAPI_Config.h.")
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError("SELECT_IMU_3 confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h.")
        raise NativeError(f"SELECT_IMU_3 failed in the native Serial API with native status {status}.")


    def control_quat_status(self, device: int, flags: int, payload_size: int) -> bytes:
        result = (ctypes.c_uint8 * payload_size)()
        status = self._library.sbgc_py_control_quat_status(device, flags, result, payload_size)

        if status == NativeStatus.OK:
            return bytes(result)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError("CONTROL_QUAT_STATUS is unavailable: SBGC_REALTIME_MODULE is disabled in serialAPI_Config.h.")
        raise NativeError(f"CONTROL_QUAT_STATUS failed in the native Serial API with native status {status}.")


    def read_data_stream(self, device: int, cmd_id: int, size: int,) -> bytes:
        if not 1 <= size <= 0xFF:
            raise ValueError("Size must be in range 1...255")

        buffer = (ctypes.c_uint8 * size)()

        status = self._library.sbgc_py_read_data_stream(device, cmd_id, buffer, size,)

        if status == NativeStatus.OK:
            return bytes(buffer)

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "READ_DATA_STREAM is unavailable: SBGC_REALTIME_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        raise NativeError(f"READ_DATA_STREAM failed in the native Serial API with native status {status}.")


    def get_angles(self, device: int) -> NativeAngles:
        result = NativeAngles()
        status = self._library.sbgc_py_get_angles(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_ANGLES is unavailable: SBGC_REALTIME_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        raise NativeError(
            "GET_ANGLES failed in the native Serial API with native status "
            f"{status}."
        )

    def get_angles_ext(self, device: int) -> NativeAnglesExt:
        result = NativeAnglesExt()
        status = self._library.sbgc_py_get_angles_ext(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_ANGLES_EXT is unavailable: SBGC_REALTIME_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        raise NativeError(
            "GET_ANGLES_EXT failed in the native Serial API with native status "
            f"{status}."
        )


    def get_board_info(self, device: int) -> NativeBoardInfo:
        result = NativeBoardInfo()
        status = self._library.sbgc_py_get_board_info(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_BOARD_INFO is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        raise NativeError(
            "GET_BOARD_INFO failed in the native Serial API with native status "
            f"{status}."
        )

    def get_board_info_3(self, device: int) -> NativeBoardInfo3:
        result = NativeBoardInfo3()
        status = self._library.sbgc_py_get_board_info_3(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_BOARD_INFO_3 is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        raise NativeError(
            "GET_BOARD_INFO_3 failed in the native Serial API "
            f"with native status {status}."
        )


class NativeLibrary(SerialApiLibrary):
    """Common SerialAPI wrapper configured for the native Win32 transport."""

    def _configure_functions(self) -> None:
        super()._configure_functions()
        self._library.sbgc_py_open_com.argtypes = [ctypes.c_char_p, ctypes.c_uint32]
        self._library.sbgc_py_open_com.restype = ctypes.c_void_p
