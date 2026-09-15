"""Formatting helpers for SimpleBGC value objects.

Every ``format_*`` function accepts an already decoded value object and
returns a plain ``str``. They do not access a controller or write to standard
output. Invalid input types raise :class:`TypeError`; use
:func:`print_debug_var_info_3` only when immediate console output is wanted.
"""

from __future__ import annotations

from collections.abc import Sequence

from .types import (
    AdjustableVariable,
    AdjustableVariableFloat,
    AdjustableVariableInfo,
    AdjustableVariablesConfig,
    AdjustableVariablesState,
    AhrsHelper,
    Angles,
    AutoPidState,
    BoardInfo,
    BoardInfo3,
    CalibInfo,
    CanModuleInfo,
    ControlQuatStatus,
    DebugVarInfo,
    ExternalImuDebugInfo,
    PidValues,
    ProfileParameters,
    RealtimeData3,
    RealtimeData4,
    StateVars,
)

__all__ = [
    "Formatter",
    "format_angles",
    "format_auto_pid_state",
    "format_board_info",
    "format_board_info_3",
    "format_can_module_list",
    "format_control_quat_status",
    "format_calib_info",
    "format_debug_var_info_3",
    "format_ext_imu_debug",
    "format_profile_names",
    "format_profile_parameters",
    "format_profile_pid_values",
    "format_realtime_data",
    "format_state_vars",
    "format_table",
    "format_ahrs_helper",
    "format_adj_vars",
    "format_adj_vars_config",
    "format_adj_vars_info",
    "format_adj_vars_state",
    "print_debug_var_info_3",
]


def format_table(headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...]) -> str:
    """Render a left-aligned text table."""

    widths = tuple(
        max(len(row[column]) for row in (headers, *rows)) for column in range(len(headers))
    )

    def render(row: tuple[str, ...]) -> str:
        return "  ".join(value.ljust(widths[column]) for column, value in enumerate(row)).rstrip()

    separator = "  ".join("-" * width for width in widths)
    return "\n".join((render(headers), separator, *(render(row) for row in rows)))


def format_angles(angles: Angles) -> str:
    """Format the IMU, target and target-speed angles by axis."""

    if not isinstance(angles, Angles):
        raise TypeError("angles must be Angles")
    rows = (
        (
            "Roll",
            f"{angles.imu.roll:.3f}",
            f"{angles.target.roll:.3f}",
            f"{angles.target_speed.roll:.3f}",
        ),
        (
            "Pitch",
            f"{angles.imu.pitch:.3f}",
            f"{angles.target.pitch:.3f}",
            f"{angles.target_speed.pitch:.3f}",
        ),
        (
            "Yaw",
            f"{angles.imu.yaw:.3f}",
            f"{angles.target.yaw:.3f}",
            f"{angles.target_speed.yaw:.3f}",
        ),
    )
    return format_table(("Axis", "IMU, deg", "Target, deg", "Target speed, deg/s"), rows)


def format_realtime_data(data: RealtimeData3 | RealtimeData4) -> str:
    """Format fixed realtime data as axis and general-information tables."""

    if not isinstance(data, RealtimeData3):
        raise TypeError("data must be RealtimeData3 or RealtimeData4")
    axis_rows = tuple(
        (
            name,
            str(imu_angle),
            str(frame_angle),
            str(target_angle),
            str(power),
            str(rtd.acc_data),
            str(rtd.gyro_data),
        )
        for name, imu_angle, frame_angle, target_angle, power, rtd in zip(
            ("Roll", "Pitch", "Yaw"),
            data.imu_angle,
            data.frame_imu_angle,
            data.target_angle,
            data.motor_power,
            data.axis_rtd,
        )
    )
    general_rows = (
        ("Serial errors", str(data.serial_error_count)),
        ("I2C errors", str(data.i2c_error_count)),
        ("System error", f"0x{data.system_error:04X}"),
        ("System sub-error", f"0x{data.system_sub_error:02X}"),
        ("Error code", str(data.error_code)),
        ("Battery level", str(data.bat_level)),
        ("Cycle time", f"{data.cycle_time} us"),
        ("Current IMU", str(data.cur_imu)),
        ("Current profile", str(data.cur_profile)),
        ("RC", f"{data.rc_roll}, {data.rc_pitch}, {data.rc_yaw}, {data.rc_cmd}"),
    )
    if isinstance(data, RealtimeData4):
        general_rows += (
            ("Current", str(data.current)),
            ("IMU temperature", str(data.imu_temperature)),
            ("Frame IMU temperature", str(data.frame_imu_temperature)),
            ("System state flags", f"0x{data.system_state_flags:04X}"),
        )
    return "\n\n".join(
        (
            format_table(
                ("Axis", "IMU", "Frame IMU", "Target", "Motor", "ACC", "Gyro"),
                axis_rows,
            ),
            format_table(("Field", "Value"), general_rows),
        )
    )


