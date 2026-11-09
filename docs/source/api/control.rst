Gimbal control commands
=======================

The control module sends angle, speed, quaternion and external-motor control
commands. Configuration calls return a controller confirmation when requested;
commands without a response return ``None`` after their frame has been sent.
Invalid values raise ``TypeError`` or ``ValueError`` before transmission.

.. autofunction:: sbgc32.modules.control.control
.. autofunction:: sbgc32.modules.control.configure_control
.. autofunction:: sbgc32.modules.control.control_config
.. autofunction:: sbgc32.modules.control.set_api_virtual_channels
.. autofunction:: sbgc32.modules.control.control_ext
.. autofunction:: sbgc32.modules.control.control_quat
.. autofunction:: sbgc32.modules.control.configure_control_quat
.. autofunction:: sbgc32.modules.control.ext_motors_action
.. autofunction:: sbgc32.modules.control.control_ext_motors

For external motors, one ``ExternalMotorControl`` applies common values to
every selected motor. To supply different values, pass a tuple containing one
entry per selected motor, in ascending motor-ID order. No records are sent for
unselected motors. For example, motor IDs 1 and 3 receive different setpoints:

.. code-block:: python

   from sbgc32 import ExternalMotor, ExternalMotorControl

   gimbal.control_ext_motors(
       (ExternalMotorControl(setpoint=100), ExternalMotorControl(setpoint=-200)),
       motors=ExternalMotor.ID_1 | ExternalMotor.ID_3,
       need_confirmation=True,
   ).result()

Setpoints and optional ``param1`` values use raw protocol units. ``data_set``
selects 16-bit or 32-bit fields; ``PARAM1_16BIT`` and ``PARAM1_32BIT`` cannot be
combined. The confirmation flag adds no extra motor record.

.. autofunction:: sbgc32.modules.control.configure_ext_motors
.. autofunction:: sbgc32.modules.control.set_api_virtual_channels_hr
