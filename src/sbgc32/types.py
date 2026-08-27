from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import Mapping


class MotorsOffMode(IntEnum):
    """ Stopping mode accepted by CMD_MOTORS_OFF """
    NORMAL = 0
    BREAK = 1
    SAFE_STOP = 2


class BeeperMode(IntFlag):
    """ Standard CMD_BEEP_SOUND signals; CUSTOM_MELODY is a motor-sound melody. """

    CALIBRATE = 1 << 0
    CONFIRM = 1 << 1
    ERROR = 1 << 2
    CLICK = 1 << 4
    COMPLETE = 1 << 5
    INTRO = 1 << 6
    CUSTOM_MELODY = 1 << 15


class AutoPidFlag(IntFlag):
    """Configuration bits accepted by the legacy CMD_AUTO_PID command."""

    STOP = 0
    ROLL = 1 << 0
    PITCH = 1 << 1
    YAW = 1 << 2
    SEND_GUI = 1 << 3
    KEEP_CURRENT = 1 << 4
    TUNE_LPF_FREQUENCY = 1 << 5
    ALL_PROFILES = 1 << 6


class AutoPid2Action(IntEnum):
    START = 1
    START_SAVE = 2
    SAVE = 3
    STOP = 5
    READ = 6


class AutoPid2AxisFlag(IntFlag):
    ENABLED = 1 << 0
    TUNE_LPF = 1 << 1


class AutoPid2GeneralFlag(IntFlag):
    START_FROM_CURRENT_VALUES = 1 << 0
    SAVE_RESULT_TO_ALL_PROFILES = 1 << 1
    TUNE_GAIN_ONLY = 1 << 2
    AUTOSAVE = 1 << 4
    RUN_AT_SYSTEM_START_TUNE_ALL = 1 << 14
    RUN_AT_SYSTEM_START_TUNE_GAIN = 1 << 15


class SyncMotorAxis(IntEnum):
    ROLL = 0
    PITCH = 1
    YAW = 2


class DebugPortAction(IntEnum):
    STOP = 0
    START = 1


class DebugPortFilter(IntFlag):
    """Packet classes excluded from Debug Port output (zero forwards all)."""

    REALTIME_DATA_3             = 1 << 0
    REALTIME_DATA_4             = 1 << 1
    REALTIME_DATA_CUSTOM        = 1 << 2
    DEBUG_VARS_3                = 1 << 3
    MAVLINK_DEBUG               = 1 << 4
    GET_ANGLES                  = 1 << 5
    GET_ANGLES_EXT              = 1 << 6
    BODE_TEST_DATA              = 1 << 7
    HELPER_DATA                 = 1 << 8
    AHRS_HELPER                 = 1 << 9
    GYRO_CORRECTION             = 1 << 10
    CONTROL                     = 1 << 11
    SET_ADJ_VARS                = 1 << 12
    API_VIRTUAL_CHANNEL_CONTROL = 1 << 13
    API_VIRTUAL_CHANNEL_HIGH_RES = 1 << 14


@dataclass(frozen=True, slots=True)
class StateVars:
    """Persistent maintenance counters returned by CMD_READ_STATE_VARS."""

    step_signal_vars: bytes
    sub_error: int
    max_acc: int
    work_time: int
    startup_count: int
    max_current: int
    imu_temp_min: int
    imu_temp_max: int
    mcu_temp_min: int
    mcu_temp_max: int
    shock_count: bytes
    energy_time: int
    energy: float
    avg_current_time: int
    avg_current: float
    reserved: bytes = b"\x00" * 152


@dataclass(frozen=True, slots=True)
class DebugPortPacket:
    time_ms: int
    port_and_direction: int
    command_id: int
    payload_buffer: bytes


@dataclass(frozen=True, slots=True)
class AutoPidConfig:
    """Legacy automatic PID tuning request (firmware before 2.73)."""

    profile_id: int = 0
    config_flags: int = AutoPidFlag.STOP
    gain_vs_stability: int = 0
    momentum: int = 0
    action: int = 0


@dataclass(frozen=True, slots=True)
class AutoPid2Axis:
    """One axis configuration for CMD_AUTO_PID2."""

    axis_flags: int = 0
    gain: int = 0
    stimulus_gain: int = 0
    effective_frequency: int = 0
    problem_frequency: int = 0
    problem_margin: int = 0


