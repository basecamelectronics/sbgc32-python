Execute and formatting API reference
====================================

:doc:`Execute and formatting guide <../execute-formatting>`

Generic dispatch
----------------

.. list-table::
   :header-rows: 1
   :widths: 32 42 26

   * - Function
     - Parameters
     - Result
   * - ``execute(gimbal, command, **kwargs)``
     - Open ``SimpleBGC`` instance, a supported :class:`~sbgc32.Command`, and
       exactly the keyword arguments of the matching typed method.
     - The matching typed-method result. Unsupported commands raise
       ``NotImplementedError``.

``ResponseCommand`` values identify controller responses; they cannot be sent
through ``execute``. See the guide for the command-to-method mapping.

Formatter methods
-----------------

All formatters return ``str``. Except for ``print_debug_var_info_3``, they do
not write to stdout.

.. list-table::
   :header-rows: 1
   :widths: 32 42 26

   * - Method
     - Parameters
     - Result
   * - ``g.format_angles(angles=None)``
     - :class:`~sbgc32.Angles`; omit it to read current angles.
     - Text table.
   * - ``g.format_realtime_data(data=None)``
     - A realtime data structure; omit it to request ``REALTIME_DATA_3``.
     - Text table.
   * - ``g.format_control_quat_status(status)``
     - Quaternion-control status result.
     - Text table.
   * - ``g.format_debug_var_info_3(variables)`` / ``g.print_debug_var_info_3(variables)``
     - Debug-variable metadata.
     - Formatted text / prints it.
   * - ``g.format_adj_vars(variables)`` / ``g.format_adj_vars_state(state)``
     - Read adjustable-variable values or runtime state.
     - Text table.
   * - ``g.format_adj_vars_info(variables=None)`` / ``g.format_adj_vars_config(config=None)``
     - Supplied metadata/configuration; omit it to request fresh data.
     - Text table.
   * - ``g.format_auto_pid_state(state=None)`` / ``g.format_profile_pid_values(values=None)``
     - Supplied PID data; omit it to request fresh data.
     - Text table.
   * - ``g.format_board_info(info=None)`` / ``g.format_board_info_3(info=None)``
     - Supplied board information; omit it to request fresh data.
     - Text table.
   * - ``g.format_state_vars(state=None)`` / ``g.format_can_module_list(modules=None)``
     - Supplied state/modules; omit them to request fresh data.
     - Text table.

Public data types
-----------------

.. toctree::
   :maxdepth: 1

   execute-formatting-types
