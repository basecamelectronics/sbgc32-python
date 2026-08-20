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