@dataclass(frozen=True, slots=True)
class AutoPid2Config:
    """Automatic PID v2 request (firmware 2.73+)."""

    action: AutoPid2Action | int
    command_flags: int = 0
    config_version: int = 1
    axes: tuple[AutoPid2Axis, AutoPid2Axis, AutoPid2Axis] = (
        AutoPid2Axis(), AutoPid2Axis(), AutoPid2Axis(),
    )
    general_flags: int = 0
    test_frequency_from: int = 0
    test_frequency_to: int = 0
    multi_position_flags: int = 0
    multi_position_angles: tuple[int, int, int, int] = (0, 0, 0, 0)


@dataclass(frozen=True, slots=True)
class AutoPidAxisState:
    tracking_error: float


@dataclass(frozen=True, slots=True)
class AutoPidState:
    p: tuple[int, int, int]
    i: tuple[int, int, int]
    d: tuple[int, int, int]
    lpf_frequency: tuple[int, int, int]
    iteration_count: int
    axes: tuple[AutoPidAxisState, AutoPidAxisState, AutoPidAxisState]


@dataclass(frozen=True, slots=True)
class SyncMotorsConfig:
    """Power pulse used by CMD_SYNC_MOTORS; it moves the selected motor."""

    axis: SyncMotorAxis | int
    power: int
    time_ms: int
    angle: int = 0


class ControlMode(IntEnum):
    """ Low four bits of one CMD_CONTROL axis mode byte """

    NO_CONTROL                  = 0 # Give back control to RC
    SPEED                       = 1 # Continuous rotation
    ANGLE                       = 2 # Absolute angle
    SPEED_ANGLE                 = 3 # Speed with position correction
    RC                          = 4 # RC signal
    ANGLE_REL_FRAME             = 5 # Angle relative frame IMU
    RC_HIGH_RES                 = 6 # RC signal
    IGNORE                      = 7 # Do not change axis
    ANGLE_SHORTEST              = 8 # Shortest path to angle


class ControlFlag(IntFlag):
    """ High four bits that may be ORed with :class:ControlMode """

    MIX_FOLLOW = 1 << 4
    TARGET_PRECISE = 1 << 5
    AUTO_TASK = 1 << 6
    FORCE_RC_SPEED = 1 << 6
    HIGH_RES_SPEED = 1 << 7


class ControlConfigFlag(IntFlag):
    """ Additional CMD_CONTROL_CONFIG rules, except confirmation selection. """

    NO_CONFIRM = 1 << 0
    SERVO_MODE_ENABLE = 1 << 1
    SERVO_MODE_DISABLE = 1 << 2
    LPF_EXTENDED_RANGE = 1 << 3


@dataclass(frozen=True, slots=True)
class ControlAxisConfig:
    """ Filtering and motion-profile rules for one CMD_CONTROL axis. """

    angle_lpf: int = 0
    speed_lpf: int = 0
    rc_lpf: int = 0
    acceleration_limit: int = 0
    jerk_slope: int = 0


@dataclass(frozen=True, slots=True)
class ControlConfig:
    """ Rules used by CMD_CONTROL_CONFIG for roll, pitch, and yaw. """

    timeout_ms: int = 0
    channel_priorities: tuple[int, int, int, int, int] = (0, 0, 0, 0, 0)
    axes: tuple[ControlAxisConfig, ControlAxisConfig, ControlAxisConfig] = (
        ControlAxisConfig(),
        ControlAxisConfig(),
        ControlAxisConfig(),
    )
    rc_expo_rate: int = 0
    flags: int = ControlConfigFlag.NO_CONFIRM
    euler_order: int = 0


class ConfirmationStatus(IntEnum):
    """ Status of a CMD_CONFIRM request """

    NOT_RECEIVED = 0
    RECEIVED = 1
    ERROR = 2


