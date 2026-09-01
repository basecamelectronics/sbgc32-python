Service and maintenance
=======================

The service API covers controller information, motors, scripts, maintenance,
automatic PID tuning, ports, and CAN helpers. Several commands alter controller
state or can cause physical movement; use them only with appropriate hardware
safety measures.

.. seealso::

   :doc:`Service API reference <api/service>` contains the complete list of
   public service and maintenance methods.

Information and status
----------------------

``g.get_board_info()`` and ``g.get_board_info_3()`` return controller and
firmware information. Their matching ``format_board_info`` methods make a
compact diagnostic table.

.. code-block:: python

   print(g.format_board_info())
   print(g.format_board_info_3())

``g.read_state_vars()`` reads persistent maintenance counters. Use
``g.format_state_vars()`` for a readable report. Writing a complete
``StateVars`` value with ``g.write_state_vars(state)`` changes persistent
controller memory.

Motors, menu actions, and signals
---------------------------------

``g.motors_on()`` starts the gimbal motors. ``g.motors_off(mode)`` stops them;
choose an explicit ``MotorsOffMode`` when the stopping behaviour matters.

``g.execute_menu(menu_command)`` runs one supported ``MenuCommands`` action.
``g.execute_menu_ext(...)`` adds optional confirmations for the start and end
of the action. ``g.beep(...)`` and its alias ``g.play_beeper(...)`` play a
standard signal or a custom motor melody.

.. warning::

   Motor, menu, calibration, and beeper commands can change controller state
   or move the gimbal. Check the current mode and keep the mechanism clear
   before running them.

Scripts and reset
-----------------

``g.run_script(slot, debug=False)`` starts a controller script and
``g.stop_script(slot)`` stops it. When a script is started with ``debug=True``,
``g.read_script_debug_info(timeout=...)`` retrieves its latest debug packet.

``g.reset(...)`` resets the controller, waits for the selected confirmation,
and recovers the communication transport. It is not an ordinary request: do
not send other commands until it returns.

``g.enter_boot_mode()`` transitions into the bootloader. No further Serial API
communication is allowed on that connection afterwards; close it and reconnect
only when the controller is ready again.

Automatic PID and synchronization
---------------------------------

``g.tune_auto_pid(config)`` and ``g.read_auto_pid_state()`` are the legacy
automatic PID interface for firmware earlier than 2.73. On newer firmware use
``g.tune_auto_pid2(config)``. ``g.format_auto_pid_state()`` and
``g.format_profile_pid_values()`` present PID data in a GUI-oriented table.

``g.synchronize_motors(config)`` aligns parallel motors for one axis and can
move the gimbal. External-motor state helpers,
``g.request_one_external_motor_state(...)`` and
``g.read_any_external_motors_state(...)``, return raw protocol payloads.

Ports, outputs, and CAN helpers
-------------------------------

* ``g.set_debug_port(action, filter=...)`` starts or stops packet mirroring;
  ``g.read_debug_port()`` reads one mirrored packet.
* ``g.set_trigger_pin(...)``, ``g.set_servo_out(...)``, and
  ``g.set_servo_out_ext(...)`` write controller outputs.
* ``g.request_module_list()`` and ``g.scan_can_device()`` inspect CAN devices;
  ``g.format_can_module_list()`` prints a module table.
* ``g.send_transparent_command(...)`` and
  ``g.read_transparent_command(...)`` tunnel raw Serial API data to a selected
  CAN target.

The raw state and transparent-command methods are deliberately not decoded
further. Interpret their payloads using the controller firmware documentation.
