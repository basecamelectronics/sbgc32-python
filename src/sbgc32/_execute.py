"""Standalone command-dispatch entry point."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .commands import Command, ResponseCommand
from .types import SelectImuAction

if TYPE_CHECKING:
    from .device import SimpleBGC


def execute(gimbal: SimpleBGC, command: Command | int, **kwargs: object) -> object:
    """Execute a SerialAPI command through an open controller connection.

    ``execute`` needs a :class:`SimpleBGC` instance because the connection,
    transport and controller state belong to that object.
    """
    if isinstance(command, ResponseCommand):
        raise ValueError(f"{command.name} is sent by the board and cannot be executed.")
    command = Command(command)

    reads = {
        Command.CMD_GET_ANGLES: gimbal.get_angles,
        Command.CMD_GET_ANGLES_EXT: gimbal.get_angles_ext,
        Command.CMD_REALTIME_DATA: gimbal.get_realtime_data,
        Command.CMD_REALTIME_DATA_3: gimbal.get_realtime_data_3,
        Command.CMD_REALTIME_DATA_4: gimbal.get_realtime_data_4,
        Command.CMD_BOARD_INFO: gimbal.get_board_info,
        Command.CMD_BOARD_INFO_3: gimbal.get_board_info_3,
        Command.CMD_MOTORS_ON: gimbal.motors_on,
    }

    if command in reads:
        if kwargs:
            raise TypeError(f"{command.name} does not accept keyword arguments: {', '.join(kwargs)}")
        return reads[command]()

    if command is Command.CMD_REALTIME_DATA_CUSTOM:
        flags = gimbal._required_argument(command, kwargs, "flags")
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.get_realtime_data_custom(flags)

    if command is Command.CMD_CONTROL_QUAT_STATUS:
        flags = gimbal._required_argument(command, kwargs, "flags")
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.get_control_quat_status(flags)

    if command is Command.CMD_SELECT_IMU_3:
        imu_type = gimbal._required_argument(command, kwargs, "imu_type")
        action = kwargs.pop("action", SelectImuAction.SIMPLE_SELECT)
        time_ms = kwargs.pop("time_ms", 0)
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.select_imu_3(
            imu_type,
            action,
            time_ms,
            need_confirmation=need_confirmation,
        )

    if command is Command.CMD_GET_ADJ_VARS_VAL:
        ids = gimbal._required_argument(command, kwargs, "ids")
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.get_adj_vars(ids)

    if command is Command.CMD_SET_ADJ_VARS_VAL:
        variables = gimbal._required_argument(command, kwargs, "variables")
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.set_adj_vars(variables, need_confirmation=need_confirmation)

    if command is Command.CMD_SAVE_PARAMS_3:
        ids = kwargs.pop("ids", None)
        all_active = kwargs.pop("all_active", False)
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        if all_active:
            if ids is not None:
                raise TypeError("CMD_SAVE_PARAMS_3 accepts either ids=... or all_active=True")
            return gimbal.save_all_adj_vars(need_confirmation=need_confirmation)
        if ids is None:
            raise TypeError("CMD_SAVE_PARAMS_3 requires ids=(...) or all_active=True")
        return gimbal.save_adj_vars(ids, need_confirmation=need_confirmation)

    if command is Command.CMD_GET_ADJ_VARS_VAL_F:
        ids = gimbal._required_argument(command, kwargs, "ids")
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.get_adj_vars_float(ids)

    if command is Command.CMD_SET_ADJ_VARS_VAL_F:
        variables = gimbal._required_argument(command, kwargs, "variables")
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.set_adj_vars_float(variables, need_confirmation=need_confirmation)

    if command is Command.CMD_READ_ADJ_VARS_CFG:
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.read_adj_vars_config()

    if command is Command.CMD_WRITE_ADJ_VARS_CFG:
        config = gimbal._required_argument(command, kwargs, "config")
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.write_adj_vars_config(config, need_confirmation=need_confirmation)

    if command is Command.CMD_ADJ_VARS_STATE:
        selectors = tuple(gimbal._required_argument(command, kwargs, name) for name in (
            "trigger_slot", "analog_source_id", "analog_variable_id", "lut_source_id", "lut_variable_id"
        ))
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.get_adj_vars_state(*selectors)

    if command is Command.CMD_ADJ_VARS_INFO:
        start_id = kwargs.pop("start_id", 0)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.get_adj_vars_info(start_id)

    if command is Command.CMD_READ_PARAMS_3:
        profile_id = kwargs.pop("profile_id", 0xFF)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.read_profile_pid_values(profile_id)

    if command is Command.CMD_READ_RC_INPUTS:
        sources = gimbal._required_argument(command, kwargs, "sources")
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.read_rc_inputs(sources)

    if command is Command.CMD_DATA_STREAM_INTERVAL:
        config = gimbal._required_argument(command, kwargs, "config")
        start = kwargs.pop("start", True)
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return (
            gimbal.start_data_stream(config, need_confirmation=need_confirmation)
            if start else gimbal.stop_data_stream(config, need_confirmation=need_confirmation)
        )

    if command is Command.CMD_DEBUG_VARS_INFO_3:
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.request_debug_var_info_3()

    if command is Command.CMD_DEBUG_VARS_3:
        variables = gimbal._required_argument(command, kwargs, "variables")
        selected_indexes = kwargs.pop("selected_indexes", None)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.request_debug_var_values_3(variables, selected_indexes)

    if command is Command.CMD_READ_STATE_VARS:
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.read_state_vars()

    if command is Command.CMD_WRITE_STATE_VARS:
        state = gimbal._required_argument(command, kwargs, "state")
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.write_state_vars(state, need_confirmation=need_confirmation)

    if command is Command.CMD_SCRIPT_DEBUG:
        timeout = kwargs.pop("timeout", 1.0)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.read_script_debug_info(timeout)

    if command is Command.CMD_MODULE_LIST:
        max_devices = kwargs.pop("max_devices", 13)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.request_module_list(max_devices)

    if command is Command.CMD_CAN_DEVICE_SCAN:
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.scan_can_device()

    if command is Command.CMD_SIGN_MESSAGE:
        sign_type = gimbal._required_argument(command, kwargs, "sign_type")
        message = gimbal._required_argument(command, kwargs, "message")
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.sign_message(sign_type, message)

    if command is Command.CMD_TRANSPARENT_SAPI:
        target = kwargs.pop("target", None)
        payload = kwargs.pop("payload", None)
        max_payload_size = kwargs.pop("max_payload_size", 254)
        gimbal._reject_remaining_arguments(command, kwargs)
        if target is None and payload is None:
            return gimbal.read_transparent_command(max_payload_size)
        if target is None or payload is None:
            raise TypeError("CMD_TRANSPARENT_SAPI requires target=... and payload=..., or neither to read")
        return gimbal.send_transparent_command(target, payload)

    if command is Command.CMD_EXT_MOTORS_STATE:
        motor_id = kwargs.pop("motor_id", None)
        result_size = gimbal._required_argument(command, kwargs, "result_size")
        if motor_id is None:
            gimbal._reject_remaining_arguments(command, kwargs)
            return gimbal.read_any_external_motors_state(result_size)
        data_set = gimbal._required_argument(command, kwargs, "data_set")
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.request_one_external_motor_state(motor_id, data_set, result_size)

    if command is Command.CMD_AUTO_PID:
        config = kwargs.pop("config", None)
        need_confirmation = kwargs.pop("need_confirmation", False)
        read_state = kwargs.pop("read_state", config is None)
        gimbal._reject_remaining_arguments(command, kwargs)
        if config is None:
            if not read_state:
                return gimbal.break_auto_pid(need_confirmation=need_confirmation)
            return gimbal.read_auto_pid_state()
        return gimbal.tune_auto_pid(config, need_confirmation=need_confirmation)

    if command is Command.CMD_AUTO_PID2:
        config = gimbal._required_argument(command, kwargs, "config")
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.tune_auto_pid2(config, need_confirmation=need_confirmation)

    if command is Command.CMD_SYNC_MOTORS:
        config = gimbal._required_argument(command, kwargs, "config")
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.synchronize_motors(config, need_confirmation=need_confirmation)

    if command is Command.CMD_BOOT_MODE_3:
        extended = kwargs.pop("extended", True)
        need_confirmation = kwargs.pop("need_confirmation", False)
        delay_ms = kwargs.pop("delay_ms", 0)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.enter_boot_mode(
            extended=extended, need_confirmation=need_confirmation, delay_ms=delay_ms
        )

    if command is Command.CMD_RESET:
        delay_ms = kwargs.pop("delay_ms", 100)
        need_confirmation = kwargs.pop("need_confirmation", True)
        restore_state = kwargs.pop("restore_state", False)
        confirmation_timeout = kwargs.pop("confirmation_timeout", 2.0)
        startup_delay = kwargs.pop("startup_delay", 5.0)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.reset(
            delay_ms=delay_ms,
            need_confirmation=need_confirmation,
            restore_state=restore_state,
            confirmation_timeout=confirmation_timeout,
            startup_delay=startup_delay,
        )

    if command is Command.CMD_SET_DEBUG_PORT:
        action = gimbal._required_argument(command, kwargs, "action")
        filter = kwargs.pop("filter", 0)
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.set_debug_port(action, filter, need_confirmation=need_confirmation)

    if command is Command.CMD_TRIGGER_PIN:
        pin = gimbal._required_argument(command, kwargs, "pin")
        state = gimbal._required_argument(command, kwargs, "state")
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.set_trigger_pin(pin, state, need_confirmation=need_confirmation)

    if command is Command.CMD_SERVO_OUT:
        values = gimbal._required_argument(command, kwargs, "values")
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.set_servo_out(values)

    if command is Command.CMD_SERVO_OUT_EXT:
        outputs = gimbal._required_argument(command, kwargs, "outputs")
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.set_servo_out_ext(outputs)

    actions = {
        Command.CMD_RUN_SCRIPT: gimbal.run_script,
        Command.CMD_MOTORS_OFF: gimbal.motors_off,
        Command.CMD_BEEP_SOUND: gimbal.beep,
    }
    if command in actions:
        if command is Command.CMD_RUN_SCRIPT and kwargs.pop("stop", False):
            slot = kwargs.pop("slot", 1)
            gimbal._reject_remaining_arguments(command, kwargs)
            return gimbal.stop_script(slot)
        return actions[command](**kwargs)

    if command is Command.CMD_EXECUTE_MENU:
        menu_command = gimbal._required_argument(command, kwargs, "menu_command")
        confirm_on_start = kwargs.pop("confirm_on_start", None)
        confirm_on_finish = kwargs.pop("confirm_on_finish", None)
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        if confirm_on_start is not None or confirm_on_finish is not None:
            if need_confirmation:
                raise TypeError("CMD_EXECUTE_MENU accepts need_confirmation=... or extended confirmation flags")
            return gimbal.execute_menu_ext(
                menu_command,
                confirm_on_start=False if confirm_on_start is None else confirm_on_start,
                confirm_on_finish=False if confirm_on_finish is None else confirm_on_finish,
            )
        return gimbal.execute_menu(menu_command, need_confirmation=need_confirmation)

    if command is Command.CMD_CONTROL:
        axes = gimbal._required_argument(command, kwargs, "axes")
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.control(axes, need_confirmation=need_confirmation)

    if command is Command.CMD_CONTROL_CONFIG:
        config = kwargs.pop("config", None)
        confirm_control = kwargs.pop("confirm_control", None)
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.configure_control(
            config,
            confirm_control=confirm_control,
            need_confirmation=need_confirmation,
        )

    if command is Command.CMD_CONTROL_EXT:
        control = gimbal._required_argument(command, kwargs, "control")
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.control_ext(control)

    if command is Command.CMD_CONTROL_QUAT:
        control = gimbal._required_argument(command, kwargs, "control")
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.control_quat(control, need_confirmation=need_confirmation)

    if command is Command.CMD_CONTROL_QUAT_CONFIG:
        config = gimbal._required_argument(command, kwargs, "config")
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.configure_control_quat(config, need_confirmation=need_confirmation)

    if command is Command.CMD_EXT_MOTORS_ACTION:
        motors = gimbal._required_argument(command, kwargs, "motors")
        action = gimbal._required_argument(command, kwargs, "action")
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.ext_motors_action(motors, action, need_confirmation=need_confirmation)

    if command is Command.CMD_EXT_MOTORS_CONTROL:
        control = gimbal._required_argument(command, kwargs, "control")
        motors = gimbal._required_argument(command, kwargs, "motors")
        data_set = kwargs.pop("data_set", 0)
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.control_ext_motors(control, motors, data_set, need_confirmation=need_confirmation)

    if command is Command.CMD_EXT_MOTORS_CONTROL_CONFIG:
        config = gimbal._required_argument(command, kwargs, "config")
        need_confirmation = kwargs.pop("need_confirmation", False)
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.configure_ext_motors(config, need_confirmation=need_confirmation)

    if command is Command.CMD_API_VIRT_CH_CONTROL:
        values = gimbal._required_argument(command, kwargs, "values")
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.set_api_virtual_channels(values)

    if command is Command.CMD_API_VIRT_CH_HIGH_RES:
        values = gimbal._required_argument(command, kwargs, "values")
        gimbal._reject_remaining_arguments(command, kwargs)
        return gimbal.set_api_virtual_channels_hr(values)

    raise NotImplementedError(f"Command {command.name} is not implemented")
