from __future__ import annotations

import ctypes
from collections.abc import Mapping
from math import exp, isclose, isfinite, log
from time import sleep

from ._control import make_confirmation, validate_uint
from ._serial_api_library import NativeAutoPid, NativeAutoPid2, NativeAutoPid2Axis, NativeStateVars, NativeSyncMotors
from .commands import MenuCommands
from .types import (
    AutoPid2Axis,
    AutoPid2Config,
    AutoPidAxisState,
    AutoPidConfig,
    AutoPidState,
    BeeperMode,
    BoardInfo,
    BoardInfo3,
    CanModuleInfo,
    CanDeviceScan,
    CommandConfirmation,
    DebugPortPacket,
    MotorsOffMode,
    MenuCommandFlag,
    MenuExecutionResult,
    PidValues,
    ServoOutput,
    ScriptDebugInfo,
    StateVars,
    SyncMotorsConfig,
    TriggerPin,
    TriggerPinState,
)


_AUTO_PID2_MIN_FIRMWARE = 2730
_PID_GUI_SCALE = log(50) / 127
_AXIS_NAMES = ("Roll", "Pitch", "Yaw")


def _require_legacy_auto_pid_firmware(self) -> None:
    firmware_ver = get_board_info(self).firmware_ver

    if firmware_ver >= _AUTO_PID2_MIN_FIRMWARE:
        raise NotImplementedError(
            "CMD_AUTO_PID is supported only before firmware 2.73; "
            "use tune_auto_pid2() on this controller."
        )


def _auto_pid_config(config: AutoPidConfig) -> NativeAutoPid:
    if not isinstance(config, AutoPidConfig):
        raise TypeError("config must be an AutoPidConfig")

    return NativeAutoPid(
        profile_id=validate_uint(config.profile_id, "profile_id", 0xFF),
        config_flags=validate_uint(int(config.config_flags), "config_flags", 0xFF),
        gain_vs_stability=validate_uint(config.gain_vs_stability, "gain_vs_stability", 0xFF),
        momentum=validate_uint(config.momentum, "momentum", 0xFF),
        action=validate_uint(config.action, "action", 0xFF),
    )


def _auto_pid2_frequency_from(value: float) -> int:
    if type(value) not in (int, float) or not isfinite(value):
        raise TypeError("test_frequency_from must be a finite number of Hz")

    encoded = round(value * 10)

    if not isclose(value, encoded / 10, abs_tol=1e-9):
        raise ValueError("test_frequency_from must use 0.1 Hz increments")

    return validate_uint(encoded, "test_frequency_from", 0xFF)


def _auto_pid2_frequency_to(value: float) -> int:
    if type(value) not in (int, float) or not isfinite(value):
        raise TypeError("test_frequency_to must be a finite number of Hz")

    encoded = round(value / 2)

    if not isclose(value, encoded * 2, abs_tol=1e-9):
        raise ValueError("test_frequency_to must use 2 Hz increments")

    return validate_uint(encoded, "test_frequency_to", 0xFF)


def _auto_pid2_config(config: AutoPid2Config) -> NativeAutoPid2:
    if not isinstance(config, AutoPid2Config):
        raise TypeError("config must be an AutoPid2Config")

    if len(config.axes) != 3 or any(not isinstance(axis, AutoPid2Axis) for axis in config.axes):
        raise TypeError("axes must contain exactly three AutoPid2Axis records")

    if len(config.multi_position_angles) != 4:
        raise ValueError("multi_position_angles must contain exactly four values")

    if any(type(value) is not int or not -128 <= value <= 127 for value in config.multi_position_angles):
        raise ValueError("each multi_position_angles value must be an integer in range -128..127")

    native_axes = (NativeAutoPid2Axis * 3)(
        *(NativeAutoPid2Axis(
            axis_flags=validate_uint(int(axis.axis_flags), "axis_flags", 0xFF),
            gain=validate_uint(axis.gain, "gain", 0xFF),
            stimulus_gain=validate_uint(axis.stimulus_gain, "stimulus_gain", 0xFFFF),
            effective_frequency=validate_uint(axis.effective_frequency, "effective_frequency", 0xFF),
            problem_frequency=validate_uint(axis.problem_frequency, "problem_frequency", 0xFF),
            problem_margin=validate_uint(axis.problem_margin, "problem_margin", 0xFF),

        ) for axis in config.axes
    ))

    return NativeAutoPid2(
        action=validate_uint(int(config.action), "action", 0xFF),
        command_flags=validate_uint(config.command_flags, "command_flags", 0xFFFF),
        config_version=validate_uint(config.config_version, "config_version", 0xFF),
        axis=native_axes,
        general_flags=validate_uint(config.general_flags, "general_flags", 0xFFFF),
        test_frequency_from=_auto_pid2_frequency_from(config.test_frequency_from),
        test_frequency_to=_auto_pid2_frequency_to(config.test_frequency_to),
        multi_position_flags=validate_uint(config.multi_position_flags, "multi_position_flags", 0xFF),
        multi_position_angle=(ctypes.c_int8 * 4)(*config.multi_position_angles),
    )