def format_control_quat_status(status: ControlQuatStatus) -> str:
    """Format the optional fields in a quaternion-control status response."""

    if not isinstance(status, ControlQuatStatus):
        raise TypeError("status must be ControlQuatStatus")
    rows: list[tuple[str, str]] = [
        ("Requested fields", f"0x{int(status.requested_fields):04X}"),
    ]
    if status.mode is not None:
        rows.append(("Mode", str(int(status.mode))))
    if status.control_flags is not None:
        rows.append(("Flags", f"0x{status.control_flags:02X}"))
    for name, value in (
        ("Target attitude", status.target_attitude),
        ("Setpoint attitude", status.setpoint_attitude),
        ("Actual attitude", status.actual_attitude),
        ("Target speed", status.target_speed_raw),
        ("Setpoint speed", status.setpoint_speed_raw),
        ("Actual speed", status.actual_speed_raw),
    ):
        if value is not None:
            rows.append(
                (
                    name,
                    ", ".join(
                        f"{item:g}" if isinstance(item, float) else str(item) for item in value
                    ),
                )
            )
    return format_table(("Field", "Value"), tuple(rows))


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
    """Return a compact table suitable for displaying ``DEBUG_VARS_INFO_3``."""

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
        rows.append(
            (
                str(variable.index),
                variable.name,
                _DEBUG_VAR_TYPE_NAMES.get(raw_type & 0x07, f"unknown (0x{raw_type:02X})"),
                ", ".join(flags) or "-",
            )
        )

    return format_table(("IDX", "NAME", "TYPE", "FLAGS"), tuple(rows))


def print_debug_var_info_3(variables: Sequence[DebugVarInfo]) -> None:
    """Print :func:`format_debug_var_info_3` to standard output."""

    print(format_debug_var_info_3(variables))


def format_ext_imu_debug(info: ExternalImuDebugInfo) -> str:
    """Format the useful diagnostics returned by ``CMD_EXT_IMU_DEBUG_INFO``."""

    if not isinstance(info, ExternalImuDebugInfo):
        raise TypeError("info must be ExternalImuDebugInfo")
    return format_table(
        ("Field", "Value"),
        (
            ("Main reference", str(info.main_imu_ref_src)),
            ("Frame reference", str(info.frame_imu_ref_src)),
            ("External IMU status", str(info.external_imu_status)),
            ("Packets received", str(info.packets_received)),
            ("Parse errors", str(info.parse_error_count)),
            ("Heading correction", str(info.external_heading_correction)),
            ("Attitude correction", str(info.external_attitude_correction)),
            ("Acceleration body", " ".join(f"{value:g}" for value in info.acceleration_body)),
        ),
    )


def format_ahrs_helper(helper: AhrsHelper) -> str:
    """Format Z and H vectors returned by ``CMD_AHRS_HELPER``."""

    if not isinstance(helper, AhrsHelper):
        raise TypeError("helper must be AhrsHelper")
    return format_table(
        ("Field", "Value"),
        (
            ("Z vector", " ".join(f"{value:g}" for value in helper.z_vector)),
            ("H vector", " ".join(f"{value:g}" for value in helper.h_vector)),
        ),
    )


def format_adj_vars(variables: Sequence[AdjustableVariable | AdjustableVariableFloat]) -> str:
    """Format integer or float adjustable-variable values."""
    values = tuple(variables)
    if any(
        not isinstance(value, (AdjustableVariable, AdjustableVariableFloat)) for value in values
    ):
        raise TypeError("variables must contain AdjustableVariable or AdjustableVariableFloat")
    rows = tuple(
        (
            str(value.id),
            f"{value.value:g}" if isinstance(value, AdjustableVariableFloat) else str(value.value),
        )
        for value in values
    )
    return format_table(("ID", "Value"), rows) if rows else "No adjustable variables"


