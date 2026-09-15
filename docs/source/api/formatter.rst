Formatter
=========

``Formatter`` converts already decoded controller values into text tables. It
does not send commands, block, or print. Call it through either
``Formatter`` or a connection's ``format`` attribute:

.. code-block:: python

   report = gimbal.format.realtime_data(data)
   print(report)

Inputs and results
------------------

Each method returns ``str``. The ``table`` method builds a table from text
headers and rows. The remaining methods accept the decoded value indicated in
their description. They raise ``TypeError`` for an incompatible value or an
invalid required structure, such as a profile-name tuple of the wrong size.

Use the concise names below in new code. ``format_*`` aliases are retained for
compatibility with module-level formatter function names.

.. autoclass:: sbgc32.Formatter
   :members: table, angles, realtime_data, control_quat_status, debug_var_info_3, ext_imu_debug, ahrs_helper, adj_vars, adj_vars_info, adj_vars_config, adj_vars_state, calib_info, profile_names, profile_parameters, auto_pid_state, profile_pid_values, board_info, board_info_3, state_vars, can_module_list
   :show-inheritance:
