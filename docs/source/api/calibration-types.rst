Calibration data types
======================

.. py:class:: sbgc32.CalibInfo

   .. list-table::
      :header-rows: 1
      :widths: 34 20 46

      * - Field group
        - Type
        - Meaning
      * - ``progress`` / ``imu_type`` / ``current_axis``
        - ``int`` / ``ImuType``
        - Calibration progress, selected IMU, and active axis.
      * - ``acceleration`` / ``gyro_amplitude`` / ``heading_error_length``
        - tuple / ``int``
        - Firmware calibration measurements.
      * - temperature fields and slots
        - ``int`` / ``bool`` / tuple
        - Temperature calibration status and limits.

.. py:class:: sbgc32.CalibCoggingAxisConfig

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``angle`` / ``smooth`` / ``speed`` / ``period``
        - ``int``
        - Firmware cogging motion settings for one axis.

.. py:class:: sbgc32.CalibCogging

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``action``
        - ``CalibCoggingAction``
        - Calibrate or delete cogging data.
      * - ``axes``
        - ``CalibCoggingAxis``
        - Bit mask of target axes.
      * - ``axis_config``
        - Three ``CalibCoggingAxisConfig`` values
        - Roll, pitch, yaw configuration.
      * - ``iterations``
        - ``int``
        - Calibration iteration count.

Related enums: :class:`~sbgc32.ImuType`,
:class:`~sbgc32.CalibCoggingAction`, and :class:`~sbgc32.CalibCoggingAxis`.
