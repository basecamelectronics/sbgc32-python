Command dispatch and readable output
====================================

Typed methods such as ``g.get_angles()`` and ``g.control(...)`` are the
recommended interface: their names state the intent and their annotations show
the expected request and result types. The package also supplies a generic
``execute`` function for applications that select a command dynamically.

.. seealso::

   :doc:`Execute and formatting API reference <api/execute-formatting>` gives
   the concise signatures for dispatch and all formatters.

Generic command dispatch
------------------------

Import ``execute`` from the package and pass an open ``SimpleBGC`` connection,
a ``Command`` member, and the command-specific keyword arguments. ``execute``
is a package-level function, not a ``SimpleBGC`` method.

.. code-block:: python

   from sbgc32 import Command, RealtimeDataCustomFlag as RTD, execute

   data = execute(g, Command.CMD_REALTIME_DATA_3)
   custom = execute(g, Command.CMD_REALTIME_DATA_CUSTOM, flags=RTD.RC_DATA)

It returns the same result as the corresponding typed method. Unsupported
commands raise ``NotImplementedError``. Board-originated ``ResponseCommand``
members, including ``CMD_CONFIRM`` and ``CMD_ERROR``, cannot be executed and
raise ``ValueError``.

Use ``execute`` when a command is selected from configuration, a command-line
tool, or a generic integration layer. Prefer the typed method in application
code where the command is known in advance.

Supported dispatch arguments
----------------------------

``execute`` supports the implemented command set. Important argument mappings
are:

.. list-table::
   :header-rows: 1
   :widths: 37 63

   * - Command
     - Required or optional keyword arguments
   * - ``CMD_REALTIME_DATA_CUSTOM`` / ``CMD_CONTROL_QUAT_STATUS``
     - ``flags``
   * - ``CMD_SELECT_IMU_3``
     - ``imu_type``; optional ``action``, ``time_ms``, ``need_confirmation``
   * - Integer adjustable-variable commands
     - ``ids`` or ``variables``; the save command accepts ``ids`` or
       ``all_active=True``
   * - Float adjustable-variable commands
     - ``ids`` or ``variables``
   * - Adjustable-variable configuration and state
     - ``config`` for write; five selector arguments for state;
       optional ``start_id`` for info
   * - ``CMD_CONTROL`` and ``CMD_CONTROL_CONFIG``
     - ``axes``; or optional ``config``, ``confirm_control``, and
       ``need_confirmation``
   * - Extended and quaternion control
     - The same named arguments as their corresponding ``g.*`` method
   * - Virtual API channels
     - ``values``
   * - Run script, motors off, and beep
     - The same keyword arguments as ``g.run_script``, ``g.motors_off``, or
       ``g.beep``
   * - ``CMD_EXECUTE_MENU``
     - ``menu_command`` and optional ``need_confirmation``

Read-only angle, realtime, board-information, and motors-on commands do not
accept keyword arguments.

Readable output
---------------

The ``format_*`` methods return plain text; they never call ``print``. This
makes them suitable for terminals, log files, test assertions, and a GUI text
widget.

.. code-block:: python

   print(g.format_angles())
   print(g.format_realtime_data())
   print(g.format_board_info())

When a formatter accepts an optional value and it is omitted, it requests the
current controller value first. For example, ``g.format_realtime_data()`` reads
``REALTIME_DATA_3`` and formats it, while
``g.format_realtime_data(previous_data)`` formats the supplied result without
another request.

Available formatters
--------------------

* Realtime: ``format_angles``, ``format_realtime_data``,
  ``format_control_quat_status``, and ``format_debug_var_info_3``.
* Adjustable variables: ``format_adj_vars``, ``format_adj_vars_info``,
  ``format_adj_vars_config``, and ``format_adj_vars_state``.
* Service and maintenance: ``format_board_info``, ``format_board_info_3``,
  ``format_state_vars``, ``format_auto_pid_state``,
  ``format_profile_pid_values``, and ``format_can_module_list``.

``g.print_debug_var_info_3(variables)`` is the one convenience helper that
prints immediately. Every other formatter returns a string, so use ``print``
explicitly when console output is wanted.
