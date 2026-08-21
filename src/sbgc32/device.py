from __future__ import annotations

from time import sleep

from . import _adjvars, _control, _realtime, _service
from ._serial_api_library import NativeError
from .backends import create_backend
from .commands import Command, MenuCommands, ResponseCommand
from .types import (
    AdjustableVariable,
    Angles,
    AnglesExt,
    BeeperMode,
    BoardInfo,
    BoardInfo3,
    CommandConfirmation,
    ControlAxis,
    ControlConfig,
    MotorsOffMode,
    RealtimeData3,
    RealtimeData4,
    RealtimeDataCustom,
    RealtimeDataCustomFlag,
    ScriptDebugInfo,
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
        """ @brief  Saves selected adjustable-variable values to EEPROM.

            @code   SimpleBGC.save_adj_vars((0,1,2,))

            @param  ids               - IDs of variables to persist.
                    need_confirmation - request CMD_CONFIRM from supported firmware.
        """
        return _adjvars.save_adj_vars(self, ids, need_confirmation=need_confirmation)

    def save_all_adj_vars(self, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """ @brief  Saves all active, unsaved adjustable variables to EEPROM.

            @code   SimpleBGC.save_all_adj_vars()
        """
        return _adjvars.save_all_adj_vars(self, need_confirmation=need_confirmation)

    def get_angles(self) -> Angles:
        """ @brief  Get information about the actual gimbal control state.

            @code   angles = SimpleBGC.get_angles()

                    print(f"IMU: roll={angles.imu.roll:7.2f}°, "
                          f"pitch={angles.imu.pitch:7.2f}°, "
                          f"yaw={angles.imu.yaw:7.2f}°")
        """
        return _realtime.get_angles(self)

    def get_angles_ext(self) -> AnglesExt:
        """ @brief  Get information about angles in different format.

            @code   angles = SimpleBGC.get_angles_ext()

                    roll, pitch, yaw = angles.axis_gae
                    print(roll.imu_angle)
                    print(roll.target_angle)
                    print(roll.frame_cam_angle)
        """
        return _realtime.get_angles_ext(self)

    def get_realtime_data(self) -> RealtimeData3:
        """ @brief The old name of REALTIME_DATA_3. Receives real-time data.

            @code   data = SimpleBGC.get_realtime_data()

                    print(f"Battery: {data.bat_level / 100:.2f} V")
                    print(f"System error mask: 0x{data.system_error:04X}")
        """
        return _realtime.get_realtime_data_3(self)

    def get_realtime_data_3(self) -> RealtimeData3:
        """ @brief Receives real-time data.

            @code  data = SimpleBGC.get_realtime_data_3()

                    print(f"Battery: {data.bat_level / 100:.2f} V")
                    print(f"System error mask: 0x{data.system_error:04X}")
        """
        return _realtime.get_realtime_data_3(self)

    def get_realtime_data_4(self) -> RealtimeData4:
        """ @brief Receives extended version of real-time data.

            @code  data = SimpleBGC.get_realtime_data_4()

                    print(f"IMU temperature: {data.imu_temperature} C")
                    print(f"System state flags: 0x{data.system_state_flags:08X}")
        """
        return _realtime.get_realtime_data_4(self)

    def get_realtime_data_custom(self, flags: RealtimeDataCustomFlag | int) -> RealtimeDataCustom:
        """ @brief  Requests configurable realtime data.

            @code   from sbgc32 import RealtimeDataCustomFlag as RTD
                    flags = (RTD.RC_DATA | RTD.COMM_ERRORS)

                    data = SimpleBGC.get_realtime_data_custom(flags=flags)

                    print("RC data:", data.fields[RTD.RC_DATA])
                    print("Communication errors:", data.fields[RTD.COMM_ERRORS])

            @param  flags - required data.
        """
        return _realtime.get_realtime_data_custom(self, flags)

    def motors_on(self) -> None:
        """ @brief  Turns on gimbal motors.

            @code   SimpleBGC.motors_on()
         """
        _service.motors_on(self)

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
                     print(f"Board: {board.board_version}")
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
