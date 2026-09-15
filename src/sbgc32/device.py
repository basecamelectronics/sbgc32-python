"""Public asynchronous connection object."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future
from types import ModuleType
from typing import Any, ClassVar

from . import types as value_types
from .dispatcher import Decoder, MessageDispatcher, ResponseKey
from .format import Formatter
from .modules import adjvars, calib, eeprom, imu, profiles, realtime, service
from .modules import control as control_module
from .protocol import ProtocolCodec
from .pyserial import PySerialTransport
from .workers import DEFAULT_WORKER_ROUTES, WorkerManager, WorkerRoute

__all__ = ["SimpleBGC"]


class SimpleBGC:
    """Open a Serial API connection to a SimpleBGC controller.

    Args:
        port: System serial-port name, for example ``"COM4"``.
        baudrate: Serial-port speed in bits per second.
        protocol_version: Version of protocol, ``1`` or ``2``.
        write_timeout: Maximum duration of one serial write, or ``None`` to
            wait indefinitely.

    Raises:
        OSError: If the serial port cannot be opened.
    """

    #: Stateless text-formatting helpers, available as ``gimbal.format``.
    format: ClassVar[Formatter] = Formatter()
    #: All public value classes and enums, available as ``gimbal.types``.
    types: ClassVar[ModuleType] = value_types

    def __init__(
        self,
        port: str,
        *,
        baudrate: int = 115200,
        protocol_version: int = 2,
        write_timeout: float | None = 1.0,
        worker_routes: tuple[WorkerRoute, ...] = DEFAULT_WORKER_ROUTES,
        serial_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._closed = False
        self._dispatcher = MessageDispatcher()
        self._workers = WorkerManager(
            self._dispatcher.completion_queue,
            worker_routes,
        )
        self._codec = ProtocolCodec(protocol_version=protocol_version)
        self._transport = PySerialTransport(
            self._dispatcher,
            self._codec,
            port=port,
            baudrate=baudrate,
            write_timeout=write_timeout,
            serial_factory=serial_factory,
        )

        self._dispatcher.start()
        self._workers.start()

        try:
            self._transport.start()
        except BaseException:
            self._dispatcher.stop().result(timeout=1)
            self._dispatcher.join(timeout=1)
            self._workers.join(timeout=1)
            raise

    @property
    def transport_error(self) -> BaseException | None:
        """The physical port error that stopped the connection, if any."""

        return self._transport.fatal_error

    # TRANSPORT MODULE
    def request_raw(
        self,
        command_id: int,
        payload: bytes = b"",
        *,
        response_command_id: int | None = None,
        response_key: ResponseKey | None = None,
        timeout: float | None = 1.0,
        route: str = "general",
        decoder: Decoder | None = None,
    ) -> Future[Any]:
        """Send one command and return its result Future without blocking.

        ``decoder`` receives a validated :class:`WireFrame` in a worker thread.
        Without a decoder, the Future result is the ``WireFrame`` itself.
        """

        self._ensure_open()
        return self._dispatcher.request(
            command_id,
            payload,
            response_command_id=response_command_id,
            response_key=response_key,
            timeout=timeout,
            route=route,
            decoder=decoder,
        )

    def send_raw(
        self,
        command_id: int,
        payload: bytes = b"",
        *,
        route: str = "general",
    ) -> Future[None]:
        """Queue a command that has no protocol response.

        Its Future completes once the TX thread has successfully handed the
        frame to the serial transport; it never waits for an RX frame.
        """

        self._ensure_open()
        return self._dispatcher.send(command_id, payload, route=route)

    def receive_unsolicited_raw(
        self,
        command_id: int,
        *,
        timeout: float | None = 1.0,
        route: str = "general",
        decoder: Decoder | None = None,
    ) -> Future[Any]:
        """Wait asynchronously for the next unmatched command frame."""

        self._ensure_open()
        return self._dispatcher.receive_unsolicited(
            command_id, timeout=timeout, route=route, decoder=decoder
        )

    def close(self, timeout: float | None = 2.0) -> None:
        """Close the COM port and wait for internal threads to finish."""

        if self._closed:
            return

        self._closed = True
        self._transport.stop().result(timeout=timeout)
        self._transport.join(timeout=timeout)
        self._dispatcher.join(timeout=timeout)
        self._workers.join(timeout=timeout)

    def __enter__(self) -> "SimpleBGC":
        self._ensure_open()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise ConnectionError("The SimpleBGC connection is closed")

    # REALTIME MODULE
    get_angles = realtime.get_angles
    get_angles_ext = realtime.get_angles_ext
    get_realtime_data = realtime.get_realtime_data
    get_realtime_data_3 = realtime.get_realtime_data_3
    get_realtime_data_4 = realtime.get_realtime_data_4
    get_realtime_data_custom = realtime.get_realtime_data_custom
    read_rc_inputs = realtime.read_rc_inputs
    get_control_quat_status = realtime.get_control_quat_status
    start_data_stream = realtime.start_data_stream
    stop_data_stream = realtime.stop_data_stream
    read_data_stream = realtime.read_data_stream
    request_debug_var_info_3 = realtime.request_debug_var_info_3
    request_debug_var_values_3 = realtime.request_debug_var_values_3
    select_imu_3 = realtime.select_imu_3

    # EERPROM MODULE
    read_i2c_register = eeprom.read_i2c_register
    write_i2c_register = eeprom.write_i2c_register
    read_eeprom = eeprom.read_eeprom
    write_eeprom = eeprom.write_eeprom
    read_external_data = eeprom.read_external_data
    write_external_data = eeprom.write_external_data
    read_file = eeprom.read_file
    write_file = eeprom.write_file
    clear_file_system = eeprom.clear_file_system

    # IMU MODULE
    request_ext_imu_debug = imu.request_ext_imu_debug
    send_ext_imu_command = imu.send_ext_imu_command
    send_ext_sens_command = imu.send_ext_sens_command
    get_ahrs_helper = imu.get_ahrs_helper
    set_ahrs_helper = imu.set_ahrs_helper
    correction_gyro = imu.correction_gyro
    provide_helper_data = imu.provide_helper_data
    provide_helper_data_ext = imu.provide_helper_data_ext

    # ADJVARS MODULE
    get_adj_vars = adjvars.get_adj_vars
    get_adj_var = adjvars.get_adj_var
    set_adj_vars = adjvars.set_adj_vars
    set_adj_var = adjvars.set_adj_var
    save_adj_vars = adjvars.save_adj_vars
    save_all_adj_vars = adjvars.save_all_adj_vars
    get_adj_vars_float = adjvars.get_adj_vars_float
    get_adj_var_float = adjvars.get_adj_var_float
    set_adj_vars_float = adjvars.set_adj_vars_float
    set_adj_var_float = adjvars.set_adj_var_float
    read_adj_vars_config = adjvars.read_adj_vars_config
    write_adj_vars_config = adjvars.write_adj_vars_config
    get_adj_vars_state = adjvars.get_adj_vars_state
    get_adj_vars_info = adjvars.get_adj_vars_info

    # CALIB MODULE
    request_calib_info = calib.request_calib_info
    calib_acc = calib.calib_acc
    calib_gyro = calib.calib_gyro
    calib_mag = calib.calib_mag
    calib_poles = calib.calib_poles
    calib_offset = calib.calib_offset
    calib_encoders_fld_offset = calib.calib_encoders_fld_offset
    calib_encoders_offset = calib.calib_encoders_offset
    calib_bat = calib.calib_bat
    calib_orient_corr = calib.calib_orient_corr
    calib_acc_ext_ref = calib.calib_acc_ext_ref
    calib_cogging = calib.calib_cogging

    # CONTROL MODULE
    control = control_module.control
    configure_control = control_module.configure_control
    control_config = control_module.control_config
    set_api_virtual_channels = control_module.set_api_virtual_channels
    control_ext = control_module.control_ext
    control_quat = control_module.control_quat
    configure_control_quat = control_module.configure_control_quat
    ext_motors_action = control_module.ext_motors_action
    control_ext_motors = control_module.control_ext_motors
    configure_ext_motors = control_module.configure_ext_motors
    set_api_virtual_channels_hr = control_module.set_api_virtual_channels_hr

    # PROFILES MODULE
    read_profile_names = profiles.read_profile_names
    write_profile_names = profiles.write_profile_names
    manage_profile_set = profiles.manage_profile_set
    set_profile_writing = profiles.set_profile_writing
    read_profile_parameter_block = profiles.read_profile_parameter_block
    write_profile_parameter_block = profiles.write_profile_parameter_block
    read_params_3 = profiles.read_params_3
    read_params_ext = profiles.read_params_ext
    read_params_ext2 = profiles.read_params_ext2
    read_params_ext3 = profiles.read_params_ext3
    write_params_3 = profiles.write_params_3
    write_params_ext = profiles.write_params_ext
    write_params_ext2 = profiles.write_params_ext2
    write_params_ext3 = profiles.write_params_ext3
    read_profile_parameters = profiles.read_profile_parameters
    write_profile_parameters = profiles.write_profile_parameters
    use_profile_defaults = profiles.use_profile_defaults

    # SERVICE MODULE
    get_board_info = service.get_board_info
    get_board_info_3 = service.get_board_info_3
    tune_auto_pid = service.tune_auto_pid
    break_auto_pid = service.break_auto_pid
    tune_auto_pid2 = service.tune_auto_pid2
    read_auto_pid_state = service.read_auto_pid_state
    read_profile_pid_values = service.read_profile_pid_values
    motors_on = service.motors_on
    motors_off = service.motors_off
    synchronize_motors = service.synchronize_motors
    request_motor_state = service.request_motor_state
    read_motor_state = service.read_motor_state
    enter_boot_mode = service.enter_boot_mode
    read_state_vars = service.read_state_vars
    write_state_vars = service.write_state_vars
    set_debug_port = service.set_debug_port
    read_debug_port = service.read_debug_port
    set_servo_out = service.set_servo_out
    set_servo_out_ext = service.set_servo_out_ext
    run_script = service.run_script
    stop_script = service.stop_script
    read_script_debug_info = service.read_script_debug_info
    reset = service.reset
    set_trigger_pin = service.set_trigger_pin
    execute_menu = service.execute_menu
    execute_menu_ext = service.execute_menu_ext
    beep = service.beep
    play_beeper = service.play_beeper
    sign_message = service.sign_message
    scan_can_device = service.scan_can_device
    request_module_list = service.request_module_list
    send_transparent_command = service.send_transparent_command
    read_transparent_command = service.read_transparent_command
