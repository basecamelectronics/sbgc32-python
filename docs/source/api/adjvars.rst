Adjustable variables API reference
==================================

:doc:`Adjustable variables guide <../adjvars>`

Methods below belong to an open ``SimpleBGC`` instance. IDs are integers in
``0..255``. Read and write calls accept one to 40 values; saving accepts up to
102 IDs.

Value methods
-------------

.. list-table::
   :header-rows: 1
   :widths: 32 42 26

   * - Method
     - Parameters
     - Result
   * - ``g.get_adj_var(id)`` / ``g.get_adj_vars(ids)``
     - One ``id`` or an iterable of IDs.
     - One or several :class:`~sbgc32.AdjustableVariable` records.
   * - ``g.set_adj_var(id, value, *, need_confirmation=False)``
     - ID and signed 32-bit integer ``value``.
     - Confirmation or ``None``.
   * - ``g.set_adj_vars(variables, *, need_confirmation=False)``
     - Iterable of :class:`~sbgc32.AdjustableVariable` records.
     - Confirmation or ``None``.
   * - ``g.get_adj_var_float(id)`` / ``g.get_adj_vars_float(ids)``
     - One ID or an iterable of IDs.
     - One or several :class:`~sbgc32.AdjustableVariableFloat` records.
   * - ``g.set_adj_var_float(id, value, *, need_confirmation=False)``
     - ID and finite floating-point ``value``.
     - Confirmation or ``None``.
   * - ``g.set_adj_vars_float(variables, *, need_confirmation=False)``
     - Iterable of :class:`~sbgc32.AdjustableVariableFloat` records.
     - Confirmation or ``None``.

Persistence and configuration
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 32 42 26

   * - Method
     - Parameters
     - Result
   * - ``g.save_adj_vars(ids, *, need_confirmation=False)``
     - Iterable of selected IDs.
     - Confirmation or ``None``.
   * - ``g.save_all_adj_vars(*, need_confirmation=False)``
     - No values; saves all active unsaved variables.
     - Confirmation or ``None``.
   * - ``g.read_adj_vars_config()``
     - No parameters.
     - :class:`~sbgc32.AdjustableVariablesConfig`.
   * - ``g.write_adj_vars_config(config, *, need_confirmation=False)``
     - ``config`` — :class:`~sbgc32.AdjustableVariablesConfig`.
     - Confirmation or ``None``.
   * - ``g.get_adj_vars_state(trigger_slot, analog_source_id, analog_variable_id, lut_source_id, lut_variable_id)``
     - Selected trigger slot and source/variable IDs for analog and LUT state.
     - :class:`~sbgc32.AdjustableVariablesState`.
   * - ``g.get_adj_vars_info(start_id=0)``
     - First ID to query.
     - :class:`~sbgc32.AdjustableVariableInfo` records.

Formatters
----------

.. list-table::
   :header-rows: 1
   :widths: 32 42 26

   * - Method
     - Parameters
     - Result
   * - ``g.format_adj_vars(variables)`` / ``g.format_adj_vars_state(state)``
     - Previously read values or runtime state.
     - Text table (``str``).
   * - ``g.format_adj_vars_info(variables=None)`` / ``g.format_adj_vars_config(config=None)``
     - A supplied result; omit it to request fresh information first.
     - Text table (``str``).

Public data types
-----------------

.. toctree::
   :maxdepth: 1

   adjvars-types
