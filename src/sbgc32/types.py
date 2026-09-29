"""Public value objects and protocol enumerations.

The module contains no transport logic. Dataclasses are immutable decoded
command results or command payloads; their constructor parameters are the
fields shown in the generated API reference. ``IntEnum`` and ``IntFlag``
classes represent the integer values and bit masks defined by the SerialAPI.

All public classes are available through ``sbgc32.types`` and through the
``SimpleBGC.types`` namespace. They are also re-exported from :mod:`sbgc32`
for applications that prefer direct imports.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum, IntFlag


class SerialApiStatus(IntEnum):
    TX_RX_OK = 0
    TX_BUS_BUSY_ERROR = 2
    RX_EMPTY_BUFF_ERROR = 3
    RX_BUFFER_REALTIME_ERROR = 4
    RX_HEADER_CHECKSUM_ERROR = 5
    RX_PAYLOAD_CHECKSUM_ERROR = 6
    RX_NOT_FOUND_ERROR = 7
    RX_BUFFER_OVERFLOW_ERROR = 8


class ControllerErrorCode(IntEnum):
    NO_ERROR = 0
    CMD_SIZE = 1
    WRONG_PARAMS = 2
    CRYPTO = 4
    UNKNOWN_COMMAND = 6
    WRONG_STATE = 8
    NOT_SUPPORTED = 9
    OPERATION_FAILED = 10
    TEMPORARY = 11


class TransparentCommandPort(IntEnum):
    """Serial port on the destination device for CMD_TRANSPARENT_SAPI."""

    DEVICE_1 = 0
    DEVICE_2 = 1
    DEVICE_3 = 2
    DEVICE_4 = 3


class TransparentCommandDevice(IntEnum):
    """Destination device for CMD_TRANSPARENT_SAPI."""

    SBGC32 = 4
    GPS_IMU = 5
    CAN_IMU_MAIN = 6
    CAN_IMU_FRAME = 7
    GPS_SPLIT_RECEIVER = 8
    CAN_SERIAL_HUB_1 = 9
    CAN_SERIAL_HUB_2 = 10
    CAN_DRIVER_1 = 11
    CAN_DRIVER_2 = 12
    CAN_DRIVER_3 = 13
    CAN_DRIVER_4 = 14


class TransparentCommandFlag(IntFlag):
    """Optional behaviour flags for CMD_TRANSPARENT_SAPI."""

    SKIP_DATA_PACKET = 0
    BLOCK_AND_WAIT = 1 << 6


class EepromFileId(IntEnum):
    SCRIPT = 1
    IMU_CALIB = 3
    COGGING_CORRECTION = 4
    ADJ_VAR_LUT = 5
    PROFILE_SET = 6
    PARAMS = 7
    TUNE = 8
    CAN_DRIVER = 10


class ProfileId(IntEnum):
    PROFILE_1 = 0
    PROFILE_2 = 1
    PROFILE_3 = 2
    PROFILE_4 = 3
    PROFILE_5 = 4
    CURRENT = 0xFF


class ProfileSet(IntEnum):
    SET_1 = 1
    SET_2 = 2
    SET_3 = 3
    SET_4 = 4
    SET_5 = 5
    BACKUP = 6


class ProfileSetAction(IntEnum):
    SAVE = 1
    CLEAR = 2
    LOAD = 3


class ProfileWritingAction(IntEnum):
    STOP = 0
    START = 1


class ExternalImuCommandType(IntEnum):
    TX = 0
    RX = 1
    TX_RX = 2


class ExternalSensorCommandFlag(IntFlag):
    LOW_PRIORITY = 0
    HIGH_PRIORITY = 1


def transparent_command_target(
    port: TransparentCommandPort | int,
    device: TransparentCommandDevice | int,
    flag: TransparentCommandFlag | int = TransparentCommandFlag.SKIP_DATA_PACKET,
) -> int:
    """Pack a transparent-command target byte from its protocol fields."""

    try:
        port = TransparentCommandPort(port)
        device = TransparentCommandDevice(device)
        flag = TransparentCommandFlag(flag)
    except ValueError as error:
        raise ValueError("invalid CMD_TRANSPARENT_SAPI target field") from error

    if flag not in (
        TransparentCommandFlag.SKIP_DATA_PACKET,
        TransparentCommandFlag.BLOCK_AND_WAIT,
    ):
        raise ValueError("unsupported CMD_TRANSPARENT_SAPI flag")

    return int(port | device | flag)


class MotorsOffMode(IntEnum):
    """Stopping mode accepted by CMD_MOTORS_OFF"""

    NORMAL = 0
    BREAK = 1
    SAFE_STOP = 2


class BeeperMode(IntFlag):
    """Standard CMD_BEEP_SOUND signals; CUSTOM_MELODY is a motor-sound melody."""

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

    REALTIME_DATA_3 = 1 << 0
    REALTIME_DATA_4 = 1 << 1
    REALTIME_DATA_CUSTOM = 1 << 2
    DEBUG_VARS_3 = 1 << 3
    MAVLINK_DEBUG = 1 << 4
    GET_ANGLES = 1 << 5
    GET_ANGLES_EXT = 1 << 6
    BODE_TEST_DATA = 1 << 7
    HELPER_DATA = 1 << 8
    AHRS_HELPER = 1 << 9
    GYRO_CORRECTION = 1 << 10
    CONTROL = 1 << 11
    SET_ADJ_VARS = 1 << 12
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
    """One serial command mirrored from another controller port."""

    time_ms: int
    port_and_direction: int
    command_id: int
    payload_buffer: bytes
    payload_size: int


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
    """One axis configuration for CMD_AUTO_PID2.

    The frequency fields are expressed in Hz, as in the GUI. ``problem_margin``
    is in 0.1 dB.
    """

    axis_flags: int = 0
    gain: int = 0
    stimulus_gain: int = 0
    effective_frequency: int = 0
    problem_frequency: int = 0
    problem_margin: int = 0


@dataclass(frozen=True, slots=True)
class AutoPid2Config:
    """Automatic PID v2 request (firmware 2.73+).

    ``test_frequency_from`` is in Hz with a 0.1 Hz resolution (0..25.5 Hz).
    ``test_frequency_to`` is in Hz with a 2 Hz resolution (0..510 Hz).
    These are physical units rather than the two differently scaled protocol
    bytes used by CMD_AUTO_PID2.
    """

    action: AutoPid2Action | int
    command_flags: int = 0
    config_version: int = 1
    axes: tuple[AutoPid2Axis, AutoPid2Axis, AutoPid2Axis] = (
        AutoPid2Axis(),
        AutoPid2Axis(),
        AutoPid2Axis(),
    )
    general_flags: int = 0
    test_frequency_from: float = 0.0
    test_frequency_to: float = 0.0
    multi_position_flags: int = 0
    multi_position_angles: tuple[int, int, int, int] = (0, 0, 0, 0)


@dataclass(frozen=True, slots=True)
class AutoPidAxisState:
    tracking_error: float


@dataclass(frozen=True, slots=True)
class AutoPidState:
    """Latest CMD_AUTO_PID packet; ``p``, ``i``, and ``d`` are raw bytes."""

    p: tuple[int, int, int]
    i: tuple[int, int, int]
    d: tuple[int, int, int]
    lpf_frequency: tuple[int, int, int]
    iteration_count: int
    axes: tuple[AutoPidAxisState, AutoPidAxisState, AutoPidAxisState]


@dataclass(frozen=True, slots=True)
class PidValues:
    """Raw P/I/D bytes stored in one profile."""

    profile_id: int
    p: tuple[int, int, int]
    i: tuple[int, int, int]
    d: tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class SyncMotorsConfig:
    """Power pulse used by CMD_SYNC_MOTORS; it moves the selected motor."""

    axis: SyncMotorAxis | int
    power: int
    time_ms: int
    angle: int = 0


class ControlMode(IntEnum):
    """Low four bits of one CMD_CONTROL axis mode byte"""

    NO_CONTROL = 0  # Give back control to RC
    SPEED = 1  # Continuous rotation
    ANGLE = 2  # Absolute angle
    SPEED_ANGLE = 3  # Speed with position correction
    RC = 4  # RC signal
    ANGLE_REL_FRAME = 5  # Angle relative frame IMU
    RC_HIGH_RES = 6  # RC signal
    IGNORE = 7  # Do not change axis
    ANGLE_SHORTEST = 8  # Shortest path to angle


class ControlFlag(IntFlag):
    """High four bits that may be ORed with :class:ControlMode"""

    MIX_FOLLOW = 1 << 4
    TARGET_PRECISE = 1 << 5
    AUTO_TASK = 1 << 6
    FORCE_RC_SPEED = 1 << 6
    HIGH_RES_SPEED = 1 << 7


class ControlConfigFlag(IntFlag):
    """Additional CMD_CONTROL_CONFIG rules, except confirmation selection."""

    NO_CONFIRM = 1 << 0
    SERVO_MODE_ENABLE = 1 << 1
    SERVO_MODE_DISABLE = 1 << 2
    LPF_EXTENDED_RANGE = 1 << 3
    LPF_FREQUENCY_HZ = 1 << 4


class ControlExtDataSet(IntFlag):
    ROLL_SPEED = 1 << 0
    ROLL_ANGLE = 1 << 1
    ROLL_ANGLE_HIGH_RES = 1 << 2
    ROLL_SPEED_HIGH_RES = 1 << 3
    PITCH_SPEED = 1 << 5
    PITCH_ANGLE = 1 << 6
    PITCH_ANGLE_HIGH_RES = 1 << 7
    PITCH_SPEED_HIGH_RES = 1 << 8
    YAW_SPEED = 1 << 10
    YAW_ANGLE = 1 << 11
    YAW_ANGLE_HIGH_RES = 1 << 12
    YAW_SPEED_HIGH_RES = 1 << 13


class ControlExtFlag(IntFlag):
    DISABLE_ANGLE_ERROR_CORRECTION = 1 << 0


@dataclass(frozen=True, slots=True)
class ControlExtAxis:
    mode: ControlMode | int = ControlMode.NO_CONTROL
    flags: ControlExtFlag | int = 0
    speed: int = 0
    angle: int = 0


@dataclass(frozen=True, slots=True)
class ControlExt:
    data_set: ControlExtDataSet | int
    axes: tuple[ControlExtAxis, ControlExtAxis, ControlExtAxis]


class ControlQuatFlag(IntFlag):
    NEED_CONFIRM = 1 << 0
    ATTITUDE_PACKED = 1 << 1
    ATTITUDE_LIMITED_180 = 1 << 2
    ATTITUDE_REMOVE_ABSENT_AXES = 1 << 3
    AUTO_TASK = 1 << 6


@dataclass(frozen=True, slots=True)
class ControlQuat:
    mode: "ControlQuatMode | int"
    flags: ControlQuatFlag | int = 0
    attitude: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    speed: tuple[float, float, float] = (0.0, 0.0, 0.0)


class ControlQuatConfigParameter(IntFlag):
    MAX_SPEED = 1 << 0
    ACCELERATION_LIMIT = 1 << 1
    JERK_SLOPE = 1 << 2
    FLAGS = 1 << 3
    ATTITUDE_LPF_FREQUENCY = 1 << 4
    SPEED_LPF_FREQUENCY = 1 << 5


class ControlQuatConfigFlag(IntFlag):
    MOTION_PROFILE_SPLIT_XYZ = 1 << 0


@dataclass(frozen=True, slots=True)
class ControlQuatConfig:
    data_set: ControlQuatConfigParameter | int
    max_speed: tuple[int, int, int] = (0, 0, 0)
    acceleration_limit: tuple[int, int, int] = (0, 0, 0)
    jerk_slope: tuple[int, int, int] = (0, 0, 0)
    flags: ControlQuatConfigFlag | int = 0
    attitude_lpf_frequency: int = 0
    speed_lpf_frequency: int = 0


class ExternalMotor(IntFlag):
    ID_1 = 1 << 0
    ID_2 = 1 << 1
    ID_3 = 1 << 2
    ID_4 = 1 << 3
    ID_5 = 1 << 4
    ID_6 = 1 << 5
    ID_7 = 1 << 6


class ExternalMotorAction(IntEnum):
    OFF_FLOATING = 1
    OFF_BRAKE = 2
    OFF_SAFE = 3
    ON = 4
    HOME_POSITION = 5
    SEARCH_HOME = 6


class ExternalMotorParameter(IntFlag):
    SETPOINT_32BIT = 1 << 0
    PARAM1_16BIT = 1 << 1
    PARAM1_32BIT = 1 << 2


@dataclass(frozen=True, slots=True)
class ExternalMotorControl:
    setpoint: int
    param1: int = 0


class ExternalMotorsControlConfigParameter(IntFlag):
    MODE = 1 << 0
    MAX_SPEED = 1 << 1
    MAX_ACCELERATION = 1 << 2
    JERK_SLOPE = 1 << 3
    MAX_TORQUE = 1 << 4


class ExternalMotorsControlMode(IntEnum):
    POSITION = 0
    SPEED = 1
    TORQUE = 2


@dataclass(frozen=True, slots=True)
class ExternalMotorsControlConfig:
    motors: ExternalMotor | int
    data_set: ExternalMotorsControlConfigParameter | int
    mode: ExternalMotorsControlMode | int = ExternalMotorsControlMode.POSITION
    max_speed: int = 0
    max_acceleration: int = 0
    jerk_slope: int = 0
    max_torque: int = 0


@dataclass(frozen=True, slots=True)
class ControlAxisConfig:
    """Filtering and motion-profile rules for one CMD_CONTROL axis."""

    angle_lpf: int = 0
    speed_lpf: int = 0
    rc_lpf: int = 0
    acceleration_limit: int = 0
    jerk_slope: int = 0


@dataclass(frozen=True, slots=True)
class ControlConfig:
    """Rules used by CMD_CONTROL_CONFIG for roll, pitch, and yaw."""

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
    """Status of a CMD_CONFIRM request"""

    NOT_RECEIVED = 0
    RECEIVED = 1
    ERROR = 2


class RcInputSource(IntEnum):
    NO_SIGNAL = 0
    ROLL = 1
    PITCH = 2
    EXTERNAL_FC_ROLL = 3
    EXTERNAL_FC_PITCH = 4
    YAW = 5

    ADC_1 = 0x21
    ADC_2 = 0x22
    ADC_3 = 0x23
    ADC_4 = 0x24

    SERIAL_VIRTUAL_1 = 0x41
    API_VIRTUAL_1 = 0x81
    API_VIRTUAL_2 = 0x82
    API_VIRTUAL_3 = 0x83
    API_VIRTUAL_4 = 0x84
    API_VIRTUAL_5 = 0x85
    API_VIRTUAL_6 = 0x86
    API_VIRTUAL_7 = 0x87
    API_VIRTUAL_8 = 0x88
    API_VIRTUAL_9 = 0x89
    API_VIRTUAL_10 = 0x8A
    API_VIRTUAL_11 = 0x8B
    API_VIRTUAL_12 = 0x8C
    API_VIRTUAL_13 = 0x8D
    API_VIRTUAL_14 = 0x8E
    API_VIRTUAL_15 = 0x8F
    API_VIRTUAL_16 = 0x90
    API_VIRTUAL_17 = 0x91
    API_VIRTUAL_18 = 0x92
    API_VIRTUAL_19 = 0x93
    API_VIRTUAL_20 = 0x94
    API_VIRTUAL_21 = 0x95
    API_VIRTUAL_22 = 0x96
    API_VIRTUAL_23 = 0x97
    API_VIRTUAL_24 = 0x98
    API_VIRTUAL_25 = 0x99
    API_VIRTUAL_26 = 0x9A
    API_VIRTUAL_27 = 0x9B
    API_VIRTUAL_28 = 0x9C
    API_VIRTUAL_29 = 0x9D
    API_VIRTUAL_30 = 0x9E
    API_VIRTUAL_31 = 0x9F
    API_VIRTUAL_32 = 0xA0

    STEP_SIGNAL_1 = 0xA1


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


class AhrsHelperDirection(IntEnum):
    GET = 0
    SET = 1


class AhrsHelperLocation(IntEnum):
    CAMERA_PLATFORM = 0
    FRAME = 1 << 1


class AhrsHelperCorrection(IntEnum):
    BOTH_VECTORS = 0
    Z_VECTOR = 1 << 4
    H_VECTOR = 1 << 5


class AhrsHelperTranslation(IntEnum):
    BOTH_VECTORS = 0
    Z_VECTOR = 1 << 6
    H_VECTOR = 1 << 7


class AhrsHelperReference(IntEnum):
    SAME_AS_FRAME_IMU = 0
    ON_THE_FRAME = 1 << 8
    BELOW_OUTER = 1 << 9


class AhrsHelperOption(IntFlag):
    NONE = 0
    USE_AS_REFERENCE_ONLY = 1 << 2
    TRANSLATE_FROM_CAMERA_TO_FRAME = 1 << 3
    DISABLE_INTERNAL_CORRECTION = 1 << 10


class HelperDataFlag(IntFlag):
    COORD_SYS_GROUND_YAW_ROTATED = 1
    COORD_SYS_GROUND = 2
    COORD_SYS_FRAME = 3
    COMPUTED_IN_EULER_ORDER = 1 << 6
    FRAME_HEADING = 1 << 7


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


class DataStreamCommand(IntEnum):
    REALTIME_DATA_3 = 23
    REALTIME_DATA_4 = 25
    REALTIME_DATA_CUSTOM = 88
    REALTIME_DATA_CUSTOM2 = 139
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
    """CMD_CONFIRM or CMD_ERROR received for a previously sent command"""

    command_id: int
    status: ConfirmationStatus
    command_data: int
    error_code: int
    error_data: bytes


@dataclass(frozen=True, slots=True)
class AdjustableVariable:
    """One integer adjustable variable used by CMD_SET/GET_ADJ_VARS_VAL.

    id is the firmware-specific adjustable-variable ID and value is
    the raw signed 32-bit value used by the board. The command changes RAM only.
    """

    id: int
    value: int


@dataclass(frozen=True, slots=True)
class AdjustableVariableFloat:
    id: int
    value: float


@dataclass(frozen=True, slots=True)
class AdjustableVariableTriggerSlot:
    source: int
    actions: tuple[int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class AdjustableVariableAnalogSlot:
    source: int
    variable_id: int
    min_value: int
    max_value: int


@dataclass(frozen=True, slots=True)
class AdjustableVariablesConfig:
    trigger_slots: tuple[AdjustableVariableTriggerSlot, ...]
    analog_slots: tuple[AdjustableVariableAnalogSlot, ...]
    reserved: bytes = b"\x00" * 8


@dataclass(frozen=True, slots=True)
class AdjustableVariablesState:
    trigger_rc_data: int
    trigger_action: int
    analog_source_value: int
    analog_variable_value: float
    lut_source_value: int
    lut_variable_value: float


@dataclass(frozen=True, slots=True)
class AdjustableVariableInfo:
    id: int
    min_value: int
    max_value: int
    value: int


@dataclass(frozen=True, slots=True)
class ControlAxis:
    """One CMD_CONTROL axis using degrees and degrees per second.

    angle is converted to the 16-bit SerialAPI angle representation and
    speed to its standard speed representation by SimpleBGC.control.
    For RC and RC_HIGH_RES modes, angle remains the raw RC value
    required by the protocol rather than an angle in degrees.
    """

    mode: int = ControlMode.NO_CONTROL
    speed: float = 0.0
    angle: float = 0.0


class RealtimeDataCustomFlag(IntFlag):
    """Fields requested through CMD_REALTIME_DATA_CUSTOM."""

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
    FRAME_CAM_ANGLE_20 = 1 << 28
    MAIN_IMU_STATE = 1 << 29
    INCLUDE_FLAGS = 1 << 31
    FRAME_CAM_ANGLE = STATOR_ROTOR_ANGLE


class RealtimeDataCustom2Flag(IntFlag):
    """CMD_REALTIME_DATA_CUSTOM2 fields; firmware 2.74.2+, bit 6: 2.74.4+."""

    FRAME_IMU_ANGLES = 1 << 0
    FRAME_GYRO = 1 << 1
    FRAME_ACC = 1 << 2
    DEBUG = 1 << 3
    MAG_SENS_DATA = 1 << 4
    PIN_STATE = 1 << 5
    STAB_ERR_AMPL = 1 << 6
    INCLUDE_FLAGS = 1 << 31


@dataclass(frozen=True, slots=True)
class RealtimeImuState:
    g_ref_error: int
    h_ref_error: int
    flags: int
    ext_sensor_error: int
    reserved: bytes


@dataclass(frozen=True, slots=True)
class RealtimePinState:
    """Packed two-bit input states; unassigned/occupied inputs have value 2."""

    extra_buttons_state: int
    pin_state: int
    reserved: bytes


@dataclass(frozen=True, slots=True)
class RealtimeDataCustom2:
    flags: RealtimeDataCustom2Flag
    timestamp_ms: int
    fields: Mapping[RealtimeDataCustom2Flag, object]
    raw_payload: bytes


class PasswordProtectionFlag(IntFlag):
    ENCRYPT_PARAMS = 1 << 1
    SILENT = 1 << 2
    CHANNEL_1_ENABLED = 1 << 4
    CHANNEL_2_ENABLED = 1 << 5
    CHANNEL_3_ENABLED = 1 << 6
    CHANNEL_4_ENABLED = 1 << 7
    CHANNEL_5_ENABLED = 1 << 8
    CHANNEL_6_ENABLED = 1 << 9
    CHANNEL_1_ALLOW_CONTROL = 1 << 10
    CHANNEL_2_ALLOW_CONTROL = 1 << 11
    CHANNEL_3_ALLOW_CONTROL = 1 << 12
    CHANNEL_4_ALLOW_CONTROL = 1 << 13
    CHANNEL_5_ALLOW_CONTROL = 1 << 14
    CHANNEL_6_ALLOW_CONTROL = 1 << 15


@dataclass(frozen=True, slots=True)
class PasswordProtectionSettings:
    flags: PasswordProtectionFlag
    reserved: bytes = bytes(4)


@dataclass(frozen=True, slots=True)
class Axis3:
    """Three physical values ordered as roll, pitch, and yaw."""

    roll: float
    pitch: float
    yaw: float


@dataclass(frozen=True, slots=True)
class Angles:
    """``CMD_GET_ANGLES`` result in physical units.

    ``imu`` and ``target`` are degrees. ``target_speed`` is degrees per
    second. The SerialAPI integer scaling is converted by ``get_angles``.
    """

    imu: Axis3
    target: Axis3
    target_speed: Axis3


@dataclass(frozen=True, slots=True)
class AxisGAE:
    """CMD_GET_ANGLES_EXT result."""

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
    """CMD_SCRIPT_DEBUG result."""

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
    """One raw sbgcAxisRTD_t record."""

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
    """Extended board information returned by CMD_BOARD_INFO_3."""

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
    script_slot_sizes_ext: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class EepromFile:
    file_id: int
    page_offset: int
    data: bytes
    error_code: int


@dataclass(frozen=True, slots=True)
class ProfileParameters:
    params_3: bytes
    params_ext: bytes
    params_ext2: bytes
    params_ext3: bytes


@dataclass(frozen=True, slots=True)
class ExternalImuDebugInfo:
    main_imu_ref_src: int
    frame_imu_ref_src: int
    main_imu_z_ref_error: int
    main_imu_h_ref_error: int
    frame_imu_z_ref_error: int
    frame_imu_h_ref_error: int
    external_imu_status: int
    packets_received: int
    parse_error_count: int
    external_heading_correction: int
    external_attitude_correction: int
    dcm: tuple[float, ...]
    acceleration_body: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class CalibInfo:
    progress: int
    imu_type: ImuType
    acceleration: tuple[int, int, int]
    gyro_amplitude: int
    current_axis: int
    limits_info: int
    temperature_celsius: int
    temperature_gyro_enabled: bool
    temperature_gyro_min_celsius: int
    temperature_gyro_max_celsius: int
    temperature_acc_enabled: bool
    temperature_acc_slots: tuple[int, int, int, int, int, int]
    temperature_acc_min_celsius: int
    temperature_acc_max_celsius: int
    heading_error_length: int


class CalibCoggingAction(IntEnum):
    CALIBRATE = 1
    DELETE_CALIBRATION_DATA = 2


class CalibCoggingAxis(IntFlag):
    ROLL = 1
    PITCH = 2
    YAW = 4


@dataclass(frozen=True, slots=True)
class CalibCoggingAxisConfig:
    angle: int
    smooth: int
    speed: int
    period: int = 0


@dataclass(frozen=True, slots=True)
class CalibCogging:
    action: CalibCoggingAction
    axes: CalibCoggingAxis
    axis_config: tuple[CalibCoggingAxisConfig, CalibCoggingAxisConfig, CalibCoggingAxisConfig]
    iterations: int


@dataclass(frozen=True, slots=True)
class GyroCorrection:
    imu_type: ImuType
    zero_correction: tuple[int, int, int]
    zero_heading_correction: int = 0


@dataclass(frozen=True, slots=True)
class AhrsHelper:
    z_vector: tuple[float, float, float]
    h_vector: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class HelperData:
    frame_acceleration: tuple[int, int, int]
    frame_angle_roll: int = 0
    frame_angle_pitch: int = 0


@dataclass(frozen=True, slots=True)
class HelperDataExt:
    frame_acceleration: tuple[int, int, int]
    frame_angle_roll: int = 0
    frame_angle_pitch: int = 0
    flags: HelperDataFlag = HelperDataFlag.COORD_SYS_GROUND_YAW_ROTATED
    frame_speed: tuple[int, int, int] = (0, 0, 0)
    frame_heading: int = 0


@dataclass(frozen=True, slots=True)
class CanModuleInfo:
    can_id: int
    board_ver: int
    bootloader_ver: int
    firmware_ver: int


@dataclass(frozen=True, slots=True)
class CanDeviceScan:
    uid: bytes
    can_id: int
    can_type: int


@dataclass(frozen=True, slots=True)
class MenuExecutionResult:
    started: CommandConfirmation | None = None
    finished: CommandConfirmation | None = None


class MenuCommandFlag(IntFlag):
    NO = 0
    CONFIRM = 1 << 0
    CONFIRM_ON_FINISH = 1 << 1


class TriggerPin(IntEnum):
    RC_ROLL = 1
    RC_PITCH = 2
    EXT_FC_ROLL = 3
    EXT_FC_PITCH = 4
    RC_INPUT_YAW = 5
    AUX_1 = 16
    AUX_2 = 17
    AUX_3 = 18
    BUZZER = 32
    SSAT_POWER = 33
    CAN_DRV1_AUX1 = 64
    CAN_DRV1_AUX2 = 65
    CAN_DRV1_AUX3 = 66
    CAN_DRV2_AUX1 = 67
    CAN_DRV2_AUX2 = 68
    CAN_DRV2_AUX3 = 69
    CAN_DRV3_AUX1 = 70
    CAN_DRV3_AUX2 = 71
    CAN_DRV3_AUX3 = 72
    CAN_DRV4_AUX1 = 73
    CAN_DRV4_AUX2 = 74
    CAN_DRV4_AUX3 = 75
    CAN_DRV5_AUX1 = 76
    CAN_DRV5_AUX2 = 77
    CAN_DRV5_AUX3 = 78
    CAN_DRV6_AUX1 = 79
    CAN_DRV6_AUX2 = 80
    CAN_DRV6_AUX3 = 81
    CAN_DRV7_AUX1 = 82
    CAN_DRV7_AUX2 = 83
    CAN_DRV7_AUX3 = 84
    CAN_IMU_AUX1 = 85
    CAN_IMU_AUX2 = 86
    CAN_IMU_FRAME_AUX1 = 88
    CAN_IMU_FRAME_AUX2 = 89


class TriggerPinState(IntEnum):
    LOW = 0
    HIGH = 1
    FLOATING = 2
    PULLED_UP = 3
    PULLED_DOWN = 4


class ServoOutput(IntFlag):
    FC_ROLL = 1 << 0
    FC_PITCH = 1 << 1
    RC_PITCH = 1 << 2
    AUX_1 = 1 << 3
    CAN_DRIVER_1_PIN_1 = 1 << 4
    CAN_DRIVER_1_PIN_2 = 1 << 5
    CAN_DRIVER_2_PIN_1 = 1 << 6
    CAN_DRIVER_2_PIN_2 = 1 << 7
    CAN_DRIVER_3_PIN_1 = 1 << 8
    CAN_DRIVER_3_PIN_2 = 1 << 9
    CAN_DRIVER_4_PIN_1 = 1 << 10
    CAN_DRIVER_4_PIN_2 = 1 << 11
    CAN_DRIVER_5_PIN_1 = 1 << 12
    CAN_DRIVER_5_PIN_2 = 1 << 13
    CAN_DRIVER_6_PIN_1 = 1 << 14
    CAN_DRIVER_6_PIN_2 = 1 << 15
    CAN_DRIVER_7_PIN_1 = 1 << 16
    CAN_DRIVER_7_PIN_2 = 1 << 17


class BodeTestAxis(IntEnum):
    ROLL = 0
    PITCH = 1
    YAW = 2


class BodeStimulusType(IntEnum):
    WHITE_NOISE = 1
    SINE_SWEEP = 2
    EXPONENTIAL_SINE_SWEEP = 3


class BodeTestSystem(IntEnum):
    PLANT_OPEN_LOOP = 70
    PLANT_CLOSED_LOOP = 198
    PLANT_WITH_NOTCHES_OPEN_LOOP = 6
    PLANT_WITH_NOTCHES_CLOSED_LOOP = 134
    CONTROLLER = 3
    CONTROLLER_AND_PLANT_OPEN_LOOP = 7
    CONTROLLER_AND_PLANT_CLOSED_LOOP = 135
    OVERALL_SYSTEM_RESPONSE = 11


@dataclass(frozen=True, slots=True)
class BodeTestConfig:
    axis: BodeTestAxis | int
    stimulus_gain: int
    end_frequency_hz: int
    system: BodeTestSystem | int
    test_duration_seconds: float
    stimulus_type: BodeStimulusType | int = BodeStimulusType.WHITE_NOISE
    start_frequency_hz: int = 3
    mode: int = 0


@dataclass(frozen=True, slots=True)
class BodeTestSample:
    input_value: float
    output_value: float


@dataclass(frozen=True, slots=True)
class BodeTestData:
    sample_counter: int
    input_min: float
    output_min: float
    input_max: float
    output_max: float
    samples: tuple[BodeTestSample, ...]


@dataclass(frozen=True, slots=True)
class BodeTestFinished:
    samples_count: int
    error_code: int
    mode: int


@dataclass(frozen=True, slots=True)
class BodeTestResult:
    """All samples and completion status returned by one Bode-test run."""

    config: BodeTestConfig
    confirmation: CommandConfirmation | None
    samples: tuple[BodeTestSample, ...]
    completion: BodeTestFinished
    data_packet_counters: tuple[int, ...] = ()
    data_packet_sample_counts: tuple[int, ...] = ()

    @property
    def received_samples_count(self) -> int:
        return len(self.samples)

    @property
    def samples_match(self) -> bool:
        return self.received_samples_count in (
            self.completion.samples_count,
            self.completion.samples_count + 1,
        )

    @property
    def completion_reports_last_sample_index(self) -> bool:
        """Whether the completion count is the zero-based last sample index.

        Some firmware versions report ``SAMPLES_COUNT`` in the final CMD #37
        packet as the last sample index.  Therefore 5,000 collected samples
        are reported as 4,999.  Both representations describe a complete run.
        """
        return self.received_samples_count == self.completion.samples_count + 1

    @property
    def sample_counter_discontinuities(self) -> int:
        """Count unexpected jumps in consecutive CMD_BODE_TEST_DATA counters."""
        return sum(
            current != (previous + previous_size) & 0xFF
            for previous, previous_size, current in zip(
                self.data_packet_counters,
                self.data_packet_sample_counts,
                self.data_packet_counters[1:],
            )
        )

    @property
    def successful(self) -> bool:
        return self.completion.error_code == 0 and self.samples_match


# Re-export only value types defined by this module; implementation imports
# such as ``dataclass`` and ``IntEnum`` stay private.
__all__ = tuple(
    name
    for name, value in globals().items()
    if isinstance(value, type) and value.__module__ == __name__
)