class RcInputSource (IntEnum):
    NO_SIGNAL                   = 0
    ROLL                        = 1
    PITCH                       = 2
    EXTERNAL_FC_ROLL            = 3
    EXTERNAL_FC_PITCH           = 4
    YAW                         = 5

    ADC_1                       = 0x21
    ADC_2                       = 0x22
    ADC_3                       = 0x23
    ADC_4                       = 0x24

    SERIAL_VIRTUAL_1            = 0x41
    API_VIRTUAL_1               = 0x81
    API_VIRTUAL_2               = 0x82
    API_VIRTUAL_3               = 0x83
    API_VIRTUAL_4               = 0x84
    API_VIRTUAL_5               = 0x85
    API_VIRTUAL_6               = 0x86
    API_VIRTUAL_7               = 0x87
    API_VIRTUAL_8               = 0x88
    API_VIRTUAL_9               = 0x89
    API_VIRTUAL_10              = 0x8A
    API_VIRTUAL_11              = 0x8B
    API_VIRTUAL_12              = 0x8C
    API_VIRTUAL_13              = 0x8D
    API_VIRTUAL_14              = 0x8E
    API_VIRTUAL_15              = 0x8F
    API_VIRTUAL_16              = 0x90
    API_VIRTUAL_17              = 0x91
    API_VIRTUAL_18              = 0x92
    API_VIRTUAL_19              = 0x93
    API_VIRTUAL_20              = 0x94
    API_VIRTUAL_21              = 0x95
    API_VIRTUAL_22              = 0x96
    API_VIRTUAL_23              = 0x97
    API_VIRTUAL_24              = 0x98
    API_VIRTUAL_25              = 0x99
    API_VIRTUAL_26              = 0x9A
    API_VIRTUAL_27              = 0x9B
    API_VIRTUAL_28              = 0x9C
    API_VIRTUAL_29              = 0x9D
    API_VIRTUAL_30              = 0x9E
    API_VIRTUAL_31              = 0x9F
    API_VIRTUAL_32              = 0xA0

    STEP_SIGNAL_1               = 0xA1


@dataclass(frozen=True, slots=True)
class DebugVarInfo:
    index: int
    name: str
    raw_type: int
    raw_value: int | None = None
    value: int | float | None = None


class ImuType(IntEnum):
    """IMU selected by CMD_SELECT_IMU_3."""

    CURRENTLY_ACTIVE = 0
    MAIN = 1
    FRAME = 2


class SelectImuAction(IntEnum):
    """Action requested by CMD_SELECT_IMU_3."""

    SIMPLE_SELECT = 0
    REGULAR_CALIBRATION = 1
    RESET_ALL_CALIBRATION_AND_RESTART = 2
    TEMPERATURE_CALIBRATION = 3
    ENABLE_TEMPERATURE_CALIBRATION_DATA_IF_PRESENT = 4
    DISABLE_TEMPERATURE_CALIBRATION_DATA = 5
    RESTORE_FACTORY_CALIBRATION = 6
    COPY_CALIBRATION_FROM_MAIN_EEPROM = 7


class ControlQuatMode(IntEnum):
    DISABLED = 0
    SPEED = 1
    ATTITUDE = 2
    SPEED_ATTITUDE = 5
    SPEED_LIMITED = 9


class ControlQuatStatusFlag(IntFlag):
    MODE_AND_FLAGS = 1 << 0
    TARGET_ATTITUDE = 1 << 1
    SETPOINT_ATTITUDE = 1 << 2
    ACTUAL_ATTITUDE = 1 << 3
    TARGET_SPEED = 1 << 4
    SETPOINT_SPEED = 1 << 5
    ACTUAL_SPEED = 1 << 6
    TARGET_ATTITUDE_PACKED = 1 << 7
    SETPOINT_ATTITUDE_PACKED = 1 << 8
    ACTUAL_ATTITUDE_PACKED = 1 << 9


@dataclass(frozen=True, slots=True)
class ControlQuatStatus:
    """Selected CMD_CONTROL_QUAT_STATUS fields.

    Speed fields are raw signed protocol units; their scale depends on the
    controller firmware's quaternion-control implementation.
    """

    requested_fields: ControlQuatStatusFlag
    mode: ControlQuatMode | int | None = None
    control_flags: int | None = None
    target_attitude: tuple[float, float, float, float] | None = None
    setpoint_attitude: tuple[float, float, float, float] | None = None
    actual_attitude: tuple[float, float, float, float] | None = None
    target_speed_raw: tuple[int, int, int] | None = None
    setpoint_speed_raw: tuple[int, int, int] | None = None
    actual_speed_raw: tuple[int, int, int] | None = None
    target_attitude_packed: bytes | None = None
    setpoint_attitude_packed: bytes | None = None
    actual_attitude_packed: bytes | None = None
    raw_payload: bytes = b""
    raw_payload: bytes = b""