def tune_auto_pid(self, config: AutoPidConfig, *, need_confirmation: bool = False,) -> CommandConfirmation | None:
    self._ensure_open()

    _require_legacy_auto_pid_firmware(self)

    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")

    return make_confirmation(self._native.tune_auto_pid(
        self._device, _auto_pid_config(config), need_confirmation=need_confirmation,
    ))


def break_auto_pid(self, *, need_confirmation: bool = False) -> CommandConfirmation | None:
    self._ensure_open()

    _require_legacy_auto_pid_firmware(self)

    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")

    return make_confirmation(self._native.break_auto_pid(self._device, need_confirmation=need_confirmation,))


def tune_auto_pid2(self, config: AutoPid2Config, *, need_confirmation: bool = False,) -> CommandConfirmation | None:
    self._ensure_open()

    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")

    return make_confirmation(
        self._native.tune_auto_pid2(
            self._device, _auto_pid2_config(config),
            need_confirmation=need_confirmation,
        ))


def read_auto_pid_state(self) -> AutoPidState:
    self._ensure_open()

    _require_legacy_auto_pid_firmware(self)
    result = self._native.read_auto_pid_state(self._device)

    return AutoPidState(
        p=tuple(result.p),
        i=tuple(result.i),
        d=tuple(result.d),
        lpf_frequency=tuple(result.lpf_frequency),
        iteration_count=result.iteration_count,
        axes=tuple(AutoPidAxisState(axis.tracking_error) for axis in result.axis),
    )


def _legacy_pid_gui_value(value: int) -> float:
    return 0.1 + value * 0.02


def format_auto_pid_state(state: AutoPidState) -> str:
    if not isinstance(state, AutoPidState):
        raise TypeError("state must be an AutoPidState")

    headers = ("Axis", "P", "I", "D", "LPF, Hz", "Tracking error")
    rows = [headers]

    for axis_name, p, i, d, lpf, axis_state in zip(
        _AXIS_NAMES, state.p, state.i, state.d, state.lpf_frequency, state.axes,
    ):
        rows.append((
            axis_name,
            f"{_legacy_pid_gui_value(p):.2f} ({p})",
            f"{_legacy_pid_gui_value(i):.2f} ({i})",
            f"{_legacy_pid_gui_value(d):.2f} ({d})",
            str(lpf),
            f"{axis_state.tracking_error:.4f}",
        ))

    widths = tuple(max(len(row[column]) for row in rows) for column in range(len(headers)))
    render = lambda row: "  ".join(value.ljust(width) for value, width in zip(row, widths)).rstrip()
    separator = "  ".join("-" * width for width in widths)

    return "\n".join((render(headers), separator, *(render(row) for row in rows[1:])))


def read_profile_pid_values(self, profile_id: int = 0xFF) -> PidValues:
    self._ensure_open()

    result = self._native.read_profile_pid_values(
        self._device, validate_uint(profile_id, "profile_id", 0xFF),
    )

    return PidValues(
        profile_id=result.profile_id, p=tuple(result.p), i=tuple(result.i), d=tuple(result.d),
    )


def _pid2_gui_value(value: int) -> float:
    return exp((value - 1) * _PID_GUI_SCALE) / 50


