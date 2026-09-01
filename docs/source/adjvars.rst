Adjustable variables
====================

Adjustable variables are firmware-defined controller parameters addressed by
an ID. Their name, valid range, unit, and effect depend on the connected
firmware; this library preserves the integer or floating-point value without
inventing a parameter meaning.

.. seealso::

   :doc:`Adjustable variables API reference <api/adjvars>` lists the complete
   public method set and its parameter ranges.

Read and change values
----------------------

Use ``g.get_adj_var(id)`` for one integer variable or
``g.get_adj_vars(ids)`` for a batch of one to 40 unique IDs. The result is an
``AdjustableVariable`` record containing ``id`` and a signed 32-bit raw
``value``.

.. code-block:: python

   from sbgc32 import AdjustableVariable

   current = g.get_adj_var(1)
   print(current.id, current.value)

   g.set_adj_var(1, current.value + 1)
   g.set_adj_vars((
       AdjustableVariable(id=1, value=5),
       AdjustableVariable(id=2, value=-10),
   ))

``set_adj_var`` and ``set_adj_vars`` update controller RAM only. The changes
are lost after a restart unless they are saved explicitly.

Persist to controller memory
----------------------------

``g.save_adj_vars(ids)`` persists selected variable IDs. It accepts from one
to 102 unique IDs. ``g.save_all_adj_vars()`` persists all active unsaved
variables.

.. warning::

   Saving writes persistent controller memory. Only save values that have been
   verified for the connected firmware and hardware configuration.

Floating-point variables
------------------------

The ``*_float`` methods provide the corresponding float protocol commands:

* ``get_adj_var_float`` and ``get_adj_vars_float``;
* ``set_adj_var_float`` and ``set_adj_vars_float``.

They use ``AdjustableVariableFloat`` records. A float must be finite, and the
same ID-count and uniqueness rules apply as for integer variables.

Configuration, state, and metadata
----------------------------------

``g.read_adj_vars_config()`` reads trigger and analog-slot configuration as
``AdjustableVariablesConfig``. ``g.write_adj_vars_config(config)`` writes the
entire configuration; it requires exactly ten trigger slots, 15 analog slots,
and eight reserved bytes.

``g.get_adj_vars_state(...)`` reads selected runtime state for one trigger,
analog, and lookup-table path. ``g.get_adj_vars_info(start_id=0)`` returns
controller-provided integer metadata: ID, minimum, maximum, and current value.

Readable output
---------------

The following methods return plain text tables suitable for ``print`` or a log
file. They do not emit output themselves.

.. code-block:: python

   variables = g.get_adj_vars((1, 2, 3))
   print(g.format_adj_vars(variables))

   # Omit the argument to request fresh metadata or configuration.
   print(g.format_adj_vars_info())
   print(g.format_adj_vars_config())

``g.format_adj_vars_state(state)`` formats an already read
``AdjustableVariablesState``. Formatting is intentionally separate from the
communication operation, so an application can log a previous result without
issuing another controller request.
