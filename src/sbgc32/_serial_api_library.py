from __future__ import annotations

import ctypes
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
    TIMEOUT = -8
    EXTERNAL_MOTOR_NO_RESPONSE = -9
    CAN_NOT_SUPPORTED = -10
    STATE_VARS_NOT_SUPPORTED = -11
    IMU_NOT_SUPPORTED = -12


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


class NativePidValues(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("profile_id", ctypes.c_uint8),
        ("p", ctypes.c_uint8 * 3),
        ("i", ctypes.c_uint8 * 3),
        ("d", ctypes.c_uint8 * 3),
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


class NativeCAN_ModuleInfo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_uint8),
        ("board_ver", ctypes.c_uint16),
        ("bootloader_ver", ctypes.c_uint16),
        ("firmware_ver", ctypes.c_uint16),
        ("reserved", ctypes.c_uint8 * 6),
    ]


class NativeCAN_DeviceScan(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("UID", ctypes.c_uint8 * 12),
        ("id", ctypes.c_uint8),
        ("type", ctypes.c_uint8),
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


class NativeAdjustableVariableFloat(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_uint8),
        ("value", ctypes.c_float),
    ]


class NativeAdjustableVariableTriggerSlot(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("source", ctypes.c_uint8),
        ("actions", ctypes.c_uint8 * 5),
    ]


class NativeAdjustableVariableAnalogSlot(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("source", ctypes.c_uint8),
        ("variable_id", ctypes.c_uint8),
        ("min_value", ctypes.c_uint8),
        ("max_value", ctypes.c_uint8),
    ]


class NativeAdjustableVariablesConfig(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("trigger_slots", NativeAdjustableVariableTriggerSlot * 10),
        ("analog_slots", NativeAdjustableVariableAnalogSlot * 15),
        ("reserved", ctypes.c_uint8 * 8),
    ]


class NativeAdjustableVariablesStateRequest(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("trigger_slot", ctypes.c_uint8),
        ("analog_source_id", ctypes.c_uint16),
        ("analog_variable_id", ctypes.c_uint8),
        ("lut_source_id", ctypes.c_uint16),
        ("lut_variable_id", ctypes.c_uint8),
    ]


class NativeAdjustableVariablesState(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("trigger_rc_data", ctypes.c_int16),
        ("trigger_action", ctypes.c_uint8),
        ("analog_source_value", ctypes.c_int16),
        ("analog_variable_value", ctypes.c_float),
        ("lut_source_value", ctypes.c_int16),
        ("lut_variable_value", ctypes.c_float),
    ]


class NativeAdjustableVariableInfo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_uint8),
        ("min_value", ctypes.c_int16),
        ("max_value", ctypes.c_int16),
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


class NativeControlExtAxis(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("mode", ctypes.c_uint8),
        ("flags", ctypes.c_uint8),
        ("speed", ctypes.c_int32),
        ("angle", ctypes.c_int32),
    ]


class NativeControlExt(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("data_set", ctypes.c_uint16),
        ("axes", NativeControlExtAxis * 3),
    ]


class NativeControlQuat(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("mode", ctypes.c_uint8),
        ("flags", ctypes.c_uint8),
        ("attitude", ctypes.c_float * 4),
        ("speed", ctypes.c_float * 3),
    ]


class NativeControlQuatConfig(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("data_set", ctypes.c_uint16),
        ("max_speed", ctypes.c_uint16 * 3),
        ("acceleration_limit", ctypes.c_uint16 * 3),
        ("jerk_slope", ctypes.c_uint16 * 3),
        ("flags", ctypes.c_uint16),
        ("attitude_lpf_frequency", ctypes.c_uint8),
        ("speed_lpf_frequency", ctypes.c_uint8),
    ]


class NativeExternalMotorControl(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("setpoint", ctypes.c_int32),
        ("param1", ctypes.c_int32),
    ]