class DataStreamCommand(IntEnum):
    REALTIME_DATA_3 = 23
    REALTIME_DATA_4 = 25
    REALTIME_DATA_CUSTOM = 88
    AHRS_HELPER = 56

    EVENT = 102

    CAN_DRIVER_TELEMETRY = 127
    EXT_MOTORS_STATE = 131


@dataclass(frozen=True, slots=True)
class DataStreamConfig:
    command: DataStreamCommand
    interval_ms: int
    config: bytes = b""
    sync_to_data: bool = False
    # and 9 reserved bytes

@dataclass(frozen=True, slots=True)
class CommandConfirmation:
    """ CMD_CONFIRM or CMD_ERROR received for a previously sent command """

    command_id: int
    status: ConfirmationStatus
    command_data: int
    error_code: int
    error_data: bytes


@dataclass(frozen=True, slots=True)
class AdjustableVariable:
    """ One integer adjustable variable used by CMD_SET/GET_ADJ_VARS_VAL.

    id is the firmware-specific adjustable-variable ID and value is
    the raw signed 32-bit value used by the board. The command changes RAM only.
    """

    id: int
    value: int


@dataclass(frozen=True, slots=True)
class ControlAxis:
    """ One CMD_CONTROL axis using degrees and degrees per second.

    angle is converted to the 16-bit SerialAPI angle representation and
    speed to its standard speed representation by SimpleBGC.control.
    For RC and RC_HIGH_RES modes, angle remains the raw RC value
    required by the protocol rather than an angle in degrees.
    """

    mode: int = ControlMode.NO_CONTROL
    speed: float = 0.0
    angle: float = 0.0


class RealtimeDataCustomFlag(IntFlag):
    """ Fields requested through CMD_REALTIME_DATA_CUSTOM. """

    IMU_ANGLES = 1 << 0
    TARGET_ANGLES = 1 << 1
    TARGET_SPEED = 1 << 2
    STATOR_ROTOR_ANGLE = 1 << 3
    GYRO_DATA = 1 << 4
    RC_DATA = 1 << 5
    Z_VECTOR_H_VECTOR = 1 << 6
    RC_CHANNELS = 1 << 7
    ACC_DATA = 1 << 8
    MOTOR4_CONTROL = 1 << 9
    AHRS_DEBUG_INFO = 1 << 10
    ENCODER_RAW24 = 1 << 11
    IMU_ANGLES_RAD = 1 << 12
    SCRIPT_VARS_FLOAT = 1 << 13
    SCRIPT_VARS_INT16 = 1 << 14
    SYSTEM_POWER_STATE = 1 << 15
    FRAME_CAM_RATE = 1 << 16
    IMU_ANGLES_20 = 1 << 17
    TARGET_ANGLES_20 = 1 << 18
    COMM_ERRORS = 1 << 19
    SYSTEM_STATE = 1 << 20
    IMU_QUAT = 1 << 21
    TARGET_QUAT = 1 << 22
    IMU_TO_FRAME_QUAT = 1 << 23
    ADC_CH_RAW = 1 << 24
    SW_LIMITS_DIST = 1 << 25
    FOLLOW_DIST = 1 << 26
    EXT_TARGET_LIMIT = 1 << 27


@dataclass(frozen=True, slots=True)
class Axis3:
    """ Values for roll, pitch, and yaw. """

    roll: float
    pitch: float
    yaw: float


@dataclass(frozen=True, slots=True)
class Angles:
    """ class for angles """ 
    imu: Axis3
    target: Axis3
    target_speed: Axis3


@dataclass(frozen=True, slots=True)
class AxisGAE:
    """ CMD_GET_ANGLES_EXT result. """

    imu_angle: int
    target_angle: int
    frame_cam_angle: int
    reserved: bytes

    @property
    def IMU_Angle(self) -> int:
        return self.imu_angle

    @property
    def targetAngle(self) -> int:
        return self.target_angle

    @property
    def frameCamAngle(self) -> int:
        return self.frame_cam_angle



