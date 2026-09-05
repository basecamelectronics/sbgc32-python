Profiles API reference
======================

:doc:`Profiles guide <../profiles>`

All methods below belong to an open ``SimpleBGC`` instance. Raw profile blocks
must have the exact size defined by the corresponding firmware protocol.

Names and profile sets
----------------------

.. list-table::
   :header-rows: 1
   :widths: 34 40 26

   * - Method
     - Parameters
     - Result
   * - ``g.read_profile_names()``
     - No parameters.
     - Tuple of five UTF-8 profile names.
   * - ``g.write_profile_names(names, *, need_confirmation=False)``
     - Exactly five strings, up to 47 UTF-8 bytes each.
     - Confirmation or ``None``.
   * - ``g.manage_profile_set(slot, action, *, need_confirmation=False, confirm=False)``
     - :class:`~sbgc32.ProfileSet` and :class:`~sbgc32.ProfileSetAction`.
       Clearing requires ``confirm=True``.
     - Confirmation or ``None``.
   * - ``g.set_profile_writing(action, *, need_confirmation=False)``
     - :class:`~sbgc32.ProfileWritingAction`.
     - Confirmation or ``None``.

Raw parameter blocks
--------------------

.. list-table::
   :header-rows: 1
   :widths: 34 40 26

   * - Method
     - Parameters
     - Result
   * - ``g.read_profile_parameter_block(block, profile_id=ProfileId.CURRENT)``
     - Block ``0..3`` and :class:`~sbgc32.ProfileId`.
     - Raw block bytes: 134, 104, 151, or 221 bytes.
   * - ``g.write_profile_parameter_block(block, parameters, *, need_confirmation=False)``
     - Block ``0..3`` and its exact-size bytes.
     - Confirmation or ``None``.
   * - ``g.read_params_3()`` / ``g.read_params_ext()`` / ``g.read_params_ext2()`` / ``g.read_params_ext3()``
     - Optional profile ID.
     - Corresponding raw block bytes.
   * - ``g.write_params_3(...)`` / ``g.write_params_ext(...)`` / ``g.write_params_ext2(...)`` / ``g.write_params_ext3(...)``
     - Exact-size raw block bytes.
     - Confirmation or ``None``.
   * - ``g.read_profile_parameters(profile_id=ProfileId.CURRENT)``
     - Profile ID.
     - :class:`~sbgc32.ProfileParameters`.
   * - ``g.write_profile_parameters(parameters, *, need_confirmation=False)``
     - :class:`~sbgc32.ProfileParameters`.
     - ``None``; writes all blocks inside writing mode.
   * - ``g.use_profile_defaults(profile_id=ProfileId.CURRENT, *, confirm=False)``
     - Profile ID; must pass ``confirm=True``.
     - ``None``; restores firmware defaults.

Formatters
----------

``g.format_profile_names(names)`` and ``g.format_profile_parameters(parameters)``
return text tables for results already read from the controller.

Public data types
-----------------

.. toctree::
   :maxdepth: 1

   profiles-types
