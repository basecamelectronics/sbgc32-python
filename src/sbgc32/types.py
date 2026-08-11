from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import Mapping

# Stopping mode accepted by CMD_MOTORS_OFF
class MotorsOffMode(IntEnum):
    NORMAL = 0
    BREAK = 1
    SAFE_STOP = 2


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


@dataclass(frozen=True, slots=True)
class RealtimeDataCustom:
    """Result of a configurable CMD_REALTIME_DATA_CUSTOM request.

    ``fields`` is indexed by :class:`RealtimeDataCustomFlag`. Composite fields
    without a stable public Python structure are returned as raw ``bytes``.
    """

    flags: RealtimeDataCustomFlag
    timestamp_ms: int
    fields: Mapping[RealtimeDataCustomFlag, object]
    raw_payload: bytes

# Values for roll, pitch, and yaw
@dataclass(frozen=True, slots=True)
class Axis3:
    roll: float
    pitch: float
    yaw: float


# CMD_GET_ANGLES result, in degrees and degrees per second.
@dataclass(frozen=True, slots=True)
class Angles:
    imu: Axis3
    target: Axis3
    target_speed: Axis3


@dataclass(frozen=True, slots=True)
class AxisGAE:

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


# CMD_GET_ANGLES_EXT result, mirroring sbgcGetAnglesExt_t.
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


# CMD_SCRIPT_DEBUG result.
@dataclass(frozen=True, slots=True)
class ScriptDebugInfo:
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
    """One raw ``sbgcAxisRTD_t`` record."""

    acc_data: int
    gyro_data: int


# CMD_REALTIME_DATA and CMD_REALTIME_DATA_3 result (63 bytes).
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


# CMD_REALTIME_DATA_4 result (124 bytes).
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


# CMD_BOARD_INFO and also comfortable view of board_version and firmware_version
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


# CMD_BOARD_INFO_3
@dataclass(frozen=True, slots=True)
class BoardInfo3:
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
