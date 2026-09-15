Service and maintenance commands
================================

The service module exposes board information, motor control, Auto PID,
maintenance state, scripts, menu actions, auxiliary outputs, CAN and
transparent SerialAPI commands. Read operations return the named decoded value;
actions return ``None`` or a requested confirmation.

.. autofunction:: sbgc32.modules.service.get_board_info
.. autofunction:: sbgc32.modules.service.get_board_info_3
.. autofunction:: sbgc32.modules.service.tune_auto_pid
.. autofunction:: sbgc32.modules.service.break_auto_pid
.. autofunction:: sbgc32.modules.service.tune_auto_pid2
.. autofunction:: sbgc32.modules.service.read_auto_pid_state
.. autofunction:: sbgc32.modules.service.read_profile_pid_values
.. autofunction:: sbgc32.modules.service.motors_on
.. autofunction:: sbgc32.modules.service.motors_off
.. autofunction:: sbgc32.modules.service.synchronize_motors
.. autofunction:: sbgc32.modules.service.request_motor_state
.. autofunction:: sbgc32.modules.service.read_motor_state
.. autofunction:: sbgc32.modules.service.enter_boot_mode
.. autofunction:: sbgc32.modules.service.read_state_vars
.. autofunction:: sbgc32.modules.service.write_state_vars
.. autofunction:: sbgc32.modules.service.set_debug_port
.. autofunction:: sbgc32.modules.service.read_debug_port
.. autofunction:: sbgc32.modules.service.set_servo_out
.. autofunction:: sbgc32.modules.service.set_servo_out_ext
.. autofunction:: sbgc32.modules.service.run_script
.. autofunction:: sbgc32.modules.service.stop_script
.. autofunction:: sbgc32.modules.service.read_script_debug_info
.. autofunction:: sbgc32.modules.service.reset
.. autofunction:: sbgc32.modules.service.set_trigger_pin
.. autofunction:: sbgc32.modules.service.execute_menu
.. autofunction:: sbgc32.modules.service.execute_menu_ext
.. autofunction:: sbgc32.modules.service.beep
.. autofunction:: sbgc32.modules.service.play_beeper
.. autofunction:: sbgc32.modules.service.sign_message
.. autofunction:: sbgc32.modules.service.scan_can_device
.. autofunction:: sbgc32.modules.service.request_module_list
.. autofunction:: sbgc32.modules.service.send_transparent_command
.. autofunction:: sbgc32.modules.service.read_transparent_command
