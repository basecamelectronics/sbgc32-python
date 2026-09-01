from __future__ import annotations

from time import sleep

from collections.abc import Sequence
from . import _adjvars, _control, _realtime, _service
from ._serial_api_library import NativeError
from .backends import create_backend
from .commands import Command, MenuCommands
from .types import (
    AdjustableVariable,
    AdjustableVariableFloat,
    AdjustableVariableTriggerSlot,
    AdjustableVariableAnalogSlot,
    AdjustableVariablesConfig,
    AdjustableVariablesState,
    AdjustableVariableInfo,
    Angles,
    AnglesExt,
    AutoPid2Config,
    AutoPidConfig,
    AutoPidState,
    BeeperMode,
    BoardInfo,
    BoardInfo3,
    CanModuleInfo,
    CanDeviceScan,
    CommandConfirmation,
    ControlQuatStatus,
    ControlQuatStatusFlag,
    DebugPortPacket,
    DataStreamConfig,
    DebugVarInfo,
    ImuType,
    ControlAxis,
    ControlConfig,
    ControlExt,
    ControlQuat,
    ControlQuatConfig,
    ExternalMotorAction,
    ExternalMotorControl,
    ExternalMotorsControlConfig,
    MotorsOffMode,
    MenuExecutionResult,
    PidValues,
    RealtimeData3,
    RealtimeData4,
    RealtimeDataCustom,
    RealtimeDataCustomFlag,
    SelectImuAction,
    ScriptDebugInfo,
    StateVars,
    SyncMotorsConfig,
    ServoOutput,
    TriggerPin,
    TriggerPinState,
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

        """ Opens a SerialAPI connection to a SimpleBGC controller.

        Args:
            port: system serial port name, for example "COM4".
            baud rate: serial port speed in bits per second.
            startup_delay: delay after opening the port, in seconds.
            backend: transport implementation.

        Raises: 
            startup_delay must be non-negative. 
            backend must be native_win or pyserial.
        """

        if startup_delay < 0:
            raise ValueError("startup_delay must be non-negative")
        self._backend = create_backend(backend)
        self._native = self._backend.library
        self._device = self._backend.open(port, baud_rate)
        sleep(startup_delay)
        self._closed = False
        self._debug_script_slot: int | None = None


    # CONTROL MODULE 
    def set_api_virtual_channels(self, values: object) -> None:
        _control.set_api_virtual_channels(self, values)


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


    def control_config(self, config: ControlConfig | None = None, *, confirm_control: bool | None = None, need_confirmation: bool = False,) -> CommandConfirmation | None:
        return self.configure_control(config, confirm_control=confirm_control, need_confirmation=need_confirmation,)


    def control_ext(self, control: ControlExt) -> None:
        _control.control_ext(self, control)


    def control_quat(self, control: ControlQuat, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        return _control.control_quat(self, control, need_confirmation=need_confirmation)


    def configure_control_quat(self, config: ControlQuatConfig, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        return _control.configure_control_quat(self, config, need_confirmation=need_confirmation)


    def ext_motors_action(self, motors: int, action: ExternalMotorAction | int, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        return _control.ext_motors_action(self, motors, action, need_confirmation=need_confirmation)


    def control_ext_motors(self, control: ExternalMotorControl, motors: int, data_set: int = 0, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        return _control.control_ext_motors(self, control, motors, data_set, need_confirmation=need_confirmation)


    def configure_ext_motors(self, config: ExternalMotorsControlConfig, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        return _control.configure_ext_motors(self, config, need_confirmation=need_confirmation)


    def set_api_virtual_channels_hr(self, values: object) -> None:
        _control.set_api_virtual_channels_hr(self, values)


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


    def set_adj_vars(self, variables: object, *, need_confirmation: bool = False) -> CommandConfirmation | None:
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


    def set_adj_var(self, id: int, value: int, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """ @brief  Sets one adjustable-variable value in RAM.

            @code   SimpleBGC.set_adj_var(0, 5)

            @param  id                - adjustable-variable ID.
                    value             - signed 32-bit raw variable value.
                    need_confirmation - request CMD_CONFIRM from supported firmware.
        """
        return _adjvars.set_adj_var(self, id, value, need_confirmation=need_confirmation)


    def save_adj_vars(self, ids: object, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """ todo
        """
        return _adjvars.save_adj_vars(self, ids, need_confirmation=need_confirmation)


    def save_all_adj_vars(self, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """ @brief  Saves all active, unsaved adjustable variables to EEPROM.

            @code   SimpleBGC.save_all_adj_vars()
        """
        return _adjvars.save_all_adj_vars(self, need_confirmation=need_confirmation)


    def get_adj_vars_float(self, ids: object) -> tuple[AdjustableVariableFloat, ...]:
        return _adjvars.get_adj_vars_float(self, ids)


    def get_adj_var_float(self, id: int) -> AdjustableVariableFloat:
        return _adjvars.get_adj_var_float(self, id)


    def set_adj_vars_float(self, variables: object, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        return _adjvars.set_adj_vars_float(self, variables, need_confirmation=need_confirmation)


    def set_adj_var_float(self, id: int, value: float, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        return _adjvars.set_adj_var_float(self, id, value, need_confirmation=need_confirmation)


    def read_adj_vars_config(self) -> AdjustableVariablesConfig:
        return _adjvars.read_adj_vars_config(self)


    def write_adj_vars_config(self, config: AdjustableVariablesConfig, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        return _adjvars.write_adj_vars_config(self, config, need_confirmation=need_confirmation)

    def get_adj_vars_state(
        self,
        trigger_slot: int,
        analog_source_id: int,
        analog_variable_id: int,
        lut_source_id: int,
        lut_variable_id: int,
    ) -> AdjustableVariablesState:
        return _adjvars.get_adj_vars_state(self, trigger_slot, analog_source_id, analog_variable_id, lut_source_id, lut_variable_id)


    def get_adj_vars_info(self, start_id: int = 0) -> tuple[AdjustableVariableInfo, ...]:
        return _adjvars.get_adj_vars_info(self, start_id)


    def format_adj_vars(self, variables: Sequence[AdjustableVariable | AdjustableVariableFloat]) -> str:
        return _adjvars.format_adj_vars(variables)


    def format_adj_vars_info(self, variables: Sequence[AdjustableVariableInfo] | None = None) -> str:
        return _adjvars.format_adj_vars_info(self.get_adj_vars_info() if variables is None else variables)


    def format_adj_vars_config(self, config: AdjustableVariablesConfig | None = None) -> str:
        return _adjvars.format_adj_vars_config(self.read_adj_vars_config() if config is None else config)


    def format_adj_vars_state(self, state: AdjustableVariablesState) -> str:
        return _adjvars.format_adj_vars_state(state)


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


    def format_angles(self, angles: Angles | None = None) -> str:
        return _realtime.format_angles(self.get_angles() if angles is None else angles)


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


    def format_realtime_data(self, data: RealtimeData3 | RealtimeData4 | None = None) -> str:
        return _realtime.format_realtime_data(self.get_realtime_data() if data is None else data)


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


    def format_control_quat_status(self, status: ControlQuatStatus) -> str:
        return _realtime.format_control_quat_status(status)


    # SERVICE MODULE
    def motors_on(self) -> None:
        _service.motors_on(self)


    def tune_auto_pid(self, config: AutoPidConfig, *, need_confirmation: bool = False,) -> CommandConfirmation | None:
        """Start legacy automatic PID tuning (firmware before 2.73)."""
        return _service.tune_auto_pid(self, config, need_confirmation=need_confirmation)


    def break_auto_pid(self, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """Stop legacy automatic PID tuning."""
        return _service.break_auto_pid(self, need_confirmation=need_confirmation)


    def tune_auto_pid2(self, config: AutoPid2Config, *, need_confirmation: bool = False,) -> CommandConfirmation | None:
        """Start AutoPID2; optionally wait for its completion confirmation."""
        return _service.tune_auto_pid2(self, config, need_confirmation=need_confirmation,)


    def read_auto_pid_state(self) -> AutoPidState:
        """Read the latest automatic PID progress packet."""
        return _service.read_auto_pid_state(self)


    def format_auto_pid_state(self, state: AutoPidState | None = None) -> str:
        """Return a GUI-scale table of the latest, or supplied, PID state."""
        return _service.format_auto_pid_state(self.read_auto_pid_state() if state is None else state)


    def read_profile_pid_values(self, profile_id: int = 0xFF) -> PidValues:
        """Read the stored P/I/D values from one profile (active by default)."""
        return _service.read_profile_pid_values(self, profile_id)


    def format_profile_pid_values(self, values: PidValues | None = None) -> str:
        """Return stored AutoPID2 values in the GUI scale."""
        return _service.format_profile_pid_values(self.read_profile_pid_values() if values is None else values)


    def synchronize_motors(self, config: SyncMotorsConfig, *, need_confirmation: bool = False,) -> CommandConfirmation | None:
        """Synchronize parallel motors. This command can move the gimbal."""
        return _service.synchronize_motors(self, config, need_confirmation=need_confirmation)


    def request_one_external_motor_state(self, motor_id: int, data_set: int, result_size: int) -> bytes:
        """Request raw EXT_MOTORS_STATE data for one motor."""
        return _service.request_motor_state(self, motor_id, data_set, result_size)


    def read_any_external_motors_state(self, result_size: int) -> bytes:
        """Read a queued raw EXT_MOTORS_STATE payload."""
        return _service.read_motor_state(self, result_size)


    def enter_boot_mode(self, *, extended: bool = True, need_confirmation: bool = False, delay_ms: int = 0,) -> None:
        """Enter the bootloader; no further SerialAPI communication is allowed afterwards."""
        _service.enter_boot_mode(self, extended=extended, need_confirmation=need_confirmation, delay_ms=delay_ms,)
    

    def read_state_vars(self) -> StateVars:
        """Read persistent maintenance and cumulative state counters."""
        return _service.read_state_vars(self)

    def format_state_vars(self, state: StateVars | None = None) -> str:
        return _service.format_state_vars(self.read_state_vars() if state is None else state)


    def write_state_vars(self, state: StateVars, *, need_confirmation: bool = False,) -> CommandConfirmation | None:
        """Write persistent state counters; this changes controller memory."""
        return _service.write_state_vars(self, state, need_confirmation=need_confirmation)


    def set_debug_port(self, action: int, filter: int = 0, *, need_confirmation: bool = False,) -> CommandConfirmation | None:
        """Start or stop mirroring packets from other Serial API ports to this connection."""
        return _service.set_debug_port(self, action, filter, need_confirmation=need_confirmation)


    def read_debug_port(self) -> DebugPortPacket:
        """Read one mirrored packet with its exact payload length."""
        return _service.read_debug_port(self)


    def motors_off(self, mode: MotorsOffMode = MotorsOffMode.SAFE_STOP) -> None:
        """Turns off gimbal motors with the selected stop mode."""
        _service.motors_off(self, mode)

    def beep(
        self,
        mode: BeeperMode = BeeperMode.CONFIRM, *,
        note_length: int = 0,
        decay_factor: int = 0,
        notes_hz: tuple[int, ...] = (),
    ) -> None:
        """ Plays a standard beeper signal or a custom motor melody. """
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


    def execute_menu(self, menu_command: MenuCommands, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """ Executes one supported action. """
        return _service.execute_menu(self, menu_command, need_confirmation=need_confirmation)


    def execute_menu_ext(
        self,
        menu_command: MenuCommands | int,
        *,
        confirm_on_start: bool = False,
        confirm_on_finish: bool = False,
    ) -> MenuExecutionResult:
        return _service.execute_menu_ext(
            self,
            menu_command,
            confirm_on_start=confirm_on_start,
            confirm_on_finish=confirm_on_finish,
        )


    def set_trigger_pin(
        self,
        pin: TriggerPin | int,
        state: TriggerPinState | int,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        return _service.set_trigger_pin(
            self,
            pin,
            state,
            need_confirmation=need_confirmation,
        )


    def set_servo_out(self, values: tuple[int, int, int, int]) -> None:
        _service.set_servo_out(self, values)


    def set_servo_out_ext(self, outputs: dict[ServoOutput | int, int]) -> None:
        _service.set_servo_out_ext(self, outputs)


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

    def format_board_info(self, info: BoardInfo | None = None) -> str:
        return _service.format_board_info(self.get_board_info() if info is None else info)


    def get_board_info_3(self) -> BoardInfo3:
        """ @brief  Reads additional board information.

            @code   board3 = SimpleBGC.get_board_info_3()

                    print(f"Device ID: {board3.device_id.hex().upper()}")
                    print(f"EEPROM size: {board3.eeprom_size} bytes")
        """
        return _service.get_board_info_3(self)

    def format_board_info_3(self, info: BoardInfo3 | None = None) -> str:
        return _service.format_board_info_3(self.get_board_info_3() if info is None else info)


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


    def request_module_list(self, max_devices: int = 13,) -> tuple[CanModuleInfo, ...]:
        return _service.request_module_list(self, max_devices)

    def format_can_module_list(self, modules: tuple[CanModuleInfo, ...] | None = None) -> str:
        return _service.format_can_module_list(self.request_module_list() if modules is None else modules)


    def scan_can_device(self,) -> CanDeviceScan:
        return _service.scan_can_device(self,)


    def sign_message(self, sign_type: int, message: bytes,) -> bytes:
        return _service.sign_message(self, sign_type, message)


    def send_transparent_command(self, target: int, payload: bytes) -> None:
        """Forward raw data to a target device serial port through CAN."""
        _service.send_transparent_command(self, target, payload)


    def read_transparent_command(self, max_payload_size: int = 254) -> tuple[int, bytes]:
        """Wait for a transparent packet and return its ``(target, payload)``."""
        return _service.read_transparent_command(self, max_payload_size)


    # Transpot finctions 
    def get_last_serial_status(self) -> int:
        self._ensure_open()
        return self._native.get_last_serial_status(self._device)


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