def format_profile_pid_values(values: PidValues) -> str:
    if not isinstance(values, PidValues):
        raise TypeError("values must be PidValues")

    headers = ("Axis", "P", "I", "D")
    rows = [headers]

    for axis_name, p, i, d in zip(_AXIS_NAMES, values.p, values.i, values.d):
        rows.append((
            axis_name,
            f"{_pid2_gui_value(p):.3f} ({p})",
            f"{_pid2_gui_value(i):.3f} ({i})",
            f"{_pid2_gui_value(d):.3f} ({d})",
        ))

    widths = tuple(max(len(row[column]) for row in rows) for column in range(len(headers)))
    render = lambda row: "  ".join(value.ljust(width) for value, width in zip(row, widths)).rstrip()
    separator = "  ".join("-" * width for width in widths)

    return "\n".join((render(headers), separator, *(render(row) for row in rows[1:])))


def format_table(headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...]) -> str:
    widths = tuple(max(len(row[column]) for row in (headers, *rows)) for column in range(len(headers)))
    render = lambda row: "  ".join(value.ljust(width) for value, width in zip(row, widths)).rstrip()
    separator = "  ".join("-" * width for width in widths)
    return "\n".join((render(headers), separator, *(render(row) for row in rows)))


def format_board_info(info: BoardInfo) -> str:
    if not isinstance(info, BoardInfo):
        raise TypeError("info must be BoardInfo")
    return format_table(("Field", "Value"), (
        ("Board version", info.board_version),
        ("Firmware version", info.firmware_version),
        ("Firmware raw", str(info.firmware_ver)),
        ("Base firmware", str(info.base_firmware_ver)),
        ("Build number", str(info.build_number)),
        ("State flags", f"0x{info.state_flags:04X}"),
        ("Board features", f"0x{info.board_features:08X}"),
        ("Board features ext", f"0x{info.board_features_ext:08X}"),
        ("Connection flags", f"0x{info.connection_flag:02X}"),
        ("Firmware extra ID", str(info.firmware_extra_id)),
        ("Main IMU sensor", str(info.main_imu_sensor_model)),
        ("Frame IMU sensor", str(info.frame_imu_sensor_model)),
    ))


def format_board_info_3(info: BoardInfo3) -> str:
    if not isinstance(info, BoardInfo3):
        raise TypeError("info must be BoardInfo3")
    rows = (
        ("Device ID", info.device_id.hex(" ").upper()),
        ("MCU ID", info.mcu_id.hex(" ").upper()),
        ("EEPROM size", f"{info.eeprom_size} bytes"),
        ("Flash size", f"{info.flash_size_pages} pages"),
        ("Profile set slots", str(info.profile_set_slots)),
        ("Current profile set", str(info.profile_set_current)),
        ("IMU calibration", info.imu_calib_info.hex(" ").upper()),
        ("Hardware flags", f"0x{info.hardware_flags:04X}"),
        ("Board features ext2", f"0x{info.board_features_ext2:08X}"),
        ("CAN main limit", str(info.can_driver_main_limit)),
        ("CAN auxiliary limit", str(info.can_driver_aux_limit)),
        ("Adjustable variables", str(info.adjustable_variables_total)),
    )
    slots = tuple((f"Script slot {index}", f"{size} bytes") for index, size in enumerate(info.script_slot_sizes, 1))
    return format_table(("Field", "Value"), rows + slots)


def format_state_vars(state: StateVars) -> str:
    if not isinstance(state, StateVars):
        raise TypeError("state must be StateVars")
    return format_table(("Field", "Value"), (
        ("Sub-error", f"0x{state.sub_error:08X}"),
        ("Max acceleration", str(state.max_acc)),
        ("Work time", f"{state.work_time} s"),
        ("Startup count", str(state.startup_count)),
        ("Max current", str(state.max_current)),
        ("IMU temperature", f"{state.imu_temp_min} .. {state.imu_temp_max}"),
        ("MCU temperature", f"{state.mcu_temp_min} .. {state.mcu_temp_max}"),
        ("Shock counters", state.shock_count.hex(" ").upper()),
        ("Energy time", f"{state.energy_time} s"),
        ("Energy", f"{state.energy:g}"),
        ("Average current time", f"{state.avg_current_time} s"),
        ("Average current", f"{state.avg_current:g}"),
    ))


def format_can_module_list(modules: tuple[CanModuleInfo, ...]) -> str:
    if not isinstance(modules, tuple) or any(not isinstance(module, CanModuleInfo) for module in modules):
        raise TypeError("modules must be a tuple of CanModuleInfo")
    rows = tuple(
        (str(module.can_id), str(module.board_ver), str(module.bootloader_ver), str(module.firmware_ver))
        for module in modules
    )
    return format_table(("CAN ID", "Board", "Bootloader", "Firmware"), rows) if rows else "No CAN modules"