def format_adj_vars_info(variables: Sequence[AdjustableVariableInfo]) -> str:
    values = tuple(variables)
    if any(not isinstance(value, AdjustableVariableInfo) for value in values):
        raise TypeError("variables must contain AdjustableVariableInfo")
    rows = tuple(
        (str(value.id), str(value.min_value), str(value.max_value), str(value.value))
        for value in values
    )
    return format_table(("ID", "Min", "Max", "Value"), rows) if rows else "No adjustable variables"


def format_adj_vars_config(config: AdjustableVariablesConfig) -> str:
    if not isinstance(config, AdjustableVariablesConfig):
        raise TypeError("config must be AdjustableVariablesConfig")
    triggers = tuple(
        (str(index), str(slot.source), " ".join(map(str, slot.actions)))
        for index, slot in enumerate(config.trigger_slots)
    )
    analog = tuple(
        (
            str(index),
            str(slot.source),
            str(slot.variable_id),
            str(slot.min_value),
            str(slot.max_value),
        )
        for index, slot in enumerate(config.analog_slots)
    )
    return "\n\n".join(
        (
            format_table(("Trigger", "Source", "Actions"), triggers),
            format_table(("Analog", "Source", "Variable", "Min", "Max"), analog),
        )
    )


def format_adj_vars_state(state: AdjustableVariablesState) -> str:
    if not isinstance(state, AdjustableVariablesState):
        raise TypeError("state must be AdjustableVariablesState")
    return format_table(
        ("Field", "Value"),
        (
            ("Trigger RC", str(state.trigger_rc_data)),
            ("Trigger action", str(state.trigger_action)),
            ("Analog source", str(state.analog_source_value)),
            ("Analog variable", f"{state.analog_variable_value:g}"),
            ("LUT source", str(state.lut_source_value)),
            ("LUT variable", f"{state.lut_variable_value:g}"),
        ),
    )


def format_calib_info(info: CalibInfo) -> str:
    """Format the current calibration state returned by ``CMD_CALIB_INFO``."""
    if not isinstance(info, CalibInfo):
        raise TypeError("info must be CalibInfo")
    return format_table(
        ("Field", "Value"),
        (
            ("Progress", f"{info.progress}%"),
            ("IMU", info.imu_type.name),
            ("Acceleration", " ".join(map(str, info.acceleration))),
            ("Gyro amplitude", str(info.gyro_amplitude)),
            ("Temperature", f"{info.temperature_celsius} C"),
            ("Heading error", str(info.heading_error_length)),
        ),
    )


def format_profile_names(names: tuple[str, str, str, str, str]) -> str:
    """Format the five profile names returned by ``CMD_READ_PROFILE_NAMES``."""

    if (
        not isinstance(names, tuple)
        or len(names) != 5
        or any(not isinstance(name, str) for name in names)
    ):
        raise TypeError("names must be a tuple of five strings")
    return format_table(
        ("Profile", "Name"),
        tuple((str(index), name or f"Profile {index}") for index, name in enumerate(names, 1)),
    )


def format_profile_parameters(parameters: ProfileParameters) -> str:
    """Format the raw parameter-block sizes and target profile IDs."""

    if not isinstance(parameters, ProfileParameters):
        raise TypeError("parameters must be ProfileParameters")
    return format_table(
        ("Block", "Profile", "Bytes"),
        (
            ("Params 3", str(parameters.params_3[0]), str(len(parameters.params_3))),
            ("Params Ext", str(parameters.params_ext[0]), str(len(parameters.params_ext))),
            ("Params Ext2", str(parameters.params_ext2[0]), str(len(parameters.params_ext2))),
            ("Params Ext3", str(parameters.params_ext3[0]), str(len(parameters.params_ext3))),
        ),
    )


def format_auto_pid_state(state: AutoPidState) -> str:
    if not isinstance(state, AutoPidState):
        raise TypeError("state must be AutoPidState")
    return format_table(
        ("Axis", "P", "I", "D", "LPF, Hz", "Tracking error"),
        tuple(
            (name, str(p), str(i), str(d), str(lpf), f"{axis.tracking_error:.4f}")
            for name, p, i, d, lpf, axis in zip(
                ("Roll", "Pitch", "Yaw"), state.p, state.i, state.d, state.lpf_frequency, state.axes
            )
        ),
    )


