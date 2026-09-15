IMU and AHRS commands
=====================

The IMU module reads external-IMU diagnostics, sends external sensor messages,
and exchanges AHRS helper and correction data. Response commands return a
decoded structure or raw response tuple; fire-and-forget helper commands return
``None`` after transmission.

.. autofunction:: sbgc32.modules.imu.request_ext_imu_debug
.. autofunction:: sbgc32.modules.imu.send_ext_imu_command
.. autofunction:: sbgc32.modules.imu.send_ext_sens_command
.. autofunction:: sbgc32.modules.imu.get_ahrs_helper
.. autofunction:: sbgc32.modules.imu.set_ahrs_helper
.. autofunction:: sbgc32.modules.imu.correction_gyro
.. autofunction:: sbgc32.modules.imu.provide_helper_data
.. autofunction:: sbgc32.modules.imu.provide_helper_data_ext
