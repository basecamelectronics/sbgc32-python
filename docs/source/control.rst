Control
=======

The control API changes the gimbal state. Make sure the controller is mounted
securely, the workspace is clear, and the active firmware supports the command
before sending a movement or external-motor request.

.. seealso::

   :doc:`Control API reference <api/control>` lists every public control method
   and its parameters.

Basic three-axis control
------------------------

``g.control()`` sends one ``CMD_CONTROL`` record for roll, pitch, and yaw. It
always receives exactly three ``ControlAxis`` records in that order. In normal
angle modes, ``angle`` is expressed in degrees and ``speed`` in degrees per
second; the library converts them to the Serial API representation.

.. code-block:: python

   from sbgc32 import ControlAxis, ControlMode, SimpleBGC

   with SimpleBGC("COM4") as g:
       g.control((
           ControlAxis(mode=ControlMode.NO_CONTROL),
           ControlAxis(mode=ControlMode.ANGLE, angle=-10.0, speed=20.0),
           ControlAxis(mode=ControlMode.NO_CONTROL),
       ))

Use ``ControlMode`` to choose the base movement mode and combine it with
``ControlFlag`` when a supported command flag is required. In ``RC`` and
``RC_HIGH_RES`` modes, ``ControlAxis.angle`` is the integral raw RC value, not
an angle in degrees.

Pass ``need_confirmation=True`` when the caller must inspect the controller's
``CMD_CONFIRM`` or ``CMD_ERROR`` response. The method then returns a
``CommandConfirmation``; otherwise it returns ``None``.

Control configuration
---------------------

``g.configure_control(config)`` sends ``CMD_CONTROL_CONFIG``. A
``ControlConfig`` combines a command timeout, five channel priorities, and
three ``ControlAxisConfig`` records. Use it to configure filtering and the
motion profile before regular movement commands.

.. code-block:: python

   from sbgc32 import ControlAxisConfig, ControlConfig

   config = ControlConfig(
       timeout_ms=1_000,
       channel_priorities=(0, 0, 0, 0, 100),
       axes=(
           ControlAxisConfig(),
           ControlAxisConfig(angle_lpf=2, speed_lpf=2),
           ControlAxisConfig(),
       ),
   )
   g.configure_control(config, confirm_control=True)

``confirm_control`` controls whether subsequent ``CMD_CONTROL`` commands ask
the controller for a confirmation. ``control_config()`` is an alias for
``configure_control()``.

Virtual RC channels
-------------------

``g.set_api_virtual_channels(values)`` writes one to 32 standard API virtual
channels. Each value must be in ``-500`` to ``500``; use ``None`` for an
undefined channel. ``g.set_api_virtual_channels_hr(values)`` is the
high-resolution variant and accepts values in ``-16384`` to ``16384``.

.. code-block:: python

   # Set API_VIRTUAL_1 and API_VIRTUAL_2; leave the third channel undefined.
   g.set_api_virtual_channels((120, -120, None))

The configured controller input mapping determines which functions consume
these channels.

Extended control
----------------

Use the extended methods only when their firmware support and raw protocol
units are understood:

* ``g.control_ext(ControlExt(...))`` sends a selected set of 32-bit axis
  fields. The ``ControlExtDataSet`` mask specifies which fields are present.
* ``g.control_quat(ControlQuat(...))`` sends quaternion attitude and speed
  control; ``g.configure_control_quat(ControlQuatConfig(...))`` configures it.
* ``g.ext_motors_action(motors, action)`` changes the state of selected
  external motors.
* ``g.control_ext_motors(control, motors, data_set=...)`` sends a raw external
  motor setpoint; ``g.configure_ext_motors(config)`` configures its limits and
  mode.

``motors`` is a bit mask. Prefer combinations of ``ExternalMotor`` members to
unnamed integers, for example ``ExternalMotor.ID_1 | ExternalMotor.ID_2``.

.. warning::

   Extended and quaternion control can move the gimbal or external motors
   immediately. Validate the selected mode, data-set mask, and raw values
   against the controller's Serial API documentation before enabling them on
   hardware.

Method summary
--------------

``control`` and ``configure_control`` cover the common three-axis workflow.
``set_api_virtual_channels`` and ``set_api_virtual_channels_hr`` feed virtual
RC inputs. ``control_ext``, ``control_quat``, ``configure_control_quat``,
``ext_motors_action``, ``control_ext_motors``, and ``configure_ext_motors``
are advanced protocol-level methods.