def synchronize_motors(
    self, config: SyncMotorsConfig, *, need_confirmation: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()

    if not isinstance(config, SyncMotorsConfig):
        raise TypeError("config must be a SyncMotorsConfig")

    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")

    native_config = NativeSyncMotors(
        axis=validate_uint(int(config.axis), "axis", 2),
        power=validate_uint(config.power, "power", 0xFF),
        time_ms=validate_uint(config.time_ms, "time_ms", 0xFFFF),
        angle=validate_uint(config.angle, "angle", 0xFFFF),
    )

    return make_confirmation(self._native.synchronize_motors(
        self._device, native_config, need_confirmation=need_confirmation,
    ))


def request_motor_state(self, motor_id: int, data_set: int, result_size: int) -> bytes:
    self._ensure_open()

    return self._native.request_motor_state(
        self._device,
        validate_uint(motor_id, "motor_id", 0xFF),
        validate_uint(data_set, "data_set", 0xFFFFFFFF),
        validate_uint(result_size, "result_size", 0xFF),
    )


def read_motor_state(self, result_size: int) -> bytes:
    self._ensure_open()

    return self._native.read_motor_state(
        self._device, validate_uint(result_size, "result_size", 0xFF),
    )


def enter_boot_mode(
    self, *, extended: bool = True, need_confirmation: bool = False, delay_ms: int = 0,
) -> None:
    self._ensure_open()

    if type(extended) is not bool or type(need_confirmation) is not bool:
        raise TypeError("extended and need_confirmation must be bool")

    if need_confirmation:
        raise ValueError(
            "BOOT_MODE_3 cannot safely return CMD_CONFIRM because the controller "
            "leaves Serial API for the bootloader. Use need_confirmation=False."
        )

    if not extended and delay_ms != 0:
        raise ValueError("delay_ms is supported only by extended boot mode")

    self._native.set_boot_mode(
        self._device, extended=extended, need_confirmation=need_confirmation,
        delay_ms=validate_uint(delay_ms, "delay_ms", 0xFFFF),
    )


def _state_vars_from_native(result: NativeStateVars) -> StateVars:
    return StateVars(
        step_signal_vars=bytes(result.step_signal_vars), sub_error=result.sub_error,
        max_acc=result.max_acc, work_time=result.work_time, startup_count=result.startup_count,
        max_current=result.max_current, imu_temp_min=result.imu_temp_min,
        imu_temp_max=result.imu_temp_max, mcu_temp_min=result.mcu_temp_min,
        mcu_temp_max=result.mcu_temp_max, shock_count=bytes(result.shock_count),
        energy_time=result.energy_time, energy=result.energy,
        avg_current_time=result.avg_current_time, avg_current=result.avg_current,
        reserved=bytes(result.reserved),
    )


def _state_vars_to_native(value: StateVars) -> NativeStateVars:
    if not isinstance(value, StateVars):
        raise TypeError("state must be a StateVars")

    for name, raw_value, size in (
        ("step_signal_vars", value.step_signal_vars, 6),
        ("shock_count", value.shock_count, 4),
        ("reserved", value.reserved, 152),
    ):
        if not isinstance(raw_value, bytes) or len(raw_value) != size:
            raise ValueError(f"{name} must be bytes with length {size}")

    return NativeStateVars(
        step_signal_vars=(ctypes.c_uint8 * 6).from_buffer_copy(value.step_signal_vars),
        sub_error=validate_uint(value.sub_error, "sub_error", 0xFF),
        max_acc=validate_uint(value.max_acc, "max_acc", 0xFF),
        work_time=validate_uint(value.work_time, "work_time", 0xFFFFFFFF),
        startup_count=validate_uint(value.startup_count, "startup_count", 0xFFFF),
        max_current=validate_uint(value.max_current, "max_current", 0xFFFF),
        imu_temp_min=validate_uint(value.imu_temp_min, "imu_temp_min", 0xFF),
        imu_temp_max=validate_uint(value.imu_temp_max, "imu_temp_max", 0xFF),
        mcu_temp_min=validate_uint(value.mcu_temp_min, "mcu_temp_min", 0xFF),
        mcu_temp_max=validate_uint(value.mcu_temp_max, "mcu_temp_max", 0xFF),
        shock_count=(ctypes.c_uint8 * 4).from_buffer_copy(value.shock_count),
        energy_time=validate_uint(value.energy_time, "energy_time", 0xFFFFFFFF),
        energy=_state_vars_float(value.energy, "energy"),
        avg_current_time=validate_uint(value.avg_current_time, "avg_current_time", 0xFFFFFFFF),
        avg_current=_state_vars_float(value.avg_current, "avg_current"),
        reserved=(ctypes.c_uint8 * 152).from_buffer_copy(value.reserved),
    )


def _state_vars_float(value: object, name: str) -> float:
    if type(value) not in (int, float) or not isfinite(value):
        raise ValueError(f"{name} must be a finite number")

    return float(value)


def read_state_vars(self) -> StateVars:
    self._ensure_open()

    return _state_vars_from_native(self._native.read_state_vars(self._device))


def write_state_vars(self, state: StateVars, *, need_confirmation: bool = False) -> CommandConfirmation | None:
    self._ensure_open()

    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")

    return make_confirmation(self._native.write_state_vars(
        self._device, _state_vars_to_native(state), need_confirmation=need_confirmation,
    ))


def set_debug_port(self, action: int, filter: int = 0, *, need_confirmation: bool = False,) -> CommandConfirmation | None:
    self._ensure_open()

    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")

    return make_confirmation(self._native.set_debug_port(
        self._device, validate_uint(action, "action", 1),
        validate_uint(filter, "filter", 0xFFFFFFFF), need_confirmation=need_confirmation,
    ))


def read_debug_port(self) -> DebugPortPacket:
    self._ensure_open()

    time_ms, port_and_direction, command_id, payload, payload_size = self._native.read_debug_port(self._device)
    return DebugPortPacket(time_ms, port_and_direction, command_id, payload, payload_size)


def motors_on(self) -> None:
    self._ensure_open()

    self._native.motors_on(self._device)


def motors_off(self, mode: MotorsOffMode = MotorsOffMode.SAFE_STOP) -> None:
    self._ensure_open()

    try:
        selected_mode = MotorsOffMode(mode)
    except ValueError as error:
        raise ValueError("mode must be a MotorsOffMode value (0, 1, or 2)") from error
    self._native.motors_off(self._device, int(selected_mode))


def beep(
    self,
    mode: BeeperMode = BeeperMode.CONFIRM,
    *,
    note_length: int = 0,
    decay_factor: int = 0,
    notes_hz: tuple[int, ...] = (),
) -> None:
    self._ensure_open()

    if not isinstance(mode, BeeperMode):
        try:
            mode = BeeperMode(mode)
        except ValueError as error:
            raise ValueError("mode must be a BeeperMode value") from error

    note_length = validate_uint(note_length, "note_length", 0xFF)
    decay_factor = validate_uint(decay_factor, "decay_factor", 0xFF)
    notes_hz = tuple(notes_hz)

    if len(notes_hz) > 50:
        raise ValueError("notes_hz must contain at most 50 notes")

    if mode == BeeperMode.CUSTOM_MELODY:
        if not notes_hz:
            raise ValueError("CUSTOM_MELODY requires notes_hz with 1...50 frequencies")
        if not 1 <= note_length <= 0xFF:
            raise ValueError("CUSTOM_MELODY note_length must be in range 1...255")
        if not 0 <= decay_factor <= 15:
            raise ValueError("CUSTOM_MELODY decay_factor must be in range 0...15")

    elif notes_hz:
        raise ValueError("notes_hz is allowed only with CUSTOM_MELODY")

    normalized_notes = tuple(validate_uint(note, "each notes_hz frequency", 0xFFFF) for note in notes_hz)

    if mode == BeeperMode.CUSTOM_MELODY and any(not 554 <= note <= 21000 for note in normalized_notes):
        raise ValueError("each custom melody frequency must be in range 554..21000 Hz")

    self._native.play_beeper(self._device, int(mode), note_length, decay_factor, normalized_notes)


play_beeper = beep


def execute_menu(self, menu_command: MenuCommands, *, need_confirmation: bool = False) -> CommandConfirmation | None:
    self._ensure_open()

    try:
        selected_command = MenuCommands(menu_command)
    except ValueError as error:
        raise ValueError("menu_command must be a supported MenuCommands value") from error

    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")

    return make_confirmation(self._native.execute_menu(self._device, int(selected_command), need_confirmation=need_confirmation))


def execute_menu_ext(
    self,
    menu_command: MenuCommands | int,
    *,
    confirm_on_start: bool = False,
    confirm_on_finish: bool = False,
) -> MenuExecutionResult:
    self._ensure_open()

    if isinstance(menu_command, bool) or not isinstance(menu_command, int):
        raise TypeError("menu_command must be an integer.")

    if not 0 <= int(menu_command) <= 81:
        raise ValueError("menu_command must be in range 0...81.")

    if type(confirm_on_start) is not bool:
        raise TypeError("confirm_on_start must be bool.")

    if type(confirm_on_finish) is not bool:
        raise TypeError("confirm_on_finish must be bool.")

    flags = MenuCommandFlag.NO

    if confirm_on_start:
        flags |= MenuCommandFlag.CONFIRM

    if confirm_on_finish:
        flags |= MenuCommandFlag.CONFIRM_ON_FINISH

    started, finished = self._native.execute_menu_ext(
        self._device,
        int(menu_command),
        int(flags),
    )

    return MenuExecutionResult(
        started=make_confirmation(started),
        finished=make_confirmation(finished),
    )


def set_trigger_pin(
    self,
    pin: TriggerPin | int,
    state: TriggerPinState | int,
    *,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()

    try:
        pin = TriggerPin(pin)
    except ValueError as error:
        raise ValueError("pin must be a supported TriggerPin value.") from error

    try:
        state = TriggerPinState(state)
    except ValueError as error:
        raise ValueError("state must be a supported TriggerPinState value.") from error

    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool.")

    return make_confirmation(self._native.set_trigger_pin(
        self._device,
        int(pin),
        int(state),
        need_confirmation=need_confirmation,
    ))


def _servo_out_value(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("servo output values must be integers.")

    if not -1 <= value <= 20000:
        raise ValueError("servo output values must be in range -1...20000.")

    return value


def set_servo_out(self, values: tuple[int, int, int, int]) -> None:
    self._ensure_open()

    if not isinstance(values, tuple) or len(values) != 4:
        raise ValueError("values must be a tuple of four servo output values.")

    normalized = tuple(_servo_out_value(value) for value in values)

    self._native.set_servo_out(self._device, normalized)


def set_servo_out_ext(self, outputs: Mapping[ServoOutput | int, int]) -> None:
    self._ensure_open()

    if not isinstance(outputs, Mapping) or not outputs:
        raise ValueError("outputs must be a non-empty mapping of servo outputs to values.")

    selected: dict[int, int] = {}

    for output, value in outputs.items():
        try:
            output = ServoOutput(output)
        except ValueError as error:
            raise ValueError("outputs contains an unsupported ServoOutput value.") from error

        bit = int(output)
        if bit == 0 or bit & (bit - 1):
            raise ValueError("each outputs key must select exactly one servo output.")

        selected[bit] = _servo_out_value(value)

    pins = sum(selected)
    values = tuple(selected[bit] for bit in sorted(selected))

    self._native.set_servo_out_ext(self._device, pins, values)


def _script_slot_max(self) -> int:
    board_info = get_board_info_3(self)

    return 10 if len(board_info.script_slot_sizes) == 10 else 5


def run_script(self, slot: int = 1, *, debug: bool = False) -> None:
    self._ensure_open()

    maximum = _script_slot_max(self)

    if not 1 <= slot <= maximum:
        raise ValueError(f"slot must be in range 1..{maximum}")

    self._native.run_script(self._device, 2 if debug else 1, slot - 1)
    self._debug_script_slot = slot if debug else None


def stop_script(self, slot: int = 1) -> None:
    self._ensure_open()

    maximum = _script_slot_max(self)

    if not 1 <= slot <= maximum:
        raise ValueError(f"slot must be in range 1..{maximum}")

    self._native.run_script(self._device, 0, slot - 1)

    if self._debug_script_slot == slot:
        self._debug_script_slot = None


def read_script_debug_info(self, timeout: float = 1.0) -> ScriptDebugInfo:
    self._ensure_open()

    if self._debug_script_slot is None:
        raise RuntimeError("CMD_SCRIPT_DEBUG is not enabled. Start a script with run_script(slot=..., debug=True) before reading debug information.")

    if timeout <= 0:
        raise ValueError("timeout must be positive")
    result = self._native.read_script_debug_info(self._device, timeout)

    return ScriptDebugInfo(current_command_counter=result.current_command_counter, error_code=result.error_code)


def get_board_info(self) -> BoardInfo:
    self._ensure_open()

    result = self._native.get_board_info(self._device)
    return BoardInfo(
        board_ver=result.board_ver, firmware_ver=result.firmware_ver,
        state_flags=result.state_flags, board_features=result.board_features,
        connection_flag=result.connection_flag, firmware_extra_id=result.firmware_extra_id,
        board_features_ext=result.board_features_ext,
        main_imu_sensor_model=result.main_imu_sensor_model,
        frame_imu_sensor_model=result.frame_imu_sensor_model,
        build_number=result.build_number, base_firmware_ver=result.base_firmware_ver,
    )


def get_board_info_3(self) -> BoardInfo3:
    self._ensure_open()

    result = self._native.get_board_info_3(self._device)

    script_slot_sizes = (
        result.script_slot_1_size, result.script_slot_2_size,
        result.script_slot_3_size, result.script_slot_4_size, result.script_slot_5_size,
        result.script_slot_6_size, result.script_slot_7_size, result.script_slot_8_size,
        result.script_slot_9_size, result.script_slot_10_size,
    )

    if get_board_info(self).firmware_ver < 2730:
        script_slot_sizes = script_slot_sizes[:5]

    return BoardInfo3(
        device_id=bytes(result.device_id), mcu_id=bytes(result.mcu_id),
        eeprom_size=result.eeprom_size,
        script_slot_sizes=script_slot_sizes,
        profile_set_slots=result.profile_set_slots, profile_set_current=result.profile_set_current,
        flash_size_pages=result.flash_size, imu_calib_info=bytes(result.imu_calib_info),
        hardware_flags=result.hardware_flags, board_features_ext2=result.board_features_ext2,
        can_driver_main_limit=result.can_driver_main_limit,
        can_driver_aux_limit=result.can_driver_aux_limit,
        adjustable_variables_total=result.adjustable_variables_total,
    )


def reset(
    self, delay_ms: int = 100, *, need_confirmation: bool = True,
    restore_state: bool = False, confirmation_timeout: float = 2.0,
    startup_delay: float = 5.0,
) -> None:
    self._ensure_open()

    if not 0 <= delay_ms <= 0xFFFF:
        raise ValueError("delay_ms must be in range 0...65535")

    if startup_delay < 0:
        raise ValueError("startup_delay must be non-negative")

    if confirmation_timeout <= 0:
        raise ValueError("confirmation_timeout must be positive")

    flags = (0x01 if need_confirmation else 0) | (0x02 if restore_state else 0)

    self._native.reset(self._device, flags, delay_ms)
    self._debug_script_slot = None

    try:
        sleep(delay_ms / 1000)
        if need_confirmation:
            self._native.expect_reset(self._device, confirmation_timeout)
    finally:
        sleep(startup_delay)
        self._native.recover(self._device)


def request_module_list(self, max_devices: int = 13,) -> tuple[CanModuleInfo, ...]:
    self._ensure_open()

    if not 1 <= max_devices <= 13:
        raise ValueError("max_devices must be in range 1...13")

    self._native.get_board_info(self._device) # check for the presence of CAN
    native_items = self._native.request_module_list(self._device, max_devices,)

    return tuple(
        CanModuleInfo(
            can_id=item.id,
            board_ver=item.board_ver,
            bootloader_ver=item.bootloader_ver,
            firmware_ver=item.firmware_ver,
        )
        for item in native_items
    )


def scan_can_device(self,) -> CanDeviceScan:
    self._ensure_open()

    self._native.get_board_info(self._device) # Fills native future cahe for checking BF_CAN_PORT in .c

    result = self._native.scan_can_device(self._device,)

    return CanDeviceScan(uid=bytes(result.UID), can_id=result.id, can_type=result.type,)


def sign_message(self, sign_type: int, message: bytes,) -> bytes:
    self._ensure_open()

    result = self._native.sign_message(self._device, sign_type, message)

    return bytes(result)


def send_transparent_command(self, target: int, payload: bytes,) -> None:
    self._ensure_open()

    self._native.send_transparent_command(self._device, target, payload)


def read_transparent_command(self, max_payload_size: int = 254,) -> tuple[int, bytes]:
    self._ensure_open()

    return self._native.read_transparent_command(self._device, max_payload_size)