class NativeExternalMotorsControlConfig(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("motors", ctypes.c_uint8),
        ("data_set", ctypes.c_uint16),
        ("mode", ctypes.c_uint8),
        ("max_speed", ctypes.c_uint16),
        ("max_acceleration", ctypes.c_uint16),
        ("jerk_slope", ctypes.c_uint16),
        ("max_torque", ctypes.c_uint16),
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


class NativeTransparentCommand(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("target", ctypes.c_uint8),
        ("payload_size", ctypes.c_uint8),
        ("payload", ctypes.POINTER(ctypes.c_uint8)),
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

        # TRANSPORT MODULE
        lib.sbgc_py_close.argtypes = [ctypes.c_void_p]
        lib.sbgc_py_close.restype = None

        lib.sbgc_py_recover.argtypes = [ctypes.c_void_p]
        lib.sbgc_py_recover.restype = ctypes.c_int

        lib.sbgc_py_get_last_error.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int),
        ]
        lib.sbgc_py_get_last_error.restype = ctypes.c_int

        # REALTIME MODULE
        lib.sbgc_py_get_angles.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAngles),
        ]
        lib.sbgc_py_get_angles.restype = ctypes.c_int

        lib.sbgc_py_get_angles_ext.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAnglesExt),
        ]
        lib.sbgc_py_get_angles_ext.restype = ctypes.c_int

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

        # SERVICE MODULE
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

        lib.sbgc_py_reset.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint16,
        ]
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

        lib.sbgc_py_execute_menu_ext.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_execute_menu_ext.restype = ctypes.c_int

        lib.sbgc_py_set_trigger_pin.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_set_trigger_pin.restype = ctypes.c_int

        lib.sbgc_py_set_servo_out.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_set_servo_out.restype = ctypes.c_int

        lib.sbgc_py_set_servo_out_ext.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_set_servo_out_ext.restype = ctypes.c_int

        lib.sbgc_py_run_script.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
        ]
        lib.sbgc_py_run_script.restype = ctypes.c_int

        lib.sbgc_py_read_script_debug_info.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeScriptDebugInfo),
        ]
        lib.sbgc_py_read_script_debug_info.restype = ctypes.c_int

        lib.sbgc_py_tune_auto_pid.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAutoPid),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_tune_auto_pid.restype = ctypes.c_int

        lib.sbgc_py_break_auto_pid.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_break_auto_pid.restype = ctypes.c_int

        lib.sbgc_py_tune_auto_pid2.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAutoPid2),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_tune_auto_pid2.restype = ctypes.c_int

        lib.sbgc_py_read_profile_pid_values.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.POINTER(NativePidValues),
        ]
        lib.sbgc_py_read_profile_pid_values.restype = ctypes.c_int

        lib.sbgc_py_read_auto_pid_state.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAutoPidState),
        ]
        lib.sbgc_py_read_auto_pid_state.restype = ctypes.c_int

        lib.sbgc_py_synchronize_motors.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeSyncMotors),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_synchronize_motors.restype = ctypes.c_int

        lib.sbgc_py_request_motor_state.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint16,
        ]
        lib.sbgc_py_request_motor_state.restype = ctypes.c_int

        lib.sbgc_py_read_motor_state.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint16,
        ]
        lib.sbgc_py_read_motor_state.restype = ctypes.c_int

        lib.sbgc_py_set_boot_mode.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint16,
        ]
        lib.sbgc_py_set_boot_mode.restype = ctypes.c_int

        lib.sbgc_py_write_state_vars.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeStateVars),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_write_state_vars.restype = ctypes.c_int

        lib.sbgc_py_read_state_vars.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeStateVars),
        ]
        lib.sbgc_py_read_state_vars.restype = ctypes.c_int

        lib.sbgc_py_set_debug_port.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint32,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_set_debug_port.restype = ctypes.c_int

        lib.sbgc_py_read_debug_port.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint16),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint16,
        ]
        lib.sbgc_py_read_debug_port.restype = ctypes.c_int

        lib.sbgc_py_request_module_list.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeCAN_ModuleInfo),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_request_module_list.restype = ctypes.c_int

        lib.sbgc_py_CAN_device_scan.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeCAN_DeviceScan),
        ]
        lib.sbgc_py_CAN_device_scan.restype = ctypes.c_int

        lib.sbgc_py_sign_message.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
        ]
        lib.sbgc_py_sign_message.restype = ctypes.c_int

        lib.sbgc_py_read_transparent_command.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeTransparentCommand),
        ]
        lib.sbgc_py_read_transparent_command.restype = ctypes.c_int

        lib.sbgc_py_send_transparent_command.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeTransparentCommand),
        ]
        lib.sbgc_py_send_transparent_command.restype = ctypes.c_int

        lib.sbgc_py_read_i2c_reg.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint8),
        ]
        lib.sbgc_py_read_i2c_reg.restype = ctypes.c_int

        lib.sbgc_py_write_i2c_reg.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_write_i2c_reg.restype = ctypes.c_int

        lib.sbgc_py_read_eeprom.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_uint16,
            ctypes.POINTER(ctypes.c_uint8),
        ]
        lib.sbgc_py_read_eeprom.restype = ctypes.c_int

        lib.sbgc_py_write_eeprom.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint16,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_write_eeprom.restype = ctypes.c_int

        lib.sbgc_py_read_external_data.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
        ]
        lib.sbgc_py_read_external_data.restype = ctypes.c_int

        lib.sbgc_py_write_external_data.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_write_external_data.restype = ctypes.c_int

        lib.sbgc_py_read_file.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint16,
            ctypes.c_uint16,
            ctypes.c_uint16,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint16),
            ctypes.POINTER(ctypes.c_uint16),
            ctypes.POINTER(ctypes.c_uint8),
        ]
        lib.sbgc_py_read_file.restype = ctypes.c_int

        lib.sbgc_py_write_file.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint16,
            ctypes.c_uint16,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint16,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_write_file.restype = ctypes.c_int

        lib.sbgc_py_clear_file_system.argtypes = [ctypes.c_void_p]
        lib.sbgc_py_clear_file_system.restype = ctypes.c_int

        lib.sbgc_py_read_profile_names.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint16,
        ]
        lib.sbgc_py_read_profile_names.restype = ctypes.c_int

        lib.sbgc_py_write_profile_names.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint16,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_write_profile_names.restype = ctypes.c_int

        lib.sbgc_py_manage_profile_set.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_manage_profile_set.restype = ctypes.c_int

        lib.sbgc_py_write_params_set.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_write_params_set.restype = ctypes.c_int

        lib.sbgc_py_read_profile_params.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint16,
        ]
        lib.sbgc_py_read_profile_params.restype = ctypes.c_int

        lib.sbgc_py_write_profile_params.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint16,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_write_profile_params.restype = ctypes.c_int

        lib.sbgc_py_use_profile_defaults.argtypes = [ctypes.c_void_p, ctypes.c_uint8]
        lib.sbgc_py_use_profile_defaults.restype = ctypes.c_int

        lib.sbgc_py_request_ext_imu_debug.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_request_ext_imu_debug.restype = ctypes.c_int

        lib.sbgc_py_send_ext_imu_command.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
            ctypes.c_uint8,
        ]
        lib.sbgc_py_send_ext_imu_command.restype = ctypes.c_int

        lib.sbgc_py_send_ext_sens_command.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
        ]
        lib.sbgc_py_send_ext_sens_command.restype = ctypes.c_int

        lib.sbgc_py_correction_gyro.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_int16,
        ]
        lib.sbgc_py_correction_gyro.restype = ctypes.c_int

        lib.sbgc_py_call_ahrs_helper.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
            ctypes.c_uint16,
        ]
        lib.sbgc_py_call_ahrs_helper.restype = ctypes.c_int

        lib.sbgc_py_provide_helper_data.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_provide_helper_data.restype = ctypes.c_int

        lib.sbgc_py_provide_helper_data_ext.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_provide_helper_data_ext.restype = ctypes.c_int

        lib.sbgc_py_request_calib_info.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_request_calib_info.restype = ctypes.c_int
        for name in (
            "sbgc_py_calib_acc",
            "sbgc_py_calib_gyro",
            "sbgc_py_calib_mag",
            "sbgc_py_calib_poles",
            "sbgc_py_calib_offset",
            "sbgc_py_calib_encoders_fld_offset",
        ):
            getattr(lib, name).argtypes = [ctypes.c_void_p]
            getattr(lib, name).restype = ctypes.c_int
        lib.sbgc_py_calib_encoders_offset.argtypes = [ctypes.c_void_p, ctypes.c_uint8]
        lib.sbgc_py_calib_encoders_offset.restype = ctypes.c_int
        lib.sbgc_py_calib_bat.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint16,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_calib_bat.restype = ctypes.c_int
        lib.sbgc_py_calib_orient_corr.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_calib_orient_corr.restype = ctypes.c_int
        lib.sbgc_py_calib_acc_ext_ref.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_calib_acc_ext_ref.restype = ctypes.c_int
        lib.sbgc_py_calib_cogging.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_calib_cogging.restype = ctypes.c_int

        # GIMBAL CONTROL MODULE
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

        lib.sbgc_py_set_api_virtual_channels.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_set_api_virtual_channels.restype = ctypes.c_int

        lib.sbgc_py_control_ext.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeControlExt),
        ]
        lib.sbgc_py_control_ext.restype = ctypes.c_int

        lib.sbgc_py_control_quat.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeControlQuat),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_control_quat.restype = ctypes.c_int

        lib.sbgc_py_control_quat_config.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeControlQuatConfig),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_control_quat_config.restype = ctypes.c_int

        lib.sbgc_py_ext_motors_action.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_ext_motors_action.restype = ctypes.c_int

        lib.sbgc_py_ext_motors_control.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeExternalMotorControl),
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_ext_motors_control.restype = ctypes.c_int

        lib.sbgc_py_ext_motors_control_config.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeExternalMotorsControlConfig),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_ext_motors_control_config.restype = ctypes.c_int

        lib.sbgc_py_set_api_virtual_channels_hr.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_set_api_virtual_channels_hr.restype = ctypes.c_int

        # ADJVAR MODULE
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

        lib.sbgc_py_get_adj_vars_float.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
            ctypes.POINTER(NativeAdjustableVariableFloat),
        ]
        lib.sbgc_py_get_adj_vars_float.restype = ctypes.c_int

        lib.sbgc_py_set_adj_vars_float.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAdjustableVariableFloat),
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_set_adj_vars_float.restype = ctypes.c_int

        lib.sbgc_py_read_adj_vars_config.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAdjustableVariablesConfig),
        ]
        lib.sbgc_py_read_adj_vars_config.restype = ctypes.c_int

        lib.sbgc_py_write_adj_vars_config.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAdjustableVariablesConfig),
            ctypes.c_uint8,
            ctypes.POINTER(NativeConfirmation),
        ]
        lib.sbgc_py_write_adj_vars_config.restype = ctypes.c_int

        lib.sbgc_py_get_adj_vars_state.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAdjustableVariablesStateRequest),
            ctypes.POINTER(NativeAdjustableVariablesState),
        ]
        lib.sbgc_py_get_adj_vars_state.restype = ctypes.c_int

        lib.sbgc_py_get_adj_vars_info.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.POINTER(NativeAdjustableVariableInfo),
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint8),
        ]
        lib.sbgc_py_get_adj_vars_info.restype = ctypes.c_int

    # Transport function
    def open_native(self, port: str, baudrate: int) -> int:
        if not isinstance(port, str) or not port:
            raise ValueError("Port must be a non-empty string.")
        if not 1 <= baudrate <= 0xFFFFFFFF:
            raise ValueError("Baudrate must be in range 1...4294967295")

        handle = self._library.sbgc_py_open_com(port.encode("ascii"), baudrate)

        if not handle:
            raise NativeError(f"Cannot open {port} at {baudrate} baud.")

        return int(handle)

    def close(self, device: int) -> None:
        self._library.sbgc_py_close(device)

    def recover(self, device: int) -> None:
        status = self._library.sbgc_py_recover(device)
        if status != NativeStatus.OK:
            raise NativeError(
                f"Cannot recover the SimpleBGC connection (native status {self._format_status(status)})."
            )

    @staticmethod
    def read_status(status: int | NativeStatus) -> str:
        """Return the symbolic name of a native bridge status code."""
        try:
            return NativeStatus(int(status)).name
        except ValueError:
            return f"UNKNOWN_STATUS({int(status)})"

    def _format_status(self, status: int | NativeStatus) -> str:
        return f"{self.read_status(status)} ({int(status)})"

    def get_last_serial_status(self, device: int) -> int:

        result = ctypes.c_int()
        status = self._library.sbgc_py_get_last_error(device, ctypes.byref(result))

        if status == NativeStatus.OK:
            return result.value

        raise NativeError(f"Can not read status: {self._format_status(status)}.")

    # SBGC_SERVICE_MODULE
    def reset(self, device: int, flags: int, delay_ms: int) -> None:

        status = self._library.sbgc_py_reset(device, flags, delay_ms)

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "RESET is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"RESET transmission failed with native status {self._format_status(status)}."
        )

    def expect_reset(self, device: int, timeout: float) -> None:

        status = self._library.sbgc_py_expect_reset(device)

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "RESET confirmation is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"RESET confirmation was not received in the native Serial API (native status {self._format_status(status)})."
        )

    def motors_on(self, device: int) -> None:

        status = self._library.sbgc_py_motors_on(device)

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "MOTORS_ON is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(f"MOTORS_ON failed with native status {self._format_status(status)}.")

    def motors_off(self, device: int, mode: int) -> None:

        status = self._library.sbgc_py_motors_off(device, mode)

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "MOTORS_OFF is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(f"MOTORS_OFF failed with native status {self._format_status(status)}.")

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
                "BEEP_SOUND is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(f"BEEP_SOUND failed with native status {self._format_status(status)}.")

    def execute_menu(
        self,
        device: int,
        menu_command: int,
        *,
        need_confirmation: bool = False,
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
                "EXECUTE_MENU is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "EXECUTE_MENU confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )

        raise NativeError(f"EXECUTE_MENU failed with native status {self._format_status(status)}.")

    def execute_menu_ext(
        self,
        device: int,
        menu_command: int,
        flags: int,
    ) -> tuple[NativeConfirmation | None, NativeConfirmation | None]:
        if not 0 <= flags <= 0x03:
            raise ValueError("flags must be in range 0...3.")

        started = NativeConfirmation() if flags & 0x01 else None
        finished = NativeConfirmation() if flags & 0x02 else None

        status = self._library.sbgc_py_execute_menu_ext(
            device,
            menu_command,
            flags,
            ctypes.byref(started) if started is not None else None,
            ctypes.byref(finished) if finished is not None else None,
        )

        if status == NativeStatus.OK:
            return started, finished

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "EXECUTE_MENU_EXT is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "EXECUTE_MENU_EXT confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"EXECUTE_MENU_EXT failed with native status {self._format_status(status)}."
        )

    def set_trigger_pin(
        self,
        device: int,
        pin_id: int,
        state: int,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "TRIGGER_PIN",
            self._library.sbgc_py_set_trigger_pin,
            device,
            pin_id,
            state,
            need_confirmation=need_confirmation,
        )

    def set_servo_out(self, device: int, values: tuple[int, int, int, int]) -> None:
        native_values = (ctypes.c_int16 * 4)(*values)

        status = self._library.sbgc_py_set_servo_out(device, native_values, len(native_values))

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "SERVO_OUT is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(f"SERVO_OUT failed with native status {self._format_status(status)}.")

    def set_servo_out_ext(
        self,
        device: int,
        pins: int,
        values: tuple[int, ...],
    ) -> None:
        native_values = (ctypes.c_int16 * len(values))(*values)

        status = self._library.sbgc_py_set_servo_out_ext(
            device,
            pins,
            native_values,
            len(native_values),
        )

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "SERVO_OUT_EXT is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(f"SERVO_OUT_EXT failed with native status {self._format_status(status)}.")

    def run_script(self, device: int, mode: int, slot: int) -> None:

        status = self._library.sbgc_py_run_script(device, mode, slot)

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "RUN_SCRIPT is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(f"RUN_SCRIPT failed with native status {self._format_status(status)}.")

    def read_script_debug_info(self, device: int, timeout: float) -> NativeScriptDebugInfo:

        result = NativeScriptDebugInfo()

        status = self._library.sbgc_py_read_script_debug_info(device, ctypes.byref(result))

        if status == NativeStatus.OK:
            return result

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "SCRIPT_DEBUG is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"SCRIPT_DEBUG was not received in the native Serial API (native status {self._format_status(status)})."
        )

    def _service_confirmation(
        self,
        command: str,
        function: object,
        *args: object,
        need_confirmation: bool,
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
                f"{command} confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                f"{command} is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        if status == NativeStatus.STATE_VARS_NOT_SUPPORTED:
            raise NativeError(
                f"{command} requires an Extended controller, firmware 2.68b7+, "
                "and the BF_STATE_VARS feature."
            )

        raise NativeError(
            f"{command} failed in the native Serial API with native status {self._format_status(status)}."
        )

    def tune_auto_pid(
        self,
        device: int,
        config: NativeAutoPid,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "AUTO_PID",
            self._library.sbgc_py_tune_auto_pid,
            device,
            ctypes.byref(config),
            need_confirmation=need_confirmation,
        )

    def break_auto_pid(
        self,
        device: int,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "AUTO_PID",
            self._library.sbgc_py_break_auto_pid,
            device,
            need_confirmation=need_confirmation,
        )

    def tune_auto_pid2(
        self,
        device: int,
        config: NativeAutoPid2,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "AUTO_PID2",
            self._library.sbgc_py_tune_auto_pid2,
            device,
            ctypes.byref(config),
            need_confirmation=need_confirmation,
        )

    def read_profile_pid_values(self, device: int, profile_id: int = 0xFF) -> NativePidValues:

        result = NativePidValues()

        status = self._library.sbgc_py_read_profile_pid_values(
            device, profile_id, ctypes.byref(result)
        )

        if status == NativeStatus.OK:
            return result

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "Profile PID read is unavailable: SBGC_PROFILES_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"Profile PID read failed in the native Serial API with native status {self._format_status(status)}."
        )

    def read_auto_pid_state(self, device: int) -> NativeAutoPidState:

        result = NativeAutoPidState()

        status = self._library.sbgc_py_read_auto_pid_state(device, ctypes.byref(result))

        if status == NativeStatus.OK:
            return result

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "AUTO_PID state is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"AUTO_PID state read failed in the native Serial API with native status {self._format_status(status)}."
        )

    def synchronize_motors(
        self,
        device: int,
        config: NativeSyncMotors,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "SYNC_MOTORS",
            self._library.sbgc_py_synchronize_motors,
            device,
            ctypes.byref(config),
            need_confirmation=need_confirmation,
        )

    def request_motor_state(
        self,
        device: int,
        motor_id: int,
        data_set: int,
        size: int,
    ) -> bytes:

        result = (ctypes.c_uint8 * size)()

        status = self._library.sbgc_py_request_motor_state(
            device,
            motor_id,
            data_set,
            result,
            size,
        )

        if status == NativeStatus.OK:
            return bytes(result)

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "EXT_MOTORS_STATE is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        if status == NativeStatus.EXTERNAL_MOTOR_NO_RESPONSE:
            raise NativeError(
                f"External motor 0x{motor_id:02X} did not reply to "
                "CMD_EXT_MOTORS_STATE. Check its ID, CAN connection, power, "
                "and External Motors configuration in GUI."
            )

        if status == NativeStatus.CAN_NOT_SUPPORTED:
            raise NativeError(
                "EXT_MOTORS_STATE is unavailable: the controller does not advertise the BF_CAN_PORT hardware feature."
            )

        raise NativeError(
            f"EXT_MOTORS_STATE request failed in the native Serial API with native status {self._format_status(status)}."
        )

    def read_motor_state(self, device: int, size: int) -> bytes:

        result = (ctypes.c_uint8 * size)()

        status = self._library.sbgc_py_read_motor_state(device, result, size)

        if status == NativeStatus.OK:
            return bytes(result)

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "EXT_MOTORS_STATE is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        if status == NativeStatus.EXTERNAL_MOTOR_NO_RESPONSE:
            raise NativeError(
                "External motors did not reply to "
                "CMD_EXT_MOTORS_STATE. Check their ID, CAN connection, power, "
                "and External Motors configuration in GUI."
            )

        if status == NativeStatus.CAN_NOT_SUPPORTED:
            raise NativeError(
                "EXT_MOTORS_STATE is unavailable: the controller does not advertise the BF_CAN_PORT hardware feature."
            )

        raise NativeError(
            f"EXT_MOTORS_STATE read failed in the native Serial API with native status {self._format_status(status)}."
        )

    def set_boot_mode(
        self,
        device: int,
        *,
        extended: bool,
        need_confirmation: bool,
        delay_ms: int,
    ) -> None:

        status = self._library.sbgc_py_set_boot_mode(
            device,
            extended,
            need_confirmation,
            delay_ms,
        )

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "BOOT_MODE_3 is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"BOOT_MODE_3 failed in the native Serial API with native status {self._format_status(status)}."
        )

    def write_state_vars(
        self,
        device: int,
        state: NativeStateVars,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "WRITE_STATE_VARS",
            self._library.sbgc_py_write_state_vars,
            device,
            ctypes.byref(state),
            need_confirmation=need_confirmation,
        )

    def read_state_vars(self, device: int) -> NativeStateVars:

        result = NativeStateVars()

        status = self._library.sbgc_py_read_state_vars(device, ctypes.byref(result))

        if status == NativeStatus.OK:
            return result

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "READ_STATE_VARS is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        if status == NativeStatus.STATE_VARS_NOT_SUPPORTED:
            raise NativeError(
                "READ_STATE_VARS requires an Extended controller, firmware 2.68b7+, and the BF_STATE_VARS feature."
            )

        raise NativeError(
            f"READ_STATE_VARS failed in the native Serial API with native status {self._format_status(status)}."
        )

    def set_debug_port(
        self,
        device: int,
        action: int,
        filter: int,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._service_confirmation(
            "SET_DEBUG_PORT",
            self._library.sbgc_py_set_debug_port,
            device,
            action,
            filter,
            need_confirmation=need_confirmation,
        )

    def read_debug_port(self, device: int) -> tuple[int, int, int, bytes, int]:

        time_ms = ctypes.c_uint16()
        port_and_direction = ctypes.c_uint8()
        command_id = ctypes.c_uint8()
        payload = (ctypes.c_uint8 * 255)()
        payload_size = ctypes.c_uint8()

        status = self._library.sbgc_py_read_debug_port(
            device,
            ctypes.byref(time_ms),
            ctypes.byref(port_and_direction),
            ctypes.byref(command_id),
            payload,
            ctypes.byref(payload_size),
            len(payload),
        )

        if status == NativeStatus.OK:
            return (
                time_ms.value,
                port_and_direction.value,
                command_id.value,
                bytes(payload[: payload_size.value]),
                payload_size.value,
            )

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "SET_DEBUG_PORT is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            "No CMD_SET_DEBUG_PORT debug record arrived on the current serial connection "
            f"before the native SerialAPI timeout (native status {self._format_status(status)})."
        )

    def request_module_list(
        self,
        device: int,
        max_devices: int = 13,
    ) -> tuple[NativeCAN_ModuleInfo, ...]:

        if not 1 <= max_devices <= 13:
            raise ValueError("max_devices must be in range 1...13")

        items = (NativeCAN_ModuleInfo * max_devices)()

        status = self._library.sbgc_py_request_module_list(device, items, max_devices)

        if status == NativeStatus.OK:
            return tuple(item for item in items if item.id != 0)

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "CMD_MODULE_LIST is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        if status == NativeStatus.CAN_NOT_SUPPORTED:
            raise NativeError(
                "CMD_MODULE_LIST is unavailable: the controller does not advertise the BF_CAN_PORT hardware feature."
            )

        raise NativeError(
            f"Module list failed in the native Serial API with native status {self._format_status(status)}."
        )

    def scan_can_device(self, device: int) -> NativeCAN_DeviceScan:

        result = NativeCAN_DeviceScan()

        status = self._library.sbgc_py_CAN_device_scan(
            device,
            ctypes.byref(result),
        )

        if status == NativeStatus.OK:
            return result

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "CMD_CAN_DEVICE_SCAN is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        if status == NativeStatus.CAN_NOT_SUPPORTED:
            raise NativeError(
                "CMD_CAN_DEVICE_SCAN is unavailable: the controller does not advertise the BF_CAN_PORT hardware feature."
            )

        raise NativeError(
            f"CMD_CAN_DEVICE_SCAN failed in the native Serial API with native status {self._format_status(status)}."
        )

    def sign_message(self, device: int, sign_type: int, message: bytes) -> bytes:

        if not isinstance(message, bytes):
            raise TypeError("message must be bytes.")

        if not 0 <= sign_type <= 0xFF:
            raise ValueError("sign_type must be in range 0...255.")

        if len(message) > 32:
            raise ValueError("message must contain at most 32 bytes.")

        tx = (ctypes.c_uint8 * 32).from_buffer_copy(message.ljust(32, b"\0"))
        rx = (ctypes.c_uint8 * 32)()

        status = self._library.sbgc_py_sign_message(
            device,
            sign_type,
            tx,
            rx,
        )

        if status == NativeStatus.OK:
            return bytes(rx)

        raise NativeError(
            f"CMD_SIGN_MESSAGE failed in the native Serial API with native status {self._format_status(status)}."
        )

    def send_transparent_command(
        self,
        device: int,
        target: int,
        payload: bytes,
    ) -> None:

        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes.")

        if not 0 <= target <= 0xFF:
            raise ValueError("target must be in range 0...255.")

        payload_size = len(payload)
        if payload_size > 254:
            raise ValueError("payload must contain at most 254 bytes.")

        native_payload = (ctypes.c_uint8 * max(1, payload_size)).from_buffer_copy(payload or b"\0")

        cmd = NativeTransparentCommand(
            target=target,
            payloadSize=payload_size,
            payload=native_payload,
        )

        status = self._library.sbgc_py_send_transparent_command(device, ctypes.byref(cmd))

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "CMD_TRANSPARENT_SAPI is unavailable: "
                "SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        if status == NativeStatus.CAN_NOT_SUPPORTED:
            raise NativeError(
                "CMD_TRANSPARENT_SAPI is unavailable: the controller does not advertise the BF_CAN_PORT hardware feature."
            )

        if status == NativeStatus.EXTERNAL_MOTOR_NO_RESPONSE:
            raise NativeError(
                "CMD_TRANSPARENT_SAPI target device did not reply. Check its CAN connection, power, and target value."
            )

        raise NativeError(
            "CMD_TRANSPARENT_SAPI failed in the native Serial API "
            f"with native status {self._format_status(status)}."
        )

    def read_transparent_command(
        self,
        device: int,
        max_payload_size: int = 254,
    ) -> tuple[int, bytes]:

        if not 0 <= max_payload_size <= 254:
            raise ValueError("max_payload_size must be in range 0...254.")

        native_payload = (ctypes.c_uint8 * max_payload_size)()

        cmd = NativeTransparentCommand(
            target=0,
            payload=native_payload,
            payloadSize=max_payload_size,
        )

        status = self._library.sbgc_py_read_transparent_command(
            device,
            ctypes.byref(cmd),
        )

        if status == NativeStatus.OK:
            return cmd.target, bytes(native_payload[: cmd.payloadSize])

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "CMD_TRANSPARENT_SAPI is unavailable: "
                "SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        if status == NativeStatus.CAN_NOT_SUPPORTED:
            raise NativeError(
                "CMD_TRANSPARENT_SAPI is unavailable: the controller does not advertise the BF_CAN_PORT hardware feature."
            )

        if status == NativeStatus.EXTERNAL_MOTOR_NO_RESPONSE:
            raise NativeError(
                "CMD_TRANSPARENT_SAPI target device did not reply. Check its CAN connection, power, and target value."
            )

        raise NativeError(
            "CMD_TRANSPARENT_SAPI failed in the native Serial API "
            f"with native status {self._format_status(status)}."
        )

    def _eeprom_confirmation(
        self, command: str, function: object, *args: object, need_confirmation: bool
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
                f"{command} confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                f"{command} is unavailable: SBGC_EEPROM_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"{command} failed in the native Serial API with native status {self._format_status(status)}."
        )

    def read_i2c_reg(
        self, device: int, device_address: int, register_address: int, size: int
    ) -> bytes:
        result = (ctypes.c_uint8 * size)()
        status = self._library.sbgc_py_read_i2c_reg(
            device, device_address, register_address, size, result
        )
        if status == NativeStatus.OK:
            return bytes(result)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "I2C_READ_REG_BUF is unavailable: SBGC_EEPROM_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"I2C_READ_REG_BUF failed in the native Serial API with native status {self._format_status(status)}."
        )

    def write_i2c_reg(
        self,
        device: int,
        device_address: int,
        register_address: int,
        data: bytes,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        buffer = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
        return self._eeprom_confirmation(
            "I2C_WRITE_REG_BUF",
            self._library.sbgc_py_write_i2c_reg,
            device,
            device_address,
            register_address,
            buffer,
            len(data),
            need_confirmation=need_confirmation,
        )

    def read_eeprom(self, device: int, address: int, size: int) -> bytes:
        result = (ctypes.c_uint8 * size)()
        status = self._library.sbgc_py_read_eeprom(device, address, size, result)
        if status == NativeStatus.OK:
            return bytes(result)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "EEPROM_READ is unavailable: SBGC_EEPROM_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"EEPROM_READ failed in the native Serial API with native status {self._format_status(status)}."
        )

    def write_eeprom(
        self,
        device: int,
        address: int,
        data: bytes,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        buffer = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
        return self._eeprom_confirmation(
            "EEPROM_WRITE",
            self._library.sbgc_py_write_eeprom,
            device,
            address,
            buffer,
            len(data),
            need_confirmation=need_confirmation,
        )

    def read_external_data(self, device: int) -> bytes:
        result = (ctypes.c_uint8 * 128)()
        status = self._library.sbgc_py_read_external_data(device, result)
        if status == NativeStatus.OK:
            return bytes(result)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "READ_EXTERNAL_DATA is unavailable: SBGC_EEPROM_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"READ_EXTERNAL_DATA failed in the native Serial API with native status {self._format_status(status)}."
        )

    def write_external_data(
        self,
        device: int,
        data: bytes,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        buffer = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
        return self._eeprom_confirmation(
            "WRITE_EXTERNAL_DATA",
            self._library.sbgc_py_write_external_data,
            device,
            buffer,
            need_confirmation=need_confirmation,
        )

    def read_eeprom_file(
        self, device: int, file_id: int, page_offset: int, max_size: int
    ) -> tuple[bytes, int, int]:
        data = (ctypes.c_uint8 * max_size)()
        file_size = ctypes.c_uint16()
        result_page_offset = ctypes.c_uint16()
        error_code = ctypes.c_uint8()
        status = self._library.sbgc_py_read_file(
            device,
            file_id,
            page_offset,
            max_size,
            data,
            ctypes.byref(file_size),
            ctypes.byref(result_page_offset),
            ctypes.byref(error_code),
        )
        if status == NativeStatus.OK:
            return (
                bytes(data[: file_size.value]),
                result_page_offset.value,
                error_code.value,
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "READ_FILE is unavailable: SBGC_EEPROM_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"READ_FILE failed in the native Serial API with native status {self._format_status(status)}."
        )

    def write_eeprom_file(
        self,
        device: int,
        file_id: int,
        page_offset: int,
        data: bytes,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        buffer = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
        return self._eeprom_confirmation(
            "WRITE_FILE",
            self._library.sbgc_py_write_file,
            device,
            file_id,
            page_offset,
            buffer,
            len(data),
            need_confirmation=need_confirmation,
        )

    def clear_file_system(self, device: int) -> None:
        status = self._library.sbgc_py_clear_file_system(device)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "FS_CLEAR_ALL is unavailable: SBGC_EEPROM_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"FS_CLEAR_ALL failed in the native Serial API with native status {self._format_status(status)}."
        )

    def _profiles_confirmation(
        self, command: str, function: object, *args: object, need_confirmation: bool
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
                f"{command} confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                f"{command} is unavailable: SBGC_PROFILES_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"{command} failed in the native Serial API with native status {self._format_status(status)}."
        )

    def read_profile_names(self, device: int) -> bytes:
        result = (ctypes.c_uint8 * 240)()
        status = self._library.sbgc_py_read_profile_names(device, result, len(result))
        if status == NativeStatus.OK:
            return bytes(result)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "READ_PROFILE_NAMES is unavailable: SBGC_PROFILES_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"READ_PROFILE_NAMES failed in the native Serial API with native status {self._format_status(status)}."
        )

    def write_profile_names(
        self,
        device: int,
        names: bytes,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        buffer = (ctypes.c_uint8 * len(names)).from_buffer_copy(names)
        return self._profiles_confirmation(
            "WRITE_PROFILE_NAMES",
            self._library.sbgc_py_write_profile_names,
            device,
            buffer,
            len(names),
            need_confirmation=need_confirmation,
        )

    def manage_profile_set(
        self,
        device: int,
        slot: int,
        action: int,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._profiles_confirmation(
            "PROFILE_SET",
            self._library.sbgc_py_manage_profile_set,
            device,
            slot,
            action,
            need_confirmation=need_confirmation,
        )

    def set_profile_writing(
        self,
        device: int,
        action: int,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._profiles_confirmation(
            "WRITE_PARAMS_SET",
            self._library.sbgc_py_write_params_set,
            device,
            action,
            need_confirmation=need_confirmation,
        )

    def read_profile_params(self, device: int, block: int, profile_id: int, size: int) -> bytes:
        result = (ctypes.c_uint8 * size)()
        status = self._library.sbgc_py_read_profile_params(device, block, profile_id, result, size)
        if status == NativeStatus.OK:
            return bytes(result)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "profile parameters are unavailable: SBGC_PROFILES_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"profile parameter read failed in the native Serial API with native status {self._format_status(status)}."
        )

    def write_profile_params(
        self,
        device: int,
        block: int,
        parameters: bytes,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        buffer = (ctypes.c_uint8 * len(parameters)).from_buffer_copy(parameters)
        return self._profiles_confirmation(
            "profile parameter write",
            self._library.sbgc_py_write_profile_params,
            device,
            block,
            buffer,
            len(parameters),
            need_confirmation=need_confirmation,
        )

    def use_profile_defaults(self, device: int, profile_id: int) -> None:
        status = self._library.sbgc_py_use_profile_defaults(device, profile_id)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "USE_DEFAULTS is unavailable: SBGC_PROFILES_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"USE_DEFAULTS failed in the native Serial API with native status {self._format_status(status)}."
        )

    def request_ext_imu_debug(self, device: int) -> bytes:
        result = (ctypes.c_uint8 * 74)()
        status = self._library.sbgc_py_request_ext_imu_debug(device, result, len(result))
        if status == NativeStatus.OK:
            return bytes(result)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "EXT_IMU_DEBUG_INFO is unavailable: SBGC_IMU_MODULE is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.IMU_NOT_SUPPORTED:
            raise NativeError(
                "EXT_IMU_DEBUG_INFO is unavailable: the controller does not advertise the BF_EXT_IMU feature."
            )
        raise NativeError(
            "EXT_IMU_DEBUG_INFO failed. Check external IMU power, connection, and configuration "
            f"(native status {self._format_status(status)})."
        )

    def _external_imu_command(
        self,
        function: object,
        command: str,
        device: int,
        command_id: int,
        payload: bytes,
        payload_size: int,
        *arguments: int,
    ) -> tuple[int, bytes]:
        result = (ctypes.c_uint8 * max(1, payload_size)).from_buffer_copy(
            payload.ljust(max(1, payload_size), b"\0")
        )
        result_command_id = ctypes.c_uint8(command_id)
        status = function(device, ctypes.byref(result_command_id), result, payload_size, *arguments)
        if status == NativeStatus.OK:
            return result_command_id.value, bytes(result[:payload_size])
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                f"{command} is unavailable: SBGC_IMU_MODULE is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.IMU_NOT_SUPPORTED:
            raise NativeError(
                f"{command} is unavailable: the controller does not advertise the BF_EXT_IMU feature."
            )
        raise NativeError(
            f"{command} failed. Check external IMU/sensor power, connection, and configuration "
            f"(native status {self._format_status(status)})."
        )

    def send_ext_imu_command(
        self,
        device: int,
        command_id: int,
        payload: bytes,
        payload_size: int,
        command_type: int,
    ) -> tuple[int, bytes]:
        return self._external_imu_command(
            self._library.sbgc_py_send_ext_imu_command,
            "EXT_IMU_CMD",
            device,
            command_id,
            payload,
            payload_size,
            command_type,
        )

    def send_ext_sens_command(
        self,
        device: int,
        command_id: int,
        payload: bytes,
        payload_size: int,
        flags: int,
        command_type: int,
    ) -> tuple[int, bytes]:
        return self._external_imu_command(
            self._library.sbgc_py_send_ext_sens_command,
            "EXT_SENS_CMD",
            device,
            command_id,
            payload,
            payload_size,
            flags,
            command_type,
        )

    def _imu_status(self, command: str, status: int) -> None:
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                f"{command} is unavailable: SBGC_IMU_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"{command} failed in the native Serial API with native status {self._format_status(status)}."
        )

    def correction_gyro(
        self,
        device: int,
        imu_type: int,
        zero_correction: tuple[int, int, int],
        zero_heading_correction: int,
    ) -> None:
        correction = (ctypes.c_int16 * 3)(*zero_correction)
        status = self._library.sbgc_py_correction_gyro(
            device,
            imu_type,
            correction,
            zero_heading_correction,
        )
        self._imu_status("GYRO_CORRECTION", status)

    def call_ahrs_helper(self, device: int, helper: bytes, mode: int) -> bytes:
        result = (ctypes.c_uint8 * len(helper)).from_buffer_copy(helper)
        status = self._library.sbgc_py_call_ahrs_helper(device, result, len(result), mode)
        self._imu_status("AHRS_HELPER", status)
        return bytes(result)

    def _provide_helper_data(
        self, function: object, command: str, device: int, helper_data: bytes
    ) -> None:
        data = (ctypes.c_uint8 * len(helper_data)).from_buffer_copy(helper_data)
        status = function(device, data, len(data))
        self._imu_status(command, status)

    def provide_helper_data(self, device: int, helper_data: bytes) -> None:
        self._provide_helper_data(
            self._library.sbgc_py_provide_helper_data,
            "HELPER_DATA",
            device,
            helper_data,
        )

    def provide_helper_data_ext(self, device: int, helper_data: bytes) -> None:
        self._provide_helper_data(
            self._library.sbgc_py_provide_helper_data_ext,
            "HELPER_DATA",
            device,
            helper_data,
        )

    def request_calib_info(self, device: int, imu_type: int) -> bytes:
        result = (ctypes.c_uint8 * 33)()
        status = self._library.sbgc_py_request_calib_info(device, result, imu_type)
        self._calib_status("CALIB_INFO", status)
        return bytes(result)

    def _calib_status(self, command: str, status: int) -> None:
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                f"{command} is unavailable: SBGC_CALIB_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"{command} failed in the native Serial API with native status {self._format_status(status)}."
        )

    def calib(self, command: str, device: int, *arguments: int) -> None:
        status = getattr(self._library, f"sbgc_py_{command}")(device, *arguments)
        self._calib_status(command.removeprefix("calib_").upper(), status)

    def calib_confirm(
        self,
        command: str,
        device: int,
        *arguments: object,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        confirmation = NativeConfirmation() if need_confirmation else None
        status = getattr(self._library, f"sbgc_py_{command}")(
            device,
            *arguments,
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )
        self._calib_status(command.removeprefix("calib_").upper(), status)
        return confirmation

    # SBGC_CONTROL_MODULE
    def set_api_virtual_channels(
        self,
        device: int,
        values: tuple[int, ...],
    ) -> None:

        count = len(values)
        native_values = (ctypes.c_int16 * count)(*values)

        status = self._library.sbgc_py_set_api_virtual_channels(
            device,
            native_values,
            count,
        )

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "API virtual channels are unavailable: "
                "SBGC_CONTROL_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            "API virtual-channel update failed in the native Serial API "
            f"with native status {self._format_status(status)}."
        )

    def control(
        self,
        device: int,
        modes: tuple[int, int, int],
        speeds: tuple[int, int, int],
        angles: tuple[int, int, int],
        *,
        need_confirmation: bool = False,
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
                "CONTROL is unavailable: SBGC_CONTROL_MODULE is disabled in serialAPI_Config.h."
            )
        # Never retry a control command. A failed status can still mean the
        # board received it and a duplicate may cause an unintended movement.
        raise NativeError(f"CONTROL failed with native status {self._format_status(status)}.")

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
            f"CONTROL_CONFIG failed with native status {self._format_status(status)}."
        )

    def control_ext(self, device: int, control: NativeControlExt) -> None:
        status = self._library.sbgc_py_control_ext(device, ctypes.byref(control))
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "CONTROL_EXT is unavailable: SBGC_CONTROL_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(f"CONTROL_EXT failed with native status {self._format_status(status)}.")

    def control_quat(
        self,
        device: int,
        control: NativeControlQuat,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_control_quat(
            device,
            ctypes.byref(control),
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )
        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "CONTROL_QUAT confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "CONTROL_QUAT is unavailable: SBGC_CONTROL_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(f"CONTROL_QUAT failed with native status {self._format_status(status)}.")

    def control_quat_config(
        self,
        device: int,
        config: NativeControlQuatConfig,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_control_quat_config(
            device,
            ctypes.byref(config),
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )
        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "CONTROL_QUAT_CONFIG confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "CONTROL_QUAT_CONFIG is unavailable: SBGC_CONTROL_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"CONTROL_QUAT_CONFIG failed with native status {self._format_status(status)}."
        )

    def ext_motors_action(
        self, device: int, motors: int, action: int, *, need_confirmation: bool = False
    ) -> NativeConfirmation | None:
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_ext_motors_action(
            device,
            motors,
            action,
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )
        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.CAN_NOT_SUPPORTED:
            raise NativeError(
                "EXT_MOTORS_ACTION is unavailable: the board does not support a CAN port."
            )
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "EXT_MOTORS_ACTION confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "EXT_MOTORS_ACTION is unavailable: SBGC_CONTROL_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"EXT_MOTORS_ACTION failed with native status {self._format_status(status)}."
        )

    def ext_motors_control(
        self,
        device: int,
        control: NativeExternalMotorControl,
        motors: int,
        data_set: int,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_ext_motors_control(
            device,
            ctypes.byref(control),
            motors,
            data_set,
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )
        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.CAN_NOT_SUPPORTED:
            raise NativeError(
                "EXT_MOTORS_CONTROL is unavailable: the board does not support a CAN port."
            )
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "EXT_MOTORS_CONTROL confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "EXT_MOTORS_CONTROL is unavailable: SBGC_CONTROL_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"EXT_MOTORS_CONTROL failed with native status {self._format_status(status)}."
        )

    def ext_motors_control_config(
        self,
        device: int,
        config: NativeExternalMotorsControlConfig,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_ext_motors_control_config(
            device,
            ctypes.byref(config),
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )
        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.CAN_NOT_SUPPORTED:
            raise NativeError(
                "EXT_MOTORS_CONTROL_CONFIG is unavailable: the board does not support a CAN port."
            )
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "EXT_MOTORS_CONTROL_CONFIG confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "EXT_MOTORS_CONTROL_CONFIG is unavailable: SBGC_CONTROL_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"EXT_MOTORS_CONTROL_CONFIG failed with native status {self._format_status(status)}."
        )

    def set_api_virtual_channels_hr(self, device: int, values: tuple[int, ...]) -> None:
        native_values = (ctypes.c_int16 * len(values))(*values)
        status = self._library.sbgc_py_set_api_virtual_channels_hr(
            device, native_values, len(values)
        )
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "API_VIRT_CH_HIGH_RES is unavailable: SBGC_CONTROL_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"API_VIRT_CH_HIGH_RES failed with native status {self._format_status(status)}."
        )

    # SBGC_ADJVAR_MODULE
    def get_adj_vars(
        self, device: int, ids: tuple[int, ...]
    ) -> tuple[NativeAdjustableVariable, ...]:
        native_ids = (ctypes.c_uint8 * len(ids))(*ids)
        result = (NativeAdjustableVariable * len(ids))()
        status = self._library.sbgc_py_get_adj_vars(device, native_ids, len(ids), result)
        if status == NativeStatus.OK:
            return tuple(result)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_ADJ_VARS_VAL is unavailable: SBGC_ADJVAR_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"GET_ADJ_VARS_VAL failed in the native Serial API with native status {self._format_status(status)}."
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
            f"SET_ADJ_VARS_VAL failed with native status {self._format_status(status)}."
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
        raise NativeError(f"SAVE_PARAMS_3 failed with native status {self._format_status(status)}.")

    def get_adj_vars_float(
        self, device: int, ids: tuple[int, ...]
    ) -> tuple[NativeAdjustableVariableFloat, ...]:
        native_ids = (ctypes.c_uint8 * len(ids))(*ids)
        result = (NativeAdjustableVariableFloat * len(ids))()
        status = self._library.sbgc_py_get_adj_vars_float(device, native_ids, len(ids), result)
        if status == NativeStatus.OK:
            return tuple(result)
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_ADJ_VARS_VAL_F is unavailable: SBGC_ADJVAR_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"GET_ADJ_VARS_VAL_F failed with native status {self._format_status(status)}."
        )

    def set_adj_vars_float(
        self,
        device: int,
        variables: tuple[NativeAdjustableVariableFloat, ...],
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        native_variables = (NativeAdjustableVariableFloat * len(variables))(*variables)
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_set_adj_vars_float(
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
                "SET_ADJ_VARS_VAL_F confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "SET_ADJ_VARS_VAL_F is unavailable: SBGC_ADJVAR_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"SET_ADJ_VARS_VAL_F failed with native status {self._format_status(status)}."
        )

    def read_adj_vars_config(self, device: int) -> NativeAdjustableVariablesConfig:
        result = NativeAdjustableVariablesConfig()
        status = self._library.sbgc_py_read_adj_vars_config(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "READ_ADJ_VARS_CFG is unavailable: SBGC_ADJVAR_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"READ_ADJ_VARS_CFG failed with native status {self._format_status(status)}."
        )

    def write_adj_vars_config(
        self,
        device: int,
        config: NativeAdjustableVariablesConfig,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        confirmation = NativeConfirmation() if need_confirmation else None
        status = self._library.sbgc_py_write_adj_vars_config(
            device,
            ctypes.byref(config),
            need_confirmation,
            ctypes.byref(confirmation) if confirmation is not None else None,
        )
        if status == NativeStatus.OK:
            return confirmation
        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "WRITE_ADJ_VARS_CFG confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "WRITE_ADJ_VARS_CFG is unavailable: SBGC_ADJVAR_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"WRITE_ADJ_VARS_CFG failed with native status {self._format_status(status)}."
        )

    def get_adj_vars_state(
        self, device: int, request: NativeAdjustableVariablesStateRequest
    ) -> NativeAdjustableVariablesState:
        result = NativeAdjustableVariablesState()
        status = self._library.sbgc_py_get_adj_vars_state(
            device, ctypes.byref(request), ctypes.byref(result)
        )
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.STATE_VARS_NOT_SUPPORTED:
            raise NativeError(
                "ADJ_VARS_STATE is unavailable: the board does not support STATE_VARS."
            )
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "ADJ_VARS_STATE is unavailable: SBGC_ADJVAR_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(
            f"ADJ_VARS_STATE failed with native status {self._format_status(status)}."
        )

    def get_adj_vars_info(
        self, device: int, start_id: int
    ) -> tuple[NativeAdjustableVariableInfo, ...]:
        result = (NativeAdjustableVariableInfo * 102)()
        count = ctypes.c_uint8()
        status = self._library.sbgc_py_get_adj_vars_info(
            device, start_id, result, len(result), ctypes.byref(count)
        )
        if status == NativeStatus.OK:
            return tuple(result[: count.value])
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "ADJ_VARS_INFO is unavailable: SBGC_ADJVAR_MODULE is disabled in serialAPI_Config.h."
            )
        raise NativeError(f"ADJ_VARS_INFO failed with native status {self._format_status(status)}.")

    # SBGC_REALTIME_MODULE
    def get_realtime_data_3(self, device: int) -> NativeRealtimeData:
        return self._get_realtime_data(device, 3)

    def get_realtime_data_4(self, device: int) -> NativeRealtimeData:
        return self._get_realtime_data(device, 4)

    def get_realtime_data(self, device: int) -> NativeRealtimeData:
        return self.get_realtime_data_3(device)

    def get_realtime_data_custom(self, device: int, flags: int, payload_size: int) -> bytes:

        if not 2 <= payload_size <= 0xFF:
            raise ValueError("payload_size must be in range 2...255.")

        result = (ctypes.c_uint8 * (payload_size + 4))()

        status = self._library.sbgc_py_get_realtime_data_custom(device, flags, result, payload_size)

        if status == NativeStatus.OK:
            return bytes(result[4:])

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "REALTIME_DATA_CUSTOM is unavailable: SBGC_REALTIME_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"REALTIME_DATA_CUSTOM failed in the native Serial API with native status {self._format_status(status)}."
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
                f"REALTIME_DATA_{version} is unavailable: SBGC_REALTIME_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"REALTIME_DATA_{version} failed in the native Serial API with native status {self._format_status(status)}."
        )

    def read_rc_inputs(self, device: int, sources: tuple[int, ...]) -> tuple[int, ...]:
        count = len(sources)

        if not 1 <= count <= 42:
            raise ValueError("Sources must contain between 1 and 42 elements.")

        source_buffer = (ctypes.c_uint8 * count)(*sources)
        value_buffer = (ctypes.c_int16 * count)()

        status = self._library.sbgc_py_read_rc_inputs(device, source_buffer, count, value_buffer)

        if status == NativeStatus.OK:
            return tuple(value_buffer)

        raise NativeError(
            f"READ_RC_INPUTS failed in the native Serial API with native status {self._format_status(status)}."
        )

    def _update_data_stream(
        self,
        function: object,
        device: int,
        config: NativeDataStreamInterval,
        *,
        need_confirmation: bool,
    ) -> NativeConfirmation | None:

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
            raise NativeError(
                "DATA_STREAM is unavailable: SBGC_REALTIME_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "DATA_STREAM confirmation is unavailable: "
                "SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"DATA_STREAM failed in the native Serial API with native status {self._format_status(status)}."
        )

    def start_data_stream(
        self,
        device: int,
        config: NativeDataStreamInterval,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._update_data_stream(
            self._library.sbgc_py_start_data_stream,
            device,
            config,
            need_confirmation=need_confirmation,
        )

    def stop_data_stream(
        self,
        device: int,
        config: NativeDataStreamInterval,
        *,
        need_confirmation: bool = False,
    ) -> NativeConfirmation | None:
        return self._update_data_stream(
            self._library.sbgc_py_stop_data_stream,
            device,
            config,
            need_confirmation=need_confirmation,
        )

    def request_debug_var_info_3(
        self,
        device: int,
        variables,
        start_index: int = 0,
    ) -> None:

        if not 0 <= start_index <= 0xFF:
            raise ValueError("Start_index must be in range 0...255.")

        count = len(variables)
        if not 1 <= count <= 0xFF:
            raise ValueError("Variables must contain from 1 to 255 items.")

        status = self._library.sbgc_py_request_debug_var_info_3(
            device, variables, start_index, count
        )

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "DEBUG_VAR_INFO_3 is unavailable: SBGC_REALTIME_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        raise NativeError(
            f"DEBUG_VAR_INFO_3 failed in the native Serial API with native status {self._format_status(status)}."
        )

    def request_debug_var_values_3(
        self, device: int, variables, masks: tuple[int, ...] | None = None
    ) -> None:

        if len(variables) == 0:
            raise ValueError("Variables must not be empty")

        mask_array = None
        if masks is not None:
            if not masks:
                raise ValueError("Masks must be None or contain at least one word.")
            if any(type(mask) is not int or not 0 <= mask <= 0xFFFF_FFFF for mask in masks):
                raise ValueError("Each mask must be an unsigned 32-bit integer.")

            mask_array = (ctypes.c_uint32 * len(masks))(*masks)

        request = NativeDebugVarValues3(
            debug_var_info_3=ctypes.cast(
                variables,
                ctypes.POINTER(NativeDebugVarInfo3),
            ),
            mask=(
                ctypes.cast(mask_array, ctypes.POINTER(ctypes.c_uint32))
                if mask_array is not None
                else None
            ),
            mask_count=0 if mask_array is None else len(mask_array),
        )

        status = self._library.sbgc_py_request_debug_var_values_3(device, ctypes.byref(request))

        if status == NativeStatus.OK:
            return

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "DEBUG_VAR_VALUES_3 is unavailable: SBGC_REALTIME_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        raise NativeError(
            f"DEBUG_VAR_VALUES_3 failed in the native Serial API with native status {self._format_status(status)}."
        )

    def select_imu_3(
        self,
        device: int,
        imu_type: int,
        action: int,
        time_ms: int,
        *,
        need_confirmation: bool = False,
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
            raise NativeError(
                "SELECT_IMU_3 is unavailable: SBGC_REALTIME_MODULE is disabled in serialAPI_Config.h."
            )

        if status == NativeStatus.CONFIRMATION_DISABLED:
            raise NativeError(
                "SELECT_IMU_3 confirmation is unavailable: SBGC_NEED_CONFIRM_CMD is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"SELECT_IMU_3 failed in the native Serial API with native status {self._format_status(status)}."
        )

    def control_quat_status(self, device: int, flags: int, payload_size: int) -> bytes:

        result = (ctypes.c_uint8 * payload_size)()
        status = self._library.sbgc_py_control_quat_status(device, flags, result, payload_size)

        if status == NativeStatus.OK:
            return bytes(result)

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "CONTROL_QUAT_STATUS is unavailable: SBGC_REALTIME_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"CONTROL_QUAT_STATUS failed in the native Serial API with native status {self._format_status(status)}."
        )

    def read_data_stream(
        self,
        device: int,
        cmd_id: int,
        size: int,
    ) -> bytes:

        if not 1 <= size <= 0xFF:
            raise ValueError("Size must be in range 1...255.")

        buffer = (ctypes.c_uint8 * size)()

        status = self._library.sbgc_py_read_data_stream(
            device,
            cmd_id,
            buffer,
            size,
        )

        if status == NativeStatus.OK:
            return bytes(buffer)

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "READ_DATA_STREAM is unavailable: SBGC_REALTIME_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        raise NativeError(
            f"READ_DATA_STREAM failed in the native Serial API with native status {self._format_status(status)}."
        )

    def get_angles(self, device: int) -> NativeAngles:

        result = NativeAngles()

        status = self._library.sbgc_py_get_angles(device, ctypes.byref(result))

        if status == NativeStatus.OK:
            return result

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_ANGLES is unavailable: SBGC_REALTIME_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"GET_ANGLES failed in the native Serial API with native status {self._format_status(status)}."
        )

    def get_angles_ext(self, device: int) -> NativeAnglesExt:

        result = NativeAnglesExt()

        status = self._library.sbgc_py_get_angles_ext(device, ctypes.byref(result))

        if status == NativeStatus.OK:
            return result

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_ANGLES_EXT is unavailable: SBGC_REALTIME_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"GET_ANGLES_EXT failed in the native Serial API with native status {self._format_status(status)}."
        )

    def get_board_info(self, device: int) -> NativeBoardInfo:

        result = NativeBoardInfo()

        status = self._library.sbgc_py_get_board_info(device, ctypes.byref(result))

        if status == NativeStatus.OK:
            return result

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_BOARD_INFO is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"GET_BOARD_INFO failed in the native Serial API with native status {self._format_status(status)}."
        )

    def get_board_info_3(self, device: int) -> NativeBoardInfo3:

        result = NativeBoardInfo3()

        status = self._library.sbgc_py_get_board_info_3(device, ctypes.byref(result))

        if status == NativeStatus.OK:
            return result

        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_BOARD_INFO_3 is unavailable: SBGC_SERVICE_MODULE is disabled in serialAPI_Config.h."
            )

        raise NativeError(
            f"GET_BOARD_INFO_3 failed in the native Serial API with native status {self._format_status(status)}."
        )


class NativeLibrary(SerialApiLibrary):
    """Common SerialAPI wrapper configured for the native Win32 transport."""

    def _configure_functions(self) -> None:
        super()._configure_functions()
        self._library.sbgc_py_open_com.argtypes = [ctypes.c_char_p, ctypes.c_uint32]
        self._library.sbgc_py_open_com.restype = ctypes.c_void_p
