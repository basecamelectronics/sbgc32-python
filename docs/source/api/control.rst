Control API reference
=====================

:doc:`Control guide <../control>`

All methods below belong to an open ``SimpleBGC`` instance, named ``g`` in the
examples. A method accepting ``need_confirmation`` returns a
``CommandConfirmation`` only when this argument is true and the controller
confirms the command.

Basic control
-------------

.. list-table::
   :header-rows: 1
   :widths: 31 42 27

   * - Method
     - Parameters
     - Result
   * - ``g.control(axes, *, need_confirmation=False)``
     - ``axes`` — three :class:`~sbgc32.ControlAxis` values in roll, pitch,
       yaw order.
     - Confirmation or ``None``.
   * - ``g.configure_control(config=None, *, confirm_control=None, need_confirmation=False)``
     - ``config`` — :class:`~sbgc32.ControlConfig`; optional
       ``confirm_control`` selects controller confirmation behaviour.
     - Confirmation or ``None``.
   * - ``g.control_config(...)``
     - Alias of ``configure_control``.
     - Same as ``configure_control``.
   * - ``g.set_api_virtual_channels(values)``
     - One to 32 RC values in ``-500..500``; use ``None`` for an unchanged
       channel.
     - ``None``.
   * - ``g.set_api_virtual_channels_hr(values)``
     - One to 32 high-resolution RC values in ``-16384..16384``; ``None``
       leaves a channel unchanged.
     - ``None``.

Extended control
----------------

.. list-table::
   :header-rows: 1
   :widths: 31 42 27

   * - Method
     - Parameters
     - Result
   * - ``g.control_ext(control)``
     - ``control`` — :class:`~sbgc32.ControlExt`, with raw axis values chosen
       by its data-set mask.
     - ``None``.
   * - ``g.control_quat(control, *, need_confirmation=False)``
     - ``control`` — :class:`~sbgc32.ControlQuat` with attitude quaternion and
       speed.
     - Confirmation or ``None``.
   * - ``g.configure_control_quat(config, *, need_confirmation=False)``
     - ``config`` — :class:`~sbgc32.ControlQuatConfig`.
     - Confirmation or ``None``.
   * - ``g.ext_motors_action(motors, action, *, need_confirmation=False)``
     - ``motors`` — :class:`~sbgc32.ExternalMotor` bit mask; ``action`` —
       :class:`~sbgc32.ExternalMotorAction`.
     - Confirmation or ``None``.
   * - ``g.control_ext_motors(control, motors, data_set=0, *, need_confirmation=False)``
     - ``control`` — :class:`~sbgc32.ExternalMotorControl`; selected
       ``motors`` and firmware ``data_set`` mask.
     - Confirmation or ``None``.
   * - ``g.configure_ext_motors(config, *, need_confirmation=False)``
     - ``config`` — :class:`~sbgc32.ExternalMotorsControlConfig`.
     - Confirmation or ``None``.

Use the enums listed in the structures section instead of raw integral values
where possible. Valid data-set flags can depend on controller firmware.

Public data types
-----------------

.. toctree::
   :maxdepth: 1

   control-types
