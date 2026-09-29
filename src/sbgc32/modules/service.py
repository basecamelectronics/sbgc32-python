"""Asynchronous service, diagnostics, CAN and auxiliary-output commands."""

from __future__ import annotations

import struct
from collections.abc import Mapping
from concurrent.futures import Future
from math import isclose, isfinite
from typing import TYPE_CHECKING, Callable, TypeVar

from ..commands import Command, MenuCommands
from ..crc import crc32
from ..dispatcher import CommandTimeoutError
from ..errors import (
    CanDeviceNotFoundError,
    CanNotSupportedError,
    ControllerCommandError,
    ExternalMotorNotFoundError,
)
from ..protocol import WireFrame
from ..types import (
    AutoPid2Action,
    AutoPid2Axis,
    AutoPid2Config,
    AutoPidAxisState,
    AutoPidConfig,
    AutoPidState,
    BeeperMode,
    BoardInfo,
    BoardInfo3,
    CanDeviceScan,
    CanModuleInfo,
    CommandConfirmation,
    DebugPortPacket,
    MenuCommandFlag,
    MenuExecutionResult,
    MotorsOffMode,
    PasswordProtectionFlag,
    PasswordProtectionSettings,
    PidValues,
    ScriptDebugInfo,
    ServoOutput,
    StateVars,
    SyncMotorsConfig,
    TriggerPin,
    TriggerPinState,
)
from .realtime import decode_confirmation

if TYPE_CHECKING:
    from ..device import SimpleBGC

_T = TypeVar("_T")
_U = TypeVar("_U")
_CAN_PORT_FEATURE = 1 << 10


def _uint(value: object, name: str, maximum: int) -> int:
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(f"{name} must be an integer in range 0..{maximum}")
    return value


def _confirmation(
    self: SimpleBGC, command: Command, payload: bytes, need: bool, timeout: float | None
) -> Future[CommandConfirmation | None]:
    if type(need) is not bool:
        raise TypeError("need_confirmation must be bool")
    if need:
        return self.request_raw(
            int(command), payload, timeout=timeout, route="service", decoder=decode_confirmation
        )
    return self.send_raw(int(command), payload, route="service")


def _exact(size: int, name: str) -> Callable[[WireFrame], bytes]:
    def decode(frame: WireFrame) -> bytes:
        if len(frame.payload) != size:
            raise ValueError(f"{name} response must contain {size} bytes, got {len(frame.payload)}")
        return frame.payload

    return decode


def _map(future: Future[_T], transform: Callable[[_T], _T]) -> Future[_T]:
    result: Future[_T] = Future()

    def done(source: Future[_T]) -> None:
        try:
            result.set_result(transform(source.result()))
        except BaseException as error:
            result.set_exception(error)

    future.add_done_callback(done)
    return result


def _chain(future: Future[_T], operation: Callable[[_T], Future[_U]]) -> Future[_U]:
    """Continue an asynchronous request without blocking a worker thread."""

    result: Future[_U] = Future()

    def complete(source: Future[_U]) -> None:
        try:
            result.set_result(source.result())
        except BaseException as error:
            result.set_exception(error)

    def start(source: Future[_T]) -> None:
        try:
            operation(source.result()).add_done_callback(complete)
        except BaseException as error:
            result.set_exception(error)

    future.add_done_callback(start)
    return result


def _require_can_port(
    self: SimpleBGC, *, timeout: float | None, operation: Callable[[], Future[_T]]
) -> Future[_T]:
    """Run ``operation`` only when BOARD_INFO advertises the CAN feature."""

    def continue_after_board_info(info: BoardInfo) -> Future[_T]:
        if not info.board_features & _CAN_PORT_FEATURE:
            raise CanNotSupportedError(
                "CAN command is unavailable: the controller does not advertise "
                "the BF_CAN_PORT hardware feature."
            )
        return operation()

    return _chain(get_board_info(self, timeout=timeout), continue_after_board_info)


def _external_motor_response(future: Future[_T], message: str) -> Future[_T]:
    """Turn the no-reply timeout of an external motor into a domain error."""

    result: Future[_T] = Future()

    def complete(source: Future[_T]) -> None:
        try:
            result.set_result(source.result())
        except CommandTimeoutError as error:
            unavailable = ExternalMotorNotFoundError(message)
            unavailable.__cause__ = error
            result.set_exception(unavailable)
        except BaseException as error:
            result.set_exception(error)

    future.add_done_callback(complete)
    return result


def _decode_board_info(frame: WireFrame) -> BoardInfo:
    return BoardInfo(*struct.unpack("<BHBHBIHBBBH", _exact(18, "BOARD_INFO")(frame)))


