Service API reference
=====================

:doc:`Service guide <../service>`

All methods below belong to an open ``SimpleBGC`` instance. Commands that move
motors, change persistent state, run scripts, or enter boot mode should only
be used when their firmware behaviour is understood.

Controller and PID
------------------

.. list-table::
   :header-rows: 1
   :widths: 32 42 26

   * - Method
     - Parameters
     - Result
   * - ``g.get_board_info()`` / ``g.get_board_info_3()``
     - No parameters.
     - :class:`~sbgc32.BoardInfo` or :class:`~sbgc32.BoardInfo3`.
   * - ``g.tune_auto_pid(config, *, need_confirmation=False)``
     - ``config`` — :class:`~sbgc32.AutoPidConfig`; legacy API (before 2.73).
     - Confirmation or ``None``.
   * - ``g.break_auto_pid(*, need_confirmation=False)``
     - No parameters.
     - Confirmation or ``None``.
   * - ``g.read_auto_pid_state()``
     - No parameters.
     - :class:`~sbgc32.AutoPidState`.
   * - ``g.tune_auto_pid2(config, *, need_confirmation=False)``
     - ``config`` — :class:`~sbgc32.AutoPid2Config`.
     - Confirmation or ``None``.
   * - ``g.read_profile_pid_values(profile_id=0xFF)``
     - Profile ID; ``0xFF`` selects the active profile.
     - :class:`~sbgc32.PidValues`.
   * - ``g.synchronize_motors(config, *, need_confirmation=False)``
     - ``config`` — :class:`~sbgc32.SyncMotorsConfig`.
     - Confirmation or ``None``.

Motors, menu, scripts, and reset
--------------------------------

.. list-table::
   :header-rows: 1
   :widths: 32 42 26

   * - Method
     - Parameters
     - Result
   * - ``g.motors_on()`` / ``g.motors_off(mode=MotorsOffMode.SAFE_STOP)``
     - Optional :class:`~sbgc32.MotorsOffMode`.
     - ``None``.
   * - ``g.beep(...)`` / ``g.play_beeper(...)``
     - Standard signal or custom motor melody parameters.
     - ``None``.
   * - ``g.execute_menu(menu_command, *, need_confirmation=False)``
     - :class:`~sbgc32.MenuCommands` member.
     - Confirmation or ``None``.
   * - ``g.execute_menu_ext(menu_command, *, confirm_on_start=False, confirm_on_finish=False)``
     - Menu command and optional start/finish confirmations.
     - :class:`~sbgc32.MenuExecutionResult`.
   * - ``g.run_script(slot=1, *, debug=False)`` / ``g.stop_script(slot=1)``
     - Script slot; ``debug=True`` enables debug output.
     - ``None``.
   * - ``g.read_script_debug_info(timeout=1.0)``
     - Read timeout in seconds.
     - :class:`~sbgc32.ScriptDebugInfo`.
   * - ``g.reset(...)`` / ``g.enter_boot_mode(...)``
     - Reset or bootloader options defined by firmware.
     - ``None``; boot mode closes normal API access.

State, outputs, and CAN
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 32 42 26

   * - Method
     - Parameters
     - Result
   * - ``g.read_state_vars()`` / ``g.write_state_vars(state, *, need_confirmation=False)``
     - No parameters to read; :class:`~sbgc32.StateVars` to write.
     - State value, confirmation, or ``None``.
   * - ``g.set_debug_port(action, filter=0, *, need_confirmation=False)``
     - Debug action and firmware packet filter.
     - Confirmation or ``None``.
   * - ``g.read_debug_port()``
     - No parameters.
     - :class:`~sbgc32.DebugPortPacket`.
   * - ``g.set_trigger_pin(pin, state, *, need_confirmation=False)``
     - Output pin and desired state.
     - Confirmation or ``None``.
   * - ``g.set_servo_out(values)`` / ``g.set_servo_out_ext(outputs)``
     - Basic servo values or selected extended outputs.
     - ``None``.
   * - ``g.request_module_list(max_devices=13)`` / ``g.scan_can_device()``
     - Maximum module count or no parameters.
     - :class:`~sbgc32.CanModuleInfo` list or :class:`~sbgc32.CanDeviceScan`.
   * - ``g.send_transparent_command(target, payload)`` / ``g.read_transparent_command(max_payload_size=254)``
     - CAN target and raw payload; maximum expected payload for reads.
     - Raw response payload.
   * - ``g.request_one_external_motor_state(motor_id, data_set, result_size)`` / ``g.read_any_external_motors_state(result_size)``
     - Motor/data-set selection and expected payload size.
     - Raw external-motor state payload.

Formatters
----------

``format_board_info``, ``format_board_info_3``, ``format_state_vars``,
``format_auto_pid_state``, ``format_profile_pid_values``, and
``format_can_module_list`` return text tables. Pass a cached result to avoid
another controller request; otherwise use their optional argument as ``None``.

Public data types
-----------------

.. toctree::
   :maxdepth: 1

   service-types
