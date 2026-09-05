IMU and AHRS API reference
==========================

:doc:`IMU and AHRS guide <../imu>`

All methods below belong to an open ``SimpleBGC`` instance.

External IMU and sensor commands
--------------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 40 26

   * - Method
     - Parameters
     - Result
   * - ``g.request_ext_imu_debug()``
     - No parameters.
     - :class:`~sbgc32.ExternalImuDebugInfo`.
   * - ``g.send_ext_imu_command(command_id, payload=b'', *, command_type=TX, response_size=None)``
     - 8-bit command ID, up to 254 payload bytes, and
       :class:`~sbgc32.ExternalImuCommandType`.
     - ``None`` for TX, otherwise ``(command_id, payload)``.
   * - ``g.send_ext_sens_command(command_id, payload=b'', *, flags=LOW_PRIORITY, command_type=TX, response_size=None)``
     - As above, plus :class:`~sbgc32.ExternalSensorCommandFlag` values.
     - ``None`` for TX, otherwise ``(command_id, payload)``.
   * - ``g.format_ext_imu_debug(info)``
     - :class:`~sbgc32.ExternalImuDebugInfo`.
     - Text table (``str``).

AHRS and helper data
--------------------

.. list-table::
   :header-rows: 1
   :widths: 34 40 26

   * - Method
     - Parameters
     - Result
   * - ``pack_ahrs_helper_mode(...)``
     - Direction, location, correction, translation, reference, and options
       enums.
     - Packed 11-bit mode integer.
   * - ``g.get_ahrs_helper(mode=0)`` / ``g.set_ahrs_helper(helper, mode=1)``
     - GET/SET mode and :class:`~sbgc32.AhrsHelper` to write.
     - Helper structure / ``None``.
   * - ``g.correction_gyro(correction)``
     - :class:`~sbgc32.GyroCorrection`.
     - ``None``.
   * - ``g.provide_helper_data(data)`` / ``g.provide_helper_data_ext(data)``
     - :class:`~sbgc32.HelperData` or :class:`~sbgc32.HelperDataExt`.
     - ``None``.
   * - ``g.format_ahrs_helper(helper)``
     - :class:`~sbgc32.AhrsHelper`.
     - Text table (``str``).

Public data types
-----------------

.. toctree::
   :maxdepth: 1

   imu-types