def get_board_info(
    self: SimpleBGC, *, cfg: int = 0, password: bytes | None = None, timeout: float | None = 1.0
) -> Future[BoardInfo]:
    """Read board information; optionally authenticate this port (2.73.6+).

    Passwords are arbitrary 1..32 bytes; encode text explicitly before calling.
    """

    payload = struct.pack("<H", _uint(cfg, "cfg", 0xFFFF))
    if password is not None:
        payload += _password_payload(password)

    return self.request_raw(
        int(Command.CMD_BOARD_INFO),
        payload,
        timeout=timeout,
        route="service",
        decoder=_decode_board_info,
    )


def _decode_board_info_3(frame: WireFrame) -> BoardInfo3:
    value = struct.unpack("<9s12sI5H3B2s5HHIBBB10s", _exact(69, "BOARD_INFO_3")(frame))
    return BoardInfo3(
        value[0],
        value[1],
        value[2],
        value[3:8],
        value[8],
        value[9],
        value[10],
        value[11],
        value[17],
        value[18],
        value[19],
        value[20],
        value[21],
        value[12:17],
    )


def get_board_info_3(self: SimpleBGC, *, timeout: float | None = 1.0) -> Future[BoardInfo3]:
    """Read the extended firmware, feature and hardware information record."""

    return self.request_raw(
        int(Command.CMD_BOARD_INFO_3),
        timeout=timeout,
        route="service",
        decoder=_decode_board_info_3,
    )


def _auto_pid_payload(config: AutoPidConfig) -> bytes:
    if not isinstance(config, AutoPidConfig):
        raise TypeError("config must be an AutoPidConfig")
    return struct.pack(
        "<5B14s",
        _uint(config.profile_id, "profile_id", 255),
        _uint(int(config.config_flags), "config_flags", 255),
        _uint(config.gain_vs_stability, "gain_vs_stability", 255),
        _uint(config.momentum, "momentum", 255),
        _uint(config.action, "action", 255),
        bytes(14),
    )


