from __future__ import annotations

from time import sleep

from collections.abc import Sequence
from . import _adjvars, _control, _realtime, _service
from ._serial_api_library import NativeError
from .backends import create_backend
from .commands import Command, MenuCommands, ResponseCommand
from .types import (
    AdjustableVariable,
    Angles,
    AnglesExt,
    AutoPid2Config,
    AutoPidConfig,
    AutoPidState,
    BeeperMode,
    BoardInfo,
    BoardInfo3,
    CommandConfirmation,
    ControlQuatStatus,
    ControlQuatStatusFlag,
    DebugPortPacket,
    DataStreamConfig,
    DebugVarInfo,
    ImuType,
    ControlAxis,
    ControlConfig,
    MotorsOffMode,
    RealtimeData3,
    RealtimeData4,
    RealtimeDataCustom,
    RealtimeDataCustomFlag,
    SelectImuAction,
    ScriptDebugInfo,
    StateVars,
    SyncMotorsConfig,
)


class SimpleBGC:
    """ Connection-oriented public interface for a SimpleBGC controller. """

    def __init__(
        self,
        port: str,
        baud_rate: int = 115200,
        startup_delay: float = 1.0,
        backend: str = "pyserial",
    ) -> None:
        """\
            @brief  Opens a SerialAPI connection to a SimpleBGC controller.

            @param  port              - system serial port name, for example "COM4".
                    baud rate          - serial port speed in bits per second.
                    startup_delay     - delay after opening the port, in seconds.
                    backend           - transport implementation to use. native_win or pyserial.
        """
        if startup_delay < 0:
            raise ValueError("startup_delay must be non-negative")
        self._backend = create_backend(backend)
        self._native = self._backend.library
        self._device = self._backend.open(port, baud_rate)
        sleep(startup_delay)
        self._closed = False
        self._debug_script_slot: int | None = None

    def execute(self, command: Command | int, **kwargs) -> object:
        """\
            @brief  Executes a supported SerialAPI command through this facade.
        """
        if isinstance(command, ResponseCommand):
            raise ValueError(f"{command.name} is sent by the board and cannot be executed.")
        command = Command(command)

        reads = {
            Command.CMD_GET_ANGLES: self.get_angles,
            Command.CMD_GET_ANGLES_EXT: self.get_angles_ext,
            Command.CMD_REALTIME_DATA: self.get_realtime_data,
            Command.CMD_REALTIME_DATA_3: self.get_realtime_data_3,
            Command.CMD_REALTIME_DATA_4: self.get_realtime_data_4,
            Command.CMD_BOARD_INFO: self.get_board_info,
            Command.CMD_BOARD_INFO_3: self.get_board_info_3,
            Command.CMD_MOTORS_ON: self.motors_on,
        }
        if command in reads:
            if kwargs:
                raise TypeError(f"{command.name} does not accept keyword arguments: {', '.join(kwargs)}")
            return reads[command]()

        if command is Command.CMD_REALTIME_DATA_CUSTOM:
            flags = self._required_argument(command, kwargs, "flags")
            self._reject_remaining_arguments(command, kwargs)
            return self.get_realtime_data_custom(flags)
        if command is Command.CMD_CONTROL_QUAT_STATUS:
            flags = self._required_argument(command, kwargs, "flags")
            self._reject_remaining_arguments(command, kwargs)
            return self.get_control_quat_status(flags)
        if command is Command.CMD_SELECT_IMU_3:
            imu_type = self._required_argument(command, kwargs, "imu_type")
            action = kwargs.pop("action", SelectImuAction.SIMPLE_SELECT)
            time_ms = kwargs.pop("time_ms", 0)
            need_confirmation = kwargs.pop("need_confirmation", False)
            self._reject_remaining_arguments(command, kwargs)
            return self.select_imu_3(
                imu_type,
                action,
                time_ms,
                need_confirmation=need_confirmation,
            )
        if command is Command.CMD_GET_ADJ_VARS_VAL:
            ids = self._required_argument(command, kwargs, "ids")
            self._reject_remaining_arguments(command, kwargs)
            return self.get_adj_vars(ids)
        if command is Command.CMD_SET_ADJ_VARS_VAL:
            variables = self._required_argument(command, kwargs, "variables")
            need_confirmation = kwargs.pop("need_confirmation", False)
            self._reject_remaining_arguments(command, kwargs)
            return self.set_adj_vars(variables, need_confirmation=need_confirmation)
        if command is Command.CMD_SAVE_PARAMS_3:
            ids = kwargs.pop("ids", None)
            all_active = kwargs.pop("all_active", False)
            need_confirmation = kwargs.pop("need_confirmation", False)
            self._reject_remaining_arguments(command, kwargs)
            if all_active:
                if ids is not None:
                    raise TypeError("CMD_SAVE_PARAMS_3 accepts either ids=... or all_active=True")
                return self.save_all_adj_vars(need_confirmation=need_confirmation)
            if ids is None:
                raise TypeError("CMD_SAVE_PARAMS_3 requires ids=(...) or all_active=True")
            return self.save_adj_vars(ids, need_confirmation=need_confirmation)

        actions = {
            Command.CMD_RUN_SCRIPT: self.run_script,
            Command.CMD_MOTORS_OFF: self.motors_off,
            Command.CMD_BEEP_SOUND: self.beep,
        }
        if command in actions:
            return actions[command](**kwargs)
        if command is Command.CMD_EXECUTE_MENU:
            menu_command = self._required_argument(command, kwargs, "menu_command")
            need_confirmation = kwargs.pop("need_confirmation", False)
            self._reject_remaining_arguments(command, kwargs)
            return self.execute_menu(menu_command, need_confirmation=need_confirmation)
        if command is Command.CMD_CONTROL:
            axes = self._required_argument(command, kwargs, "axes")
            need_confirmation = kwargs.pop("need_confirmation", False)
            self._reject_remaining_arguments(command, kwargs)
            return self.control(axes, need_confirmation=need_confirmation)
        if command is Command.CMD_CONTROL_CONFIG:
            config = kwargs.pop("config", None)
            confirm_control = kwargs.pop("confirm_control", None)
            need_confirmation = kwargs.pop("need_confirmation", False)
            self._reject_remaining_arguments(command, kwargs)
            return self.configure_control(
                config,
                confirm_control=confirm_control,
                need_confirmation=need_confirmation,
            )
        raise NotImplementedError(f"Command {command.name} is not implemented")

    # Public command methods deliberately live on the facade.  The protocol
    # implementation itself remains in the focused private modules.
    def control(
        self,
        axes: tuple[ControlAxis, ControlAxis, ControlAxis],
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """ @brief  Controls gimbal movement.

            @code   from sbgc32 import ControlAxis as CA, ControlMode as CM, ControlFlag as CF
                    SimpleBGC.control((
                        CA(mode=CM.NO_CONTROL, angle=0.0),
                        CA(mode=CM.ANGLE, angle=-10.0),
                        CA(mode=CM.NO_CONTROL, angle=0.0),
                    ))

            @param  axes              - roll, pitch and yaw control records.
                    need_confirmation - request CMD_CONFIRM from supported firmware.
        """
        return _control.control(self, axes, need_confirmation=need_confirmation)

    def configure_control(
        self,
        config: ControlConfig | None = None,
        *,
        confirm_control: bool | None = None,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """ @brief  Configure the handling of CMD_CONTROL command.

            @code   from sbgc32 import ControlConfig as CC, ControlAxisConfig as CAC
                    config = CC(
                        timeout_ms=1_000,
                        channel_priorities=(0, 0, 0, 0, 100),
                        axes=(CAC(), CAC(), CAC(angle_lpf=2, speed_lpf=2, acceleration_limit=90, jerk_slope=5))
                    )

                    SimpleBGC.configure_control(config, confirm_control=False)

            @param  config            - control configuration; omitted fields keep defaults.
                    confirm_control   - enable or disable controller confirmations.
                    need_confirmation - request confirmation for this configuration command.
        """
        return _control.configure_control(
            self,
            config,
            confirm_control=confirm_control,
            need_confirmation=need_confirmation,
        )

    def control_config(
        self,
        config: ControlConfig | None = None,
        *,
        confirm_control: bool | None = None,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """ @brief   """
        return self.configure_control(
            config,
            confirm_control=confirm_control,
            need_confirmation=need_confirmation,
        )


    # ADJVAR MODULE
    def get_adj_vars(self, ids: object) -> tuple[AdjustableVariable, ...]:
        """ @brief  Requests values of adjustable variables.

            @code   variables = SimpleBGC.get_adj_vars((1, 2, 3))
                    for variable in variables:
                        print(variable.id, variable.value)

            @param  ids - iterable of up to 40 distinct adjustable-variable IDs.
        """
        return _adjvars.get_adj_vars(self, ids)

    def get_adj_var(self, id: int) -> AdjustableVariable:
        """ @brief  Requests the value of one adjustable variable.

            @code   variable = SimpleBGC.get_adj_var(1)
                    print(variable.id, variable.value)

            @param  id - adjustable-variable ID.
        """
        return _adjvars.get_adj_var(self, id)

    def set_adj_vars(
        self, variables: object, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """ @brief  Sets new values for a set of adjustable variables in RAM.

            @code   from sbgc32 import AdjustableVariable as AV
                    SimpleBGC.set_adj_vars((
                                AV(id=1, value=5),
                                AV(id=2, value=-10),
                            ))

            @param  variables         - 1 to 40 variable records.
                    need_confirmation - request CMD_CONFIRM from supported firmware.
        """
        return _adjvars.set_adj_vars(self, variables, need_confirmation=need_confirmation)

    def set_adj_var(
        self, id: int, value: int, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """ @brief  Sets one adjustable-variable value in RAM.

            @code   SimpleBGC.set_adj_var(0, 5)

            @param  id                - adjustable-variable ID.
                    value             - signed 32-bit raw variable value.
                    need_confirmation - request CMD_CONFIRM from supported firmware.
        """
        return _adjvars.set_adj_var(self, id, value, need_confirmation=need_confirmation)

    def save_adj_vars(
        self, ids: object, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """ todo
        """
        return _adjvars.save_adj_vars(self, ids, need_confirmation=need_confirmation)

    def save_all_adj_vars(self, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """ @brief  Saves all active, unsaved adjustable variables to EEPROM.

            @code   SimpleBGC.save_all_adj_vars()
        """
        return _adjvars.save_all_adj_vars(self, need_confirmation=need_confirmation)

    # REALTIME MODEL
    def get_angles(self) -> Angles:
        """Read the current IMU, target, and target-speed angles.

        Returns:
            An :class:`Angles` object with named roll, pitch, and yaw values.
        """
        return _realtime.get_angles(self)

    def get_angles_ext(self) -> AnglesExt:
        """Read the extended angle representation.

        Returns:
            An :class:`AnglesExt` object with raw per-axis values and
            converted IMU, target, and frame-camera angle properties.
        """
        return _realtime.get_angles_ext(self)

    def get_realtime_data(self) -> RealtimeData3:
        """Read ``REALTIME_DATA_3`` using its legacy method name.

        Returns:
            The same :class:`RealtimeData3` result as
            :meth:`get_realtime_data_3`.
        """
        return _realtime.get_realtime_data_3(self)

    def get_realtime_data_3(self) -> RealtimeData3:
        """Read the fixed ``REALTIME_DATA_3`` controller packet.

        Returns:
            A :class:`RealtimeData3` object. Most fields preserve their raw
            protocol representation; ``bat_level`` is expressed in
            centivolts.
        """
        return _realtime.get_realtime_data_3(self)

    def get_realtime_data_4(self) -> RealtimeData4:
        """Read the extended ``REALTIME_DATA_4`` controller packet.

        Returns:
            A :class:`RealtimeData4` object, including every
            :class:`RealtimeData3` field.
        """
        return _realtime.get_realtime_data_4(self)

    def get_realtime_data_custom(self, flags: RealtimeDataCustomFlag | int) -> RealtimeDataCustom:
        """Request a realtime packet containing selected fields.

        Args:
            flags: A combination of :class:`RealtimeDataCustomFlag` members.

        Returns:
            A :class:`RealtimeDataCustom` object whose ``fields`` mapping is
            keyed by the selected flags.

        Raises:
            ValueError: If ``flags`` contains unsupported bits or the selected
                protocol payload is larger than 255 bytes.
        """
        return _realtime.get_realtime_data_custom(self, flags)


    def read_rc_inputs(self, sources: object) -> tuple[int | None, ...]:
        """Read RC sources as normalized ``-500`` to ``500`` values.

        Args:
            sources: An iterable containing from one to 42 RC source IDs or
                :class:`RcInputSource` values.

        Returns:
            Values in the same order as ``sources``. An inactive source is
            represented by ``None``.

        Raises:
            TypeError: If ``sources`` is not an iterable.
            ValueError: If the number or values of source IDs are invalid.
        """
        return _realtime.read_rc_inputs(self, sources)

    def set_api_virtual_channels(self, values: object) -> None:
        """ todo """
        _control.set_api_virtual_channels(self, values)

    def start_data_stream(self, config: DataStreamConfig, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """Start a periodic controller data stream.

        Args:
            config: Command, interval, command-specific configuration, and
                synchronization setting for the stream.
            need_confirmation: Request ``CMD_CONFIRM`` from firmware that
                supports confirmations.

        Returns:
            A command confirmation when requested and supported; otherwise
            ``None``.
        """
        return _realtime.start_data_stream(self, config, need_confirmation=need_confirmation)

    def stop_data_stream(self, config: DataStreamConfig, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """Stop the stream described by ``config``.

        Args:
            config: The same stream configuration used to start the stream.
            need_confirmation: Request ``CMD_CONFIRM`` from firmware that
                supports confirmations.

        Returns:
            A command confirmation when requested and supported; otherwise
            ``None``.
        """
        return _realtime.stop_data_stream(self, config, need_confirmation=need_confirmation)

    def read_data_stream(self, config: DataStreamConfig, size: int | None = None,) -> bytes:
        """Read one raw payload from a configured data stream.

        Args:
            config: The stream configuration. It determines the payload size
                for known realtime and helper stream commands.
            size: Required payload size for commands whose size is not known
                to the library. Ignored for known commands.

        Returns:
            The unparsed controller payload.

        Raises:
            ValueError: If the configuration or payload size is invalid.
        """
        return _realtime.read_data_stream(self, config, size)

    def request_debug_var_info_3(self) -> tuple[DebugVarInfo, ...]:
        """Request the complete ``DEBUG_VARS_INFO_3`` metadata list.

        Returns:
            Index-ordered :class:`DebugVarInfo` records. Pass this complete
            result unchanged to :meth:`request_debug_var_values_3`.
        """
        return _realtime.request_debug_var_info_3(self)

    def format_debug_var_info_3(self, variables: Sequence[DebugVarInfo]) -> str:
        """Format debug-variable metadata as a compact text table.

        Args:
            variables: Records returned by :meth:`request_debug_var_info_3`.

        Returns:
            A human-readable table with variable indexes, names, types, and
            protocol flags.
        """
        return _realtime.format_debug_var_info_3(variables)

    def print_debug_var_info_3(self, variables: Sequence[DebugVarInfo]) -> None:
        """Print debug-variable metadata as a formatted table.

        Args:
            variables: Records returned by :meth:`request_debug_var_info_3`.
        """
        return _realtime.print_debug_var_info_3(variables)

    def request_debug_var_values_3(self, variables: Sequence[DebugVarInfo], selected_indexes: Sequence[int] | None = None,) -> tuple[DebugVarInfo, ...]:
        """Request current values for debug variables.

        Args:
            variables: The complete, index-ordered metadata result from
                :meth:`request_debug_var_info_3`.
            selected_indexes: Optional variable indexes to request. Unselected
                records are returned unchanged.

        Returns:
            Metadata records populated with ``raw_value`` and decoded ``value``
            for each requested variable.

        Raises:
            ValueError: If ``variables`` is not a complete, index-ordered
                metadata list or a selected index is invalid.
        """
        return _realtime.request_debug_var_values_3(self, variables, selected_indexes)

    def select_imu_3(self, imu_type: ImuType | int, action: SelectImuAction | int = SelectImuAction.SIMPLE_SELECT,
        time_ms: int = 0, *, need_confirmation: bool = False,) -> CommandConfirmation | None:
        """Select an IMU or perform an extended IMU calibration action.

        Args:
            imu_type: The IMU addressed by the command.
            action: Selection or calibration action to perform.
            time_ms: Action-specific duration or timeout in milliseconds.
            need_confirmation: Request ``CMD_CONFIRM`` from firmware that
                supports confirmations.

        Returns:
            A command confirmation when requested and supported; otherwise
            ``None``.

        Raises:
            ValueError: If an enum value or ``time_ms`` is invalid.
        """
        return _realtime.select_imu_3(self, imu_type, action, time_ms, need_confirmation=need_confirmation,)

    def get_control_quat_status(self, flags: ControlQuatStatusFlag | int,) -> ControlQuatStatus:
        """Read selected quaternion-control status fields (firmware 2.73+).

        Args:
            flags: Combination of :class:`ControlQuatStatusFlag` members to
                include in the controller response.

        Returns:
            A :class:`ControlQuatStatus` object. Fields not requested by
            ``flags`` are ``None``; speed values retain raw protocol units.

        Raises:
            ValueError: If no fields or unsupported status bits are selected.
        """
        return _realtime.get_control_quat_status(self, flags)


    def motors_on(self) -> None:
        """ @brief  Turns on gimbal motors.

            @code   SimpleBGC.motors_on()
         """
        _service.motors_on(self)

    def tune_auto_pid(
        self, config: AutoPidConfig, *, need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Start legacy automatic PID tuning (firmware before 2.73)."""
        return _service.tune_auto_pid(self, config, need_confirmation=need_confirmation)

    def break_auto_pid(self, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """Stop legacy automatic PID tuning."""
        return _service.break_auto_pid(self, need_confirmation=need_confirmation)

    def tune_auto_pid2(
        self, config: AutoPid2Config, *, need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Send an automatic PID v2 request (firmware 2.73+)."""
        return _service.tune_auto_pid2(self, config, need_confirmation=need_confirmation)

    def read_auto_pid_state(self) -> AutoPidState:
        """Read the latest automatic PID progress packet."""
        return _service.read_auto_pid_state(self)

    def synchronize_motors(
        self, config: SyncMotorsConfig, *, need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Synchronize parallel motors. This command can move the gimbal."""
        return _service.synchronize_motors(self, config, need_confirmation=need_confirmation)

    def request_motor_state(self, motor_id: int, data_set: int, result_size: int) -> bytes:
        """Request raw EXT_MOTORS_STATE data for one motor."""
        return _service.request_motor_state(self, motor_id, data_set, result_size)

    def read_motor_state(self, result_size: int) -> bytes:
        """Read a queued raw EXT_MOTORS_STATE payload."""
        return _service.read_motor_state(self, result_size)

    def enter_boot_mode(
        self, *, extended: bool = True, need_confirmation: bool = False, delay_ms: int = 0,
    ) -> None:
        """Enter the bootloader; no further SerialAPI communication is allowed afterwards."""
        _service.enter_boot_mode(
            self, extended=extended, need_confirmation=need_confirmation, delay_ms=delay_ms,
        )

    def read_state_vars(self) -> StateVars:
        """Read persistent maintenance and cumulative state counters."""
        return _service.read_state_vars(self)

    def write_state_vars(
        self, state: StateVars, *, need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Write persistent state counters; this changes controller memory."""
        return _service.write_state_vars(self, state, need_confirmation=need_confirmation)

    def set_debug_port(
        self, action: int, filter: int = 0, *, need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Start or stop streaming controller packets to the debug port."""
        return _service.set_debug_port(self, action, filter, need_confirmation=need_confirmation)

    def read_debug_port(self) -> DebugPortPacket:
        """Read one queued debug-port packet into a 255-byte payload buffer."""
        return _service.read_debug_port(self)

    def motors_off(self, mode: MotorsOffMode = MotorsOffMode.SAFE_STOP) -> None:
        """ @brief  Turns off gimbal motors with the selected stop mode.
                    SAFE_STOP is the default recommended by SerialAPI. Firmware
                    before 2.68b7 ignores the mode byte.

            @code   from sbgc32 import MotorsOffMode as MOM
                    SimpleBGC.motors_off(MOM.NORMAL)

            @param  mode - required mode: NORMAL, BREAK, SAFE_STOP
        """
        _service.motors_off(self, mode)

    def beep(
        self,
        mode: BeeperMode = BeeperMode.CONFIRM, *,
        note_length: int = 0,
        decay_factor: int = 0,
        notes_hz: tuple[int, ...] = (),
    ) -> None:
        """ @brief  Plays a standard beeper signal or a custom motor melody.

            @code   from sbgc32 import BeeperMode as BM
                    SimpleBGC.beep(BeeperMode.INTRO)

            @param
        """
        _service.beep(
            self,
            mode,
            note_length=note_length,
            decay_factor=decay_factor,
            notes_hz=notes_hz,
        )

    def play_beeper(
        self,
        mode: BeeperMode = BeeperMode.CONFIRM,
        *,
        note_length: int = 0,
        decay_factor: int = 0,
        notes_hz: tuple[int, ...] = (),
    ) -> None:
        """ @brief  Alias for beep. """
        self.beep(
            mode,
            note_length=note_length,
            decay_factor=decay_factor,
            notes_hz=notes_hz,
        )

    def execute_menu(
        self, menu_command: MenuCommands, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """ @brief  Executes one supported action.

            @code   from sbgc32 import MenuCommands
                    SimpleBGC.execute_menu(MenuCommands.MENU_CMD_NO)

            @param  MenuCommands - list of menu commands.
                    need_confirmation - request CMD_CONFIRM from supported firmware.
        """
        return _service.execute_menu(self, menu_command, need_confirmation=need_confirmation)

    def run_script(self, slot: int = 1, *, debug: bool = False) -> None:
        """ @brief  Starts a script from the selected board slot.

            @code   SimpleBGC.run_script(slot=1, debug=True)
                    debug_1 = SimpleBGC.read_script_debug_info(timeout=2.0)
                    debug_2 = SimpleBGC.read_script_debug_info(timeout=2.0)
                    print(debug_1, debug_2)

            @param  slot  - script slot number.
                    debug - start in debug mode.
        """
        _service.run_script(self, slot, debug=debug)

    def stop_script(self, slot: int = 1) -> None:
        """ @brief  Stops the script running in the selected board slot.

            @code   SimpleBGC.stop_script(slot=1)
            @param  slot  - script slot number.
        """
        _service.stop_script(self, slot)

    def read_script_debug_info(self, timeout: float = 1.0) -> ScriptDebugInfo:
        """ @brief  Reads the most recent information. """
        return _service.read_script_debug_info(self, timeout)

    def get_board_info(self) -> BoardInfo:
        """ @brief  Reads version and board information

             @code   board = SimpleBGC.get_board_info()
                     print(f"Board: {board.board_ver}")
         """
        return _service.get_board_info(self)

    def get_board_info_3(self) -> BoardInfo3:
        """ @brief  Reads additional board information.

            @code   board3 = SimpleBGC.get_board_info_3()

                    print(f"Device ID: {board3.device_id.hex().upper()}")
                    print(f"EEPROM size: {board3.eeprom_size} bytes")
        """
        return _service.get_board_info_3(self)

    def reset(
        self,
        delay_ms: int = 100, *,
        need_confirmation: bool = True,
        restore_state: bool = False,
        confirmation_timeout: float = 2.0,
        startup_delay: float = 5.0,
    ) -> None:
        """ @brief  Resets the controller.

            @code   SimpleBGC.reset(need_confirmation=False, restore_state=True)

            @params delay_ms -
                    need_confirmation - request CMD_CONFIRM from supported firmware.
        """
        _service.reset(
            self,
            delay_ms,
            need_confirmation=need_confirmation,
            restore_state=restore_state,
            confirmation_timeout=confirmation_timeout,
            startup_delay=startup_delay,
        )

    @staticmethod
    def _required_argument(command: Command, kwargs: dict[str, object], name: str) -> object:
        try:
            value = kwargs.pop(name)
        except KeyError as error:
            raise TypeError(f"{command.name} requires {name}=...") from error
        return value

    @staticmethod
    def _reject_remaining_arguments(command: Command, kwargs: dict[str, object]) -> None:
        if kwargs:
            raise TypeError(f"{command.name} does not accept keyword arguments: {', '.join(kwargs)}")

    def close(self) -> None:
        """ @brief  Closes the serial connection and releases its resources. """
        if not self._closed:
            self._backend.close(self._device)
            self._closed = True
            self._debug_script_slot = None

    def _ensure_open(self) -> None:
        if self._closed:
            raise NativeError("The SimpleBGC connection is already closed.")

    def __enter__(self) -> "SimpleBGC":
        self._ensure_open()
        return self

    def __exit__(self, exception_type, exception, traceback) -> None:
        self.close()