@dataclass(frozen=True, slots=True)
class AnglesExt:

    axis_gae: tuple[AxisGAE, AxisGAE, AxisGAE]

    @property
    def AxisGAE(self) -> tuple[AxisGAE, AxisGAE, AxisGAE]:
        return self.axis_gae

    @property
    def imu(self) -> Axis3:
        return Axis3(*(axis.imu_angle * (360.0 / 16384.0) for axis in self.axis_gae))

    @property
    def target(self) -> Axis3:
        return Axis3(*(axis.target_angle * (360.0 / 16384.0) for axis in self.axis_gae))

    @property
    def frame_cam(self) -> Axis3:
        return Axis3(*(axis.frame_cam_angle * (360.0 / 16384.0) for axis in self.axis_gae))


@dataclass(frozen=True, slots=True)
class ScriptDebugInfo:
    """ CMD_SCRIPT_DEBUG result. """

    current_command_counter: int
    error_code: int

    @property
    def curComCounter(self) -> int:
        return self.current_command_counter

    @property
    def errorCode(self) -> int:
        return self.error_code


@dataclass(frozen=True, slots=True)
class AxisRealtimeData:
    """ One raw sbgcAxisRTD_t record. """

    acc_data: int
    gyro_data: int


@dataclass(frozen=True, slots=True)
class RealtimeDataCustom:

    flags: RealtimeDataCustomFlag
    timestamp_ms: int
    fields: Mapping[RealtimeDataCustomFlag, object]
    raw_payload: bytes


@dataclass(frozen=True, slots=True)
class RealtimeData3:

    axis_rtd: tuple[AxisRealtimeData, AxisRealtimeData, AxisRealtimeData]
    serial_error_count: int
    system_error: int
    system_sub_error: int
    reserved: bytes
    rc_roll: int
    rc_pitch: int
    rc_yaw: int
    rc_cmd: int
    ext_fc_roll: int
    ext_fc_pitch: int
    imu_angle: tuple[int, int, int]
    frame_imu_angle: tuple[int, int, int]
    target_angle: tuple[int, int, int]
    cycle_time: int
    i2c_error_count: int
    error_code: int
    bat_level: int
    rt_data_flags: int
    cur_imu: int
    cur_profile: int
    motor_power: tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class RealtimeData4(RealtimeData3):

    frame_cam_angle: tuple[int, int, int]
    reserved1: int
    balance_error: tuple[int, int, int]
    current: int
    mag_data: tuple[int, int, int]
    imu_temperature: int
    frame_imu_temperature: int
    imu_g_error: int
    imu_h_error: int
    motor_out: tuple[int, int, int]
    calib_mode: int
    can_imu_ext_sens_error: int
    actual_angle: tuple[int, int, int]
    system_state_flags: int
    reserved2: bytes


@dataclass(frozen=True, slots=True)
class BoardInfo:

    board_ver: int
    firmware_ver: int
    state_flags: int
    board_features: int
    connection_flag: int
    firmware_extra_id: int
    board_features_ext: int
    main_imu_sensor_model: int
    frame_imu_sensor_model: int
    build_number: int
    base_firmware_ver: int

    @property
    def board_version(self) -> str:
        return f"{self.board_ver // 10}.{self.board_ver % 10}"

    @property
    def firmware_version(self) -> str:
        major = self.firmware_ver // 1000
        minor = (self.firmware_ver % 1000) // 10
        revision = self.firmware_ver % 10
        if revision and self.firmware_ver < 2730:
            return f"{major}.{minor}b{revision}"
        if revision:
            return f"{major}.{minor}.{revision}"
        return f"{major}.{minor}"


@dataclass(frozen=True, slots=True)
class BoardInfo3:
    """Extended board information returned by CMD_BOARD_INFO_3. """

    device_id: bytes
    mcu_id: bytes
    eeprom_size: int
    script_slot_sizes: tuple[int, ...]
    profile_set_slots: int
    profile_set_current: int
    flash_size_pages: int
    imu_calib_info: bytes
    hardware_flags: int
    board_features_ext2: int
    can_driver_main_limit: int
    can_driver_aux_limit: int
    adjustable_variables_total: int