def tune_auto_pid(
    self: SimpleBGC,
    config: AutoPidConfig,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Start the original Auto PID tuning procedure using ``config``."""

    return _confirmation(
        self, Command.CMD_AUTO_PID, _auto_pid_payload(config), need_confirmation, timeout
    )


def break_auto_pid(
    self: SimpleBGC, *, need_confirmation: bool = False, timeout: float | None = 1.0
) -> Future[CommandConfirmation | None]:
    """Stop an Auto PID tuning procedure that is in progress."""

    return _confirmation(self, Command.CMD_AUTO_PID, bytes(19), need_confirmation, timeout)


def _pid2_frequency(value: object, factor: float, name: str) -> int:
    if type(value) not in (int, float) or not isfinite(value):
        raise TypeError(f"{name} must be a finite number of Hz")
    encoded = round(float(value) * factor)
    if not isclose(float(value), encoded / factor, abs_tol=1e-9):
        raise ValueError(f"{name} has an unsupported increment")
    return _uint(encoded, name, 255)


def _auto_pid2_payload(config: AutoPid2Config) -> bytes:
    if not isinstance(config, AutoPid2Config):
        raise TypeError("config must be an AutoPid2Config")
    action = AutoPid2Action(config.action)
    if action not in (AutoPid2Action.START, AutoPid2Action.SAVE, AutoPid2Action.START_SAVE):
        return bytes((int(action),)) + bytes(10)
    if len(config.axes) != 3 or any(not isinstance(axis, AutoPid2Axis) for axis in config.axes):
        raise TypeError("axes must contain exactly three AutoPid2Axis records")
    angles = config.multi_position_angles
    if (
        not isinstance(angles, tuple)
        or len(angles) != 4
        or any(type(value) is not int or not -128 <= value <= 127 for value in angles)
    ):
        raise ValueError("multi_position_angles must contain four signed bytes")
    payload = bytearray(
        struct.pack(
            "<BH8sB",
            int(action),
            _uint(config.command_flags, "command_flags", 65535),
            bytes(8),
            _uint(config.config_version, "config_version", 255),
        )
    )
    for axis in config.axes:
        payload.extend(
            struct.pack(
                "<BBHBBB6s",
                _uint(int(axis.axis_flags), "axis_flags", 255),
                _uint(axis.gain, "gain", 255),
                _uint(axis.stimulus_gain, "stimulus_gain", 65535),
                _uint(axis.effective_frequency, "effective_frequency", 255),
                _uint(axis.problem_frequency, "problem_frequency", 255),
                _uint(axis.problem_margin, "problem_margin", 255),
                bytes(6),
            )
        )
    payload.extend(
        struct.pack(
            "<HB BBB4b12s",
            _uint(config.general_flags, "general_flags", 65535),
            0,
            _pid2_frequency(config.test_frequency_from, 10, "test_frequency_from"),
            _pid2_frequency(config.test_frequency_to, 0.5, "test_frequency_to"),
            _uint(config.multi_position_flags, "multi_position_flags", 255),
            *angles,
            bytes(12),
        )
    )
    return bytes(payload)


def tune_auto_pid2(
    self: SimpleBGC,
    config: AutoPid2Config,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Start, save or stop the extended Auto PID 2 procedure."""

    return _confirmation(
        self, Command.CMD_AUTO_PID2, _auto_pid2_payload(config), need_confirmation, timeout
    )


def _decode_auto_pid_state(frame: WireFrame) -> AutoPidState:
    data = _exact(57, "AUTO_PID")(frame)
    p, i, d = data[:3], data[3:6], data[6:9]
    lpf = struct.unpack_from("<3H", data, 9)
    iteration = struct.unpack_from("<H", data, 15)[0]
    return AutoPidState(
        tuple(p),
        tuple(i),
        tuple(d),
        lpf,
        iteration,
        tuple(
            AutoPidAxisState(struct.unpack_from("<f", data, 17 + index * 10)[0])
            for index in range(3)
        ),
    )


def read_auto_pid_state(self: SimpleBGC, *, timeout: float | None = 1.0) -> Future[AutoPidState]:
    """Receive the progress and per-axis state published by Auto PID."""

    return self.receive_unsolicited_raw(
        int(Command.CMD_AUTO_PID), timeout=timeout, route="service", decoder=_decode_auto_pid_state
    )


def read_profile_pid_values(
    self: SimpleBGC, profile_id: int = 255, *, timeout: float | None = 1.0
) -> Future[PidValues]:
    """Read the P, I and D values of the selected controller profile."""

    from . import profiles

    def decode(data: bytes) -> PidValues:
        # P/I/D fields in MainParams3, as defined by the SerialAPI profile layout.
        return PidValues(
            data[0],
            tuple(data[offset] for offset in (1, 7, 13)),
            tuple(data[offset] for offset in (2, 8, 14)),
            tuple(data[offset] for offset in (3, 9, 15)),
        )

    return _map(
        profiles.read_params_3(self, _uint(profile_id, "profile_id", 255), timeout=timeout), decode
    )


def motors_on(
    self: SimpleBGC, *, need_confirmation: bool = False, timeout: float | None = 1.0
) -> Future[CommandConfirmation | None]:
    """Enable the gimbal motors."""

    return _confirmation(self, Command.CMD_MOTORS_ON, b"", need_confirmation, timeout)


def motors_off(
    self: SimpleBGC,
    mode: MotorsOffMode = MotorsOffMode.SAFE_STOP,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Disable the motors with the selected :class:`MotorsOffMode`."""

    return _confirmation(
        self, Command.CMD_MOTORS_OFF, bytes((int(MotorsOffMode(mode)),)), need_confirmation, timeout
    )


def synchronize_motors(
    self: SimpleBGC,
    config: SyncMotorsConfig,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Synchronize the selected motor axis according to ``config``."""

    if not isinstance(config, SyncMotorsConfig):
        raise TypeError("config must be a SyncMotorsConfig")
    return _confirmation(
        self,
        Command.CMD_SYNC_MOTORS,
        struct.pack(
            "<BBHH",
            _uint(int(config.axis), "axis", 2),
            _uint(config.power, "power", 255),
            _uint(config.time_ms, "time_ms", 65535),
            _uint(config.angle, "angle", 65535),
        ),
        need_confirmation,
        timeout,
    )


def _motor_state(frame: WireFrame, result_size: int) -> bytes:
    if len(frame.payload) < 5 or len(frame.payload) - 1 > result_size:
        raise ValueError("EXT_MOTORS_STATE response exceeds result_size")
    return frame.payload[5:]


def request_motor_state(
    self: SimpleBGC, motor_id: int, data_set: int, result_size: int, *, timeout: float | None = 1.0
) -> Future[bytes | None]:
    """Request an external-motor state block.

    Raises :class:`CanNotSupportedError` when this controller has no CAN port.
    For one motor, a missing reply becomes :class:`ExternalMotorNotFoundError`.
    Broadcast requests return ``None`` because the protocol has no one reply.
    """

    motor_id = _uint(motor_id, "motor_id", 255)
    result_size = _uint(result_size, "result_size", 255)
    payload = struct.pack("<BI", motor_id, _uint(data_set, "data_set", 0xFFFFFFFF))

    def request() -> Future[bytes | None]:
        if motor_id & (motor_id - 1):
            return self.send_raw(int(Command.CMD_EXT_MOTORS_STATE), payload, route="service")
        response = self.request_raw(
            int(Command.CMD_EXT_MOTORS_STATE),
            payload,
            timeout=timeout,
            route="service",
            decoder=lambda frame: _motor_state(frame, result_size),
        )
        return _external_motor_response(
            response,
            f"External motor 0x{motor_id:02X} did not reply to CMD_EXT_MOTORS_STATE. "
            "Check its ID, CAN connection, power, and External Motors configuration in GUI.",
        )

    return _require_can_port(self, timeout=timeout, operation=request)


def read_motor_state(
    self: SimpleBGC, result_size: int, *, timeout: float | None = 1.0
) -> Future[bytes]:
    """Receive the next externally published motor-state block.

    Raises :class:`CanNotSupportedError` if CAN is unavailable and
    :class:`ExternalMotorNotFoundError` if no external motor publishes a block.
    """

    result_size = _uint(result_size, "result_size", 255)

    def receive() -> Future[bytes]:
        response = self.receive_unsolicited_raw(
            int(Command.CMD_EXT_MOTORS_STATE),
            timeout=timeout,
            route="service",
            decoder=lambda frame: _motor_state(frame, result_size),
        )
        return _external_motor_response(
            response,
            "External motors did not publish CMD_EXT_MOTORS_STATE. Check CAN connection, "
            "power, and External Motors configuration in GUI.",
        )

    return _require_can_port(self, timeout=timeout, operation=receive)


def enter_boot_mode(
    self: SimpleBGC, *, extended: bool = True, need_confirmation: bool = False, delay_ms: int = 0
) -> Future[None]:
    """Switch the controller to bootloader mode for a firmware update."""

    if type(extended) is not bool or type(need_confirmation) is not bool:
        raise TypeError("extended and need_confirmation must be bool")
    if need_confirmation:
        raise ValueError("BOOT_MODE_3 cannot safely wait for confirmation")
    if not extended and delay_ms:
        raise ValueError("delay_ms is supported only by extended boot mode")
    return self.send_raw(
        int(Command.CMD_BOOT_MODE_3),
        struct.pack("<BH", 0, _uint(delay_ms, "delay_ms", 65535)) if extended else b"",
        route="service",
    )


def _decode_state(frame: WireFrame) -> StateVars:
    v = struct.unpack("<6sBBIHH4B4sIfIf152s", _exact(192, "READ_STATE_VARS")(frame))
    return StateVars(*v)


def read_state_vars(self: SimpleBGC, *, timeout: float | None = 1.0) -> Future[StateVars]:
    """Read persistent service counters and the controller state record."""

    return self.request_raw(
        int(Command.CMD_READ_STATE_VARS), timeout=timeout, route="service", decoder=_decode_state
    )


def _state_payload(state: StateVars) -> bytes:
    if not isinstance(state, StateVars):
        raise TypeError("state must be a StateVars")
    for name, value, size in (
        ("step_signal_vars", state.step_signal_vars, 6),
        ("shock_count", state.shock_count, 4),
        ("reserved", state.reserved, 152),
    ):
        if not isinstance(value, bytes) or len(value) != size:
            raise ValueError(f"{name} must be bytes with length {size}")
    if not all(isfinite(float(value)) for value in (state.energy, state.avg_current)):
        raise ValueError("state float values must be finite")
    return struct.pack(
        "<6sBBIHH4B4sIfIf152s",
        state.step_signal_vars,
        _uint(state.sub_error, "sub_error", 255),
        _uint(state.max_acc, "max_acc", 255),
        _uint(state.work_time, "work_time", 0xFFFFFFFF),
        _uint(state.startup_count, "startup_count", 65535),
        _uint(state.max_current, "max_current", 65535),
        _uint(state.imu_temp_min, "imu_temp_min", 255),
        _uint(state.imu_temp_max, "imu_temp_max", 255),
        _uint(state.mcu_temp_min, "mcu_temp_min", 255),
        _uint(state.mcu_temp_max, "mcu_temp_max", 255),
        state.shock_count,
        _uint(state.energy_time, "energy_time", 0xFFFFFFFF),
        float(state.energy),
        _uint(state.avg_current_time, "avg_current_time", 0xFFFFFFFF),
        float(state.avg_current),
        state.reserved,
    )


def write_state_vars(
    self: SimpleBGC,
    state: StateVars,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Write persistent service counters and state variables."""

    return _confirmation(
        self, Command.CMD_WRITE_STATE_VARS, _state_payload(state), need_confirmation, timeout
    )


def set_debug_port(
    self: SimpleBGC,
    action: int,
    filter: int = 0,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Configure the controller debug-port action and filter."""

    return _confirmation(
        self,
        Command.CMD_SET_DEBUG_PORT,
        struct.pack(
            "<BI11s", _uint(action, "action", 1), _uint(filter, "filter", 0xFFFFFFFF), bytes(11)
        ),
        need_confirmation,
        timeout,
    )


def read_debug_port(self: SimpleBGC, *, timeout: float | None = 1.0) -> Future[DebugPortPacket]:
    """Receive one packet emitted by the configured debug port."""

    def decode(frame: WireFrame) -> DebugPortPacket:
        if len(frame.payload) < 4:
            raise ValueError("SET_DEBUG_PORT packet must contain four bytes")
        return DebugPortPacket(
            *struct.unpack_from("<HBB", frame.payload), frame.payload[4:], len(frame.payload) - 4
        )

    return self.receive_unsolicited_raw(
        int(Command.CMD_SET_DEBUG_PORT), timeout=timeout, route="service", decoder=decode
    )


def set_servo_out(self: SimpleBGC, values: tuple[int, int, int, int]) -> Future[None]:
    """Set the four legacy auxiliary servo outputs."""

    if not isinstance(values, tuple) or len(values) != 4:
        raise ValueError("values must be a tuple of four servo output values")
    normalized = tuple(_servo_value(value) for value in values)
    return self.send_raw(
        int(Command.CMD_SERVO_OUT), struct.pack("<4h", *normalized), route="service"
    )


def _servo_value(value: object) -> int:
    if type(value) is not int:
        raise TypeError("servo output values must be integers")
    if not -1 <= value <= 20000:
        raise ValueError("servo output values must be in range -1..20000")
    return value


def set_servo_out_ext(self: SimpleBGC, outputs: Mapping[ServoOutput | int, int]) -> Future[None]:
    """Set selected auxiliary servo outputs by their output flags."""

    if not isinstance(outputs, Mapping) or not outputs:
        raise ValueError("outputs must be a non-empty mapping")
    selected = {int(ServoOutput(key)): _servo_value(value) for key, value in outputs.items()}
    if any(bit == 0 or bit & (bit - 1) for bit in selected):
        raise ValueError("each key must select exactly one servo output")
    return self.send_raw(
        int(Command.CMD_SERVO_OUT_EXT),
        struct.pack(
            "<I" + "h" * len(selected),
            sum(selected),
            *(selected[bit] for bit in sorted(selected)),
        ),
        route="service",
    )


def run_script(self: SimpleBGC, slot: int = 1, *, debug: bool = False) -> Future[None]:
    """Start a controller script slot, optionally enabling script debugging."""

    slot = _uint(slot, "slot", 10)
    if slot < 1:
        raise ValueError("slot must be in range 1..10")
    self._debug_script_slot = slot if debug else None
    return self.send_raw(
        int(Command.CMD_RUN_SCRIPT),
        bytes((2 if debug else 1, slot - 1)) + bytes(32),
        route="service",
    )


def stop_script(self: SimpleBGC, slot: int = 1) -> Future[None]:
    """Stop the script running in the selected slot."""

    slot = _uint(slot, "slot", 10)
    if slot < 1:
        raise ValueError("slot must be in range 1..10")
    if getattr(self, "_debug_script_slot", None) == slot:
        self._debug_script_slot = None
    return self.send_raw(
        int(Command.CMD_RUN_SCRIPT), bytes((0, slot - 1)) + bytes(32), route="service"
    )


def read_script_debug_info(
    self: SimpleBGC, *, timeout: float | None = 1.0
) -> Future[ScriptDebugInfo]:
    """Receive the current debugger position for a script started in debug mode."""

    if getattr(self, "_debug_script_slot", None) is None:
        raise RuntimeError("CMD_SCRIPT_DEBUG is not enabled; start a debug script first")
    return self.receive_unsolicited_raw(
        int(Command.CMD_SCRIPT_DEBUG),
        timeout=timeout,
        route="service",
        decoder=lambda frame: ScriptDebugInfo(
            *struct.unpack("<HB", _exact(3, "SCRIPT_DEBUG")(frame))
        ),
    )


def reset(
    self: SimpleBGC,
    delay_ms: int = 100,
    *,
    need_confirmation: bool = True,
    restore_state: bool = False,
    confirmation_timeout: float = 2.0,
    startup_delay: float = 5.0,
) -> Future[None]:
    """Restart the controller, optionally preserving its state."""

    if type(need_confirmation) is not bool or type(restore_state) is not bool:
        raise TypeError("need_confirmation and restore_state must be bool")
    if confirmation_timeout <= 0 or startup_delay < 0:
        raise ValueError("invalid reset timeout")
    self._debug_script_slot = None
    payload = struct.pack(
        "<BH",
        (1 if need_confirmation else 0) | (2 if restore_state else 0),
        _uint(delay_ms, "delay_ms", 65535),
    )
    if not need_confirmation:
        return self.send_raw(int(Command.CMD_RESET), payload, route="service")
    return self.request_raw(
        int(Command.CMD_RESET),
        payload,
        response_command_id=int(Command.CMD_RESET),
        timeout=confirmation_timeout + delay_ms / 1000,
        route="service",
        decoder=lambda _: None,
    )


def set_trigger_pin(
    self: SimpleBGC,
    pin: TriggerPin | int,
    state: TriggerPinState | int,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Set the logical state of a controller trigger pin."""

    return _confirmation(
        self,
        Command.CMD_TRIGGER_PIN,
        bytes((int(TriggerPin(pin)), int(TriggerPinState(state)))),
        need_confirmation,
        timeout,
    )


def execute_menu(
    self: SimpleBGC,
    menu_command: MenuCommands,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Execute a standard controller menu command."""

    return _confirmation(
        self,
        Command.CMD_EXECUTE_MENU,
        bytes((int(MenuCommands(menu_command)),)),
        need_confirmation,
        timeout,
    )


def execute_menu_ext(
    self: SimpleBGC,
    menu_command: MenuCommands | int,
    *,
    confirm_on_start: bool = False,
    confirm_on_finish: bool = False,
    timeout: float | None = 1.0,
) -> Future[MenuExecutionResult]:
    """Execute a menu command and optionally return start/finish confirmations."""

    if type(confirm_on_start) is not bool or type(confirm_on_finish) is not bool:
        raise TypeError("confirmation flags must be bool")
    command = _uint(int(menu_command), "menu_command", 81)
    flags = (int(MenuCommandFlag.CONFIRM) if confirm_on_start else 0) | (
        int(MenuCommandFlag.CONFIRM_ON_FINISH) if confirm_on_finish else 0
    )
    if not flags:
        source = self.send_raw(
            int(Command.CMD_EXECUTE_MENU), bytes((command, flags)), route="service"
        )
        return _map(source, lambda _: MenuExecutionResult(None, None))
    source = self.request_raw(
        int(Command.CMD_EXECUTE_MENU),
        bytes((command, flags)),
        timeout=timeout,
        route="service",
        decoder=decode_confirmation,
    )
    return _map(
        source,
        lambda confirmation: MenuExecutionResult(
            confirmation if confirm_on_start else None, confirmation if confirm_on_finish else None
        ),
    )


def beep(
    self: SimpleBGC,
    mode: BeeperMode = BeeperMode.CONFIRM,
    *,
    note_length: int = 0,
    decay_factor: int = 0,
    notes_hz: tuple[int, ...] = (),
) -> Future[None]:
    """Play a predefined beeper signal or a custom melody."""

    mode = BeeperMode(mode)
    notes = tuple(notes_hz)
    if len(notes) > 50:
        raise ValueError("notes_hz must contain at most 50 notes")
    if mode is BeeperMode.CUSTOM_MELODY and (
        not notes
        or not 1 <= _uint(note_length, "note_length", 255) <= 255
        or not 0 <= _uint(decay_factor, "decay_factor", 255) <= 15
    ):
        raise ValueError("invalid custom melody")
    if mode is not BeeperMode.CUSTOM_MELODY and notes:
        raise ValueError("notes_hz is allowed only with CUSTOM_MELODY")
    if any(not 554 <= _uint(note, "note", 65535) <= 21000 for note in notes):
        raise ValueError("custom melody frequencies must be 554..21000 Hz")
    return self.send_raw(
        int(Command.CMD_BEEP_SOUND),
        struct.pack(
            "<HBB8s" + "H" * len(notes),
            int(mode),
            _uint(note_length, "note_length", 255),
            _uint(decay_factor, "decay_factor", 255),
            bytes(8),
            *notes,
        ),
        route="service",
    )


play_beeper = beep


def sign_message(
    self: SimpleBGC, sign_type: int, message: bytes, *, timeout: float | None = 1.0
) -> Future[bytes]:
    """Ask the controller to sign a message and return its 32-byte signature."""

    if not isinstance(message, bytes) or len(message) > 32:
        raise ValueError("message must contain at most 32 bytes")
    return self.request_raw(
        int(Command.CMD_SIGN_MESSAGE),
        bytes((_uint(sign_type, "sign_type", 255),)) + message.ljust(32, b"\0"),
        timeout=timeout,
        route="service",
        decoder=_exact(32, "SIGN_MESSAGE"),
    )


def _decode_can_device_scan(frame: WireFrame) -> CanDeviceScan:
    """Decode a scan reply and identify the firmware's empty no-device reply."""

    devices = _decode_can_devices(frame)
    if not devices:
        raise CanDeviceNotFoundError("No CAN device replied to CMD_CAN_DEVICE_SCAN.")
    return devices[0]


def _decode_can_devices(frame: WireFrame) -> tuple[CanDeviceScan, ...]:
    if frame.command_id == 255:
        error = decode_confirmation(frame)
        raise ControllerCommandError(error.command_id, error.error_code, error.error_data)
    if frame.command_id != int(Command.CMD_CAN_DEVICE_SCAN):
        raise ValueError(f"expected CAN_DEVICE_SCAN response, got command {frame.command_id}")
    if len(frame.payload) % 14:
        raise ValueError("CAN_DEVICE_SCAN response must contain whole 14-byte records")
    return tuple(
        CanDeviceScan(*struct.unpack_from("<12sBB", frame.payload, offset))
        for offset in range(0, len(frame.payload), 14)
    )


def scan_can_devices(
    self: SimpleBGC, *, timeout: float | None = 1.0
) -> Future[tuple[CanDeviceScan, ...]]:
    """Return all CAN scan records, or an empty tuple when none were found.

    A CMD_ERROR reply raises ControllerCommandError with the original code and data.
    """

    def scan() -> Future[tuple[CanDeviceScan, ...]]:
        return self.request_raw(
            int(Command.CMD_CAN_DEVICE_SCAN),
            timeout=timeout,
            route="service",
            decoder=_decode_can_devices,
        )

    return _require_can_port(self, timeout=timeout, operation=scan)


def scan_can_device(self: SimpleBGC, *, timeout: float | None = 1.0) -> Future[CanDeviceScan]:
    """Scan the CAN bus and return the first device (legacy single-device API).

    Use scan_can_devices to receive every record when multiple devices exist.

    Raises :class:`CanNotSupportedError` when the controller has no CAN port.
    A successful scan with an unassigned ID is a valid result: it means the
    scan found a device that has not been assigned an ID yet. An empty reply
    means that no device answered and raises :class:`CanDeviceNotFoundError`.
    A rejected scan raises :class:`ControllerCommandError` instead.
    """

    def scan() -> Future[CanDeviceScan]:
        return self.request_raw(
            int(Command.CMD_CAN_DEVICE_SCAN),
            timeout=timeout,
            route="service",
            decoder=_decode_can_device_scan,
        )

    return _require_can_port(self, timeout=timeout, operation=scan)


def request_module_list(
    self: SimpleBGC, max_devices: int = 17, *, timeout: float | None = 1.0
) -> Future[tuple[CanModuleInfo, ...]]:
    """Read the list of modules currently discovered on the CAN bus.

    Raises :class:`CanNotSupportedError` when the controller has no CAN port.
    An empty tuple is a successful query with no attached CAN modules.
    """

    max_devices = _uint(max_devices, "max_devices", 17)
    if max_devices < 1:
        raise ValueError("max_devices must be in range 1..17")

    def decode(frame: WireFrame) -> tuple[CanModuleInfo, ...]:
        if not frame.payload:
            raise ValueError("MODULE_LIST response is empty")
        records = frame.payload[1:]
        if (
            len(records) % 13
            or len(records) // 13 > max_devices
            or frame.payload[0] != len(records) // 13
        ):
            raise ValueError("invalid MODULE_LIST response")
        return tuple(
            CanModuleInfo(*struct.unpack_from("<BHHH6s", records, offset)[:4])
            for offset in range(0, len(records), 13)
            if records[offset]
        )

    def request() -> Future[tuple[CanModuleInfo, ...]]:
        return self.request_raw(
            int(Command.CMD_MODULE_LIST), timeout=timeout, route="service", decoder=decode
        )

    return _require_can_port(self, timeout=timeout, operation=request)


def send_transparent_command(self: SimpleBGC, target: int, payload: bytes) -> Future[None]:
    """Send a raw SerialAPI payload to a downstream transparent target."""

    if not isinstance(payload, bytes) or len(payload) > 254:
        raise ValueError("payload must contain at most 254 bytes")
    return self.send_raw(
        int(Command.CMD_TRANSPARENT_SAPI),
        bytes((_uint(target, "target", 255),)) + payload,
        route="service",
    )


def read_transparent_command(
    self: SimpleBGC, max_payload_size: int = 254, *, timeout: float | None = 1.0
) -> Future[tuple[int, bytes]]:
    """Receive a raw transparent SerialAPI reply and its source address."""

    max_payload_size = _uint(max_payload_size, "max_payload_size", 254)

    def decode(frame: WireFrame) -> tuple[int, bytes]:
        if not frame.payload or len(frame.payload) - 1 > max_payload_size:
            raise ValueError("invalid TRANSPARENT_SAPI response")
        return frame.payload[0], frame.payload[1:]

    return self.receive_unsolicited_raw(
        int(Command.CMD_TRANSPARENT_SAPI), timeout=timeout, route="service", decoder=decode
    )


def _password_payload(password: bytes) -> bytes:
    if not isinstance(password, bytes) or not 1 <= len(password) <= 32:
        raise ValueError("password must contain 1..32 bytes")
    return bytes((len(password),)) + password


def read_password_protection(
    self: SimpleBGC, *, timeout: float | None = 1.0
) -> Future[PasswordProtectionSettings]:
    """Read password protection flags and reserved bytes (firmware 2.73.6+)."""

    def decode(frame: WireFrame) -> PasswordProtectionSettings:
        if frame.command_id != int(Command.CMD_PASS_PROTECT_READ):
            error = decode_confirmation(frame)
            raise ValueError(f"PASS_PROTECT_READ failed (controller error {error.error_code})")
        flags, reserved = struct.unpack("<I4s", _exact(8, "PASS_PROTECT_READ")(frame))
        return PasswordProtectionSettings(PasswordProtectionFlag(flags), reserved)

    return self.request_raw(
        int(Command.CMD_PASS_PROTECT_READ), timeout=timeout, route="service", decoder=decode
    )


def write_password_protection(
    self: SimpleBGC,
    flags: PasswordProtectionFlag | int,
    *,
    new_password: bytes | None = None,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation]:
    """Update protection flags; None keeps the password unchanged (2.73.6+).

    Authenticate with get_board_info(password=...) first on a protected port.
    """
    if isinstance(flags, bool) or not isinstance(flags, int):
        raise TypeError("flags must be PasswordProtectionFlag bits")
    payload = struct.pack("<I4x", _uint(int(flags), "flags", 0xFFFFFFFF))
    payload += b"\0" if new_password is None else _password_payload(new_password)
    return self.request_raw(
        int(Command.CMD_PASS_PROTECT_WRITE),
        payload,
        timeout=timeout,
        route="service",
        decoder=decode_confirmation,
    )


def start_module_flash(
    self: SimpleBGC, device_id: int, firmware_size_words: int, *, timeout: float | None = 5.0
) -> Future[CommandConfirmation]:
    """Start external CAN-module flashing. Size is in 32-bit words, not bytes.

    Device IDs are MODULE_LIST IDs (1..17), not CAN_DEVICE_SCAN IDs.
    Await and check the confirmation before writing any chunks.
    """
    payload = struct.pack(
        "<BI", _module_id(device_id), _uint(firmware_size_words, "firmware_size_words", 0xFFFFFFFF)
    )
    if firmware_size_words == 0:
        raise ValueError("firmware_size_words must be positive")
    return self.request_raw(
        int(Command.CMD_MODULE_FLASH_START),
        payload,
        timeout=timeout,
        route="service",
        decoder=decode_confirmation,
    )


def _module_id(device_id: int) -> int:
    if not 1 <= _uint(device_id, "device_id", 17):
        raise ValueError("device_id must be a MODULE_LIST ID in range 1..17")
    return device_id


def write_module_flash(
    self: SimpleBGC,
    device_id: int,
    packet_id: int,
    address: int,
    data: bytes,
    data_crc32: int | None = None,
    *,
    timeout: float | None = 5.0,
) -> Future[CommandConfirmation]:
    """Write 4..128 bytes, in multiples of four, at a byte offset in the file.

    packet_id starts at zero and increments modulo 256. If data_crc32 is None,
    CRC-32/ISO-HDLC is computed from data. Await each confirmation;
    error_data preserves the device ID and packet ID reported by CMD_ERROR.
    """
    if not isinstance(data, bytes) or not 4 <= len(data) <= 128 or len(data) % 4:
        raise ValueError("data must contain 4..128 bytes in multiples of four")
    address = _uint(address, "address", 0xFFFFFFFF)
    if address % 4 or address + len(data) > 0x100000000:
        raise ValueError("address must be word-aligned and data must fit in the address space")
    if data_crc32 is None:
        data_crc32 = crc32(data)
    payload = (
        struct.pack(
            "<BBII",
            _module_id(device_id),
            _uint(packet_id, "packet_id", 255),
            address,
            _uint(data_crc32, "data_crc32", 0xFFFFFFFF),
        )
        + data
    )
    return self.request_raw(
        int(Command.CMD_MODULE_FLASH_WRITE),
        payload,
        timeout=timeout,
        route="service",
        decoder=decode_confirmation,
    )


def finish_module_flash(
    self: SimpleBGC, device_id: int, file_crc32: int, *, timeout: float | None = 5.0
) -> Future[CommandConfirmation]:
    """Finish flashing with the bootloader CRC32 of the entire .bin file."""
    payload = struct.pack("<BI", _module_id(device_id), _uint(file_crc32, "file_crc32", 0xFFFFFFFF))
    return self.request_raw(
        int(Command.CMD_MODULE_FLASH_FINISH),
        payload,
        timeout=timeout,
        route="service",
        decoder=decode_confirmation,
    )


def set_transparent_proxy(self: SimpleBGC, port1: int, port2: int) -> Future[None]:
    """Bridge serial ports (2.74.5+); 0 selects the current port, other IDs start at 1.

    Both ports must be enabled for Serial API. There is no success response:
    completion only confirms transmission. CMD_ERROR, if any, is unsolicited.
    The bridged ports subsequently forward raw data instead of Serial API.
    """
    payload = bytes((_uint(port1, "port1", 255), _uint(port2, "port2", 255)))
    if port1 == port2:
        raise ValueError("proxy ports must be different")
    return self.send_raw(int(Command.CMD_SET_TRANSP_PROXY), payload, route="service")


def scan_udrv_devices(
    self: SimpleBGC, *, timeout: float | None = 5.0
) -> Future[tuple[CanDeviceScan, ...]]:
    """Scan uDrv modules, detect their IMU and automatically assign IDs.

    Returns all 14-byte records from CMD_CAN_DEVICE_SCAN (#96). An empty tuple
    means no devices were found. This command changes device assignments.
    A CMD_ERROR reply raises ControllerCommandError; it is not treated as an
    empty scan. Codes are command-specific and are preserved without translation.
    """

    return self.request_raw(
        int(Command.CMD_UDRV_DEVICE_SCAN),
        response_command_id=int(Command.CMD_CAN_DEVICE_SCAN),
        timeout=timeout,
        route="service",
        decoder=_decode_can_devices,
    )