def format_profile_pid_values(values: PidValues) -> str:
    if not isinstance(values, PidValues):
        raise TypeError("values must be PidValues")
    return format_table(
        ("Axis", "P", "I", "D"),
        tuple(
            (name, str(p), str(i), str(d))
            for name, p, i, d in zip(("Roll", "Pitch", "Yaw"), values.p, values.i, values.d)
        ),
    )


def format_board_info(info: BoardInfo) -> str:
    if not isinstance(info, BoardInfo):
        raise TypeError("info must be BoardInfo")
    return format_table(
        ("Field", "Value"),
        (
            ("Board", info.board_version),
            ("Firmware", info.firmware_version),
            ("Build", str(info.build_number)),
            ("Features", f"0x{info.board_features:04X}"),
        ),
    )


def format_board_info_3(info: BoardInfo3) -> str:
    if not isinstance(info, BoardInfo3):
        raise TypeError("info must be BoardInfo3")
    return format_table(
        ("Field", "Value"),
        (
            ("Device ID", info.device_id.hex(" ").upper()),
            ("EEPROM", f"{info.eeprom_size} bytes"),
            ("Flash", f"{info.flash_size_pages} pages"),
            ("Profile set", str(info.profile_set_current)),
        ),
    )


def format_state_vars(state: StateVars) -> str:
    if not isinstance(state, StateVars):
        raise TypeError("state must be StateVars")
    return format_table(
        ("Field", "Value"),
        (
            ("Work time", f"{state.work_time} s"),
            ("Startup count", str(state.startup_count)),
            ("Energy", f"{state.energy:g}"),
            ("Average current", f"{state.avg_current:g}"),
        ),
    )


def format_can_module_list(modules: tuple[CanModuleInfo, ...]) -> str:
    if not isinstance(modules, tuple) or any(
        not isinstance(module, CanModuleInfo) for module in modules
    ):
        raise TypeError("modules must be a tuple of CanModuleInfo")
    rows = tuple(
        (
            str(module.can_id),
            str(module.board_ver),
            str(module.bootloader_ver),
            str(module.firmware_ver),
        )
        for module in modules
    )
    return (
        format_table(("CAN ID", "Board", "Bootloader", "Firmware"), rows)
        if rows
        else "No CAN modules"
    )


class Formatter:
    """A namespaced, stateless interface to the package text formatters.

    The short method names are convenient for display code::

        print(Formatter.angles(angles))

    The longer ``format_*`` names are also available. The module-level
    functions remain available and are the implementations behind this
    facade.
    """

    table = staticmethod(format_table)
    angles = staticmethod(format_angles)
    realtime_data = staticmethod(format_realtime_data)
    control_quat_status = staticmethod(format_control_quat_status)
    debug_var_info_3 = staticmethod(format_debug_var_info_3)
    ext_imu_debug = staticmethod(format_ext_imu_debug)
    ahrs_helper = staticmethod(format_ahrs_helper)
    adj_vars = staticmethod(format_adj_vars)
    adj_vars_info = staticmethod(format_adj_vars_info)
    adj_vars_config = staticmethod(format_adj_vars_config)
    adj_vars_state = staticmethod(format_adj_vars_state)
    calib_info = staticmethod(format_calib_info)
    profile_names = staticmethod(format_profile_names)
    profile_parameters = staticmethod(format_profile_parameters)
    auto_pid_state = staticmethod(format_auto_pid_state)
    profile_pid_values = staticmethod(format_profile_pid_values)
    board_info = staticmethod(format_board_info)
    board_info_3 = staticmethod(format_board_info_3)
    state_vars = staticmethod(format_state_vars)
    can_module_list = staticmethod(format_can_module_list)

    # Full names mirror the existing module-level function names.
    format_table = table
    format_angles = angles
    format_realtime_data = realtime_data
    format_control_quat_status = control_quat_status
    format_debug_var_info_3 = debug_var_info_3
    format_ext_imu_debug = ext_imu_debug
    format_ahrs_helper = ahrs_helper
    format_adj_vars = adj_vars
    format_adj_vars_info = adj_vars_info
    format_adj_vars_config = adj_vars_config
    format_adj_vars_state = adj_vars_state
    format_calib_info = calib_info
    format_profile_names = profile_names
    format_profile_parameters = profile_parameters
    format_auto_pid_state = auto_pid_state
    format_profile_pid_values = profile_pid_values
    format_board_info = board_info
    format_board_info_3 = board_info_3
    format_state_vars = state_vars
    format_can_module_list = can_module_list
