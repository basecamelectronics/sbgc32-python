"""Service commands: board information, menus, sounds, scripts, and reset."""

from __future__ import annotations

from time import sleep

from ._control import make_confirmation, validate_uint
from .commands import MenuCommands
from .types import BeeperMode, BoardInfo, BoardInfo3, CommandConfirmation, MotorsOffMode, ScriptDebugInfo


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
            raise ValueError("CUSTOM_MELODY requires notes_hz with 1..50 frequencies")
        if not 1 <= note_length <= 0xFF:
            raise ValueError("CUSTOM_MELODY note_length must be in range 1..255")
        if not 0 <= decay_factor <= 15:
            raise ValueError("CUSTOM_MELODY decay_factor must be in range 0..15")
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
    return make_confirmation(self._native.execute_menu(
        self._device, int(selected_command), need_confirmation=need_confirmation
    ))


def _script_slot_max(self) -> int:
    """Return the largest zero-based script slot supported by the board."""
    board_info = get_board_info_3(self)
    return 10 if len(board_info.script_slot_sizes) == 10 else 5


def run_script(self, slot: int = 1, *, debug: bool = False) -> None:
    self._ensure_open()
    maximum = _script_slot_max(self)
    if not 1 <= slot <= maximum - 1:
        raise ValueError(f"slot must be in range 1..{maximum}")
    self._native.run_script(self._device, 2 if debug else 1, slot)
    self._debug_script_slot = slot if debug else None


def stop_script(self, slot: int = 1) -> None:
    self._ensure_open()
    maximum = _script_slot_max(self)
    if not 1 <= slot <= maximum - 1:
        raise ValueError(f"slot must be in range 1..{maximum}")
    self._native.run_script(self._device, 0, slot)
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
    # Extra BoardInfo3 fields, including script slots 6..10, were added in
    # firmware 2.73. Older firmware returns no extended feature bitmap.
    if result.board_features_ext2 == 0:
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
        raise ValueError("delay_ms must be in range 0..65535")
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
