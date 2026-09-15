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
.. autofunction:: sbgc32.modules.control.configure_ext_motors
.. autofunction:: sbgc32.modules.control.set_api_virtual_channels_hr
