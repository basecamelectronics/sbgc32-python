Realtime public data types
==========================

This page describes the public objects returned by the realtime API and the
configuration objects passed to it. Except where explicitly stated otherwise,
integer fields preserve the controller's raw protocol representation. Consult
the official Serial API documentation for firmware-specific units, bit masks,
and field availability.

Angles
------

.. autoclass:: sbgc32.Axis3

   ``Axis3`` holds values in roll, pitch, yaw order.

.. autoclass:: sbgc32.Angles

   :attr:`~sbgc32.Angles.imu`, :attr:`~sbgc32.Angles.target`, and
   :attr:`~sbgc32.Angles.target_speed` are :class:`~sbgc32.Axis3` objects.
   ``get_angles()`` returns converted angular values suitable for display.

.. autoclass:: sbgc32.AxisGAE

   ``imu_angle``, ``target_angle``, and ``frame_cam_angle`` are raw extended
   protocol values for one axis. ``reserved`` is retained unchanged for
   forward compatibility.

.. autoclass:: sbgc32.AnglesExt
   :members:

   ``axis_gae`` contains three :class:`~sbgc32.AxisGAE` records in roll,
   pitch, yaw order. The ``imu``, ``target``, and ``frame_cam`` properties
   provide converted :class:`~sbgc32.Axis3` triples.

Fixed realtime packets
----------------------

.. autoclass:: sbgc32.AxisRealtimeData

   One axis record within :attr:`~sbgc32.RealtimeData3.axis_rtd`. Both fields
   are raw controller sensor values.

.. autoclass:: sbgc32.RealtimeData3

   ``REALTIME_DATA_3`` contains the following fields:

   .. list-table::
      :header-rows: 1
      :widths: 26 74

      * - Field
        - Meaning
      * - ``axis_rtd``
        - Three :class:`~sbgc32.AxisRealtimeData` records, one per axis.
      * - ``serial_error_count`` / ``i2c_error_count``
        - Controller communication-error counters.
      * - ``system_error`` / ``system_sub_error`` / ``error_code``
        - Firmware error fields and bit masks.
      * - ``rc_roll``, ``rc_pitch``, ``rc_yaw``, ``rc_cmd``
        - Raw RC control values.
      * - ``ext_fc_roll`` / ``ext_fc_pitch``
        - Raw external follow-control values.
      * - ``imu_angle`` / ``frame_imu_angle`` / ``target_angle``
        - Three raw roll, pitch, yaw angle values.
      * - ``cycle_time``
        - Controller cycle-time value in protocol units.
      * - ``bat_level``
        - Battery level in centivolts; divide by 100 for volts.
      * - ``rt_data_flags``
        - Realtime-status bit mask.
      * - ``cur_imu`` / ``cur_profile``
        - Currently active IMU and profile identifiers.
      * - ``motor_power``
        - Three raw motor-power values in roll, pitch, yaw order.
      * - ``reserved``
        - Raw reserved protocol bytes retained for forward compatibility.

.. autoclass:: sbgc32.RealtimeData4

   ``REALTIME_DATA_4`` inherits all fields of :class:`~sbgc32.RealtimeData3`
   and appends these values:

   .. list-table::
      :header-rows: 1
      :widths: 30 70

      * - Field
        - Meaning
      * - ``frame_cam_angle`` / ``actual_angle``
        - Raw three-axis angle arrays.
      * - ``balance_error`` / ``motor_out``
        - Raw three-axis controller values.
      * - ``current``
        - Raw controller current value.
      * - ``mag_data``
        - Raw three-axis magnetometer data.
      * - ``imu_temperature`` / ``frame_imu_temperature``
        - Temperature values in protocol units.
      * - ``imu_g_error`` / ``imu_h_error``
        - IMU calibration-error values.
      * - ``calib_mode``
        - Current calibration-mode identifier.
      * - ``can_imu_ext_sens_error``
        - CAN IMU external-sensor error field.
      * - ``system_state_flags``
        - Extended controller-state bit mask.
      * - ``reserved1`` / ``reserved2``
        - Reserved values retained unchanged.

Custom realtime packet
----------------------

.. autoclass:: sbgc32.RealtimeDataCustom

   ``timestamp_ms`` is the packet timestamp. ``fields`` is a read-only mapping
   from a requested :class:`~sbgc32.RealtimeDataCustomFlag` to its decoded
   value. ``raw_payload`` is the unmodified controller response.

.. autoclass:: sbgc32.RealtimeDataCustomFlag
   :members:

   Each selected member adds a field to ``RealtimeDataCustom.fields``. The
   library returns decoded tuples for fields with an implemented primitive
   representation and returns ``bytes`` where the nested protocol structure is
   not yet exposed as a dedicated Python type.

   .. list-table::
      :header-rows: 1
      :widths: 34 30 36

      * - Flag
        - Returned value shape
        - Description
      * - ``IMU_ANGLES``, ``TARGET_ANGLES``, ``TARGET_SPEED``, ``STATOR_ROTOR_ANGLE``, ``GYRO_DATA``, ``ACC_DATA``, ``FRAME_CAM_RATE``, ``FOLLOW_DIST``
        - Three signed integers
        - Raw three-axis data in protocol order.
      * - ``RC_DATA``
        - Six signed integers
        - Raw RC values.
      * - ``Z_VECTOR_H_VECTOR``
        - Six floats
        - Z and H vector data.
      * - ``RC_CHANNELS``
        - 18 signed integers
        - Raw RC channel values.
      * - ``MOTOR4_CONTROL``
        - Two signed integers and one float
        - Fourth-motor control data.
      * - ``IMU_ANGLES_RAD``
        - Three floats
        - IMU angles in radians.
      * - ``SCRIPT_VARS_FLOAT``
        - Ten floats
        - Script floating-point variables.
      * - ``SCRIPT_VARS_INT16``
        - Ten signed integers
        - Script 16-bit integer variables.
      * - ``IMU_ANGLES_20``, ``TARGET_ANGLES_20``
        - Three signed 32-bit integers
        - High-resolution raw angle values.
      * - ``COMM_ERRORS``
        - Three unsigned 16-bit integers and one byte
        - Controller communication-error fields.
      * - ``ADC_CH_RAW``
        - Four unsigned 16-bit integers
        - Raw ADC-channel data.
      * - ``SW_LIMITS_DIST``
        - Six signed integers
        - Software-limit distance data.
      * - ``EXT_TARGET_LIMIT``
        - Six signed 32-bit integers
        - Extended target-limit data.
      * - ``AHRS_DEBUG_INFO``, ``ENCODER_RAW24``, ``SYSTEM_POWER_STATE``, ``SYSTEM_STATE``, ``IMU_QUAT``, ``TARGET_QUAT``, ``IMU_TO_FRAME_QUAT``
        - ``bytes``
        - Raw nested protocol structures.

Data streams
------------

.. autoclass:: sbgc32.DataStreamCommand
   :members:

   The library automatically determines the payload length for
   ``REALTIME_DATA_3``, ``REALTIME_DATA_4``, ``REALTIME_DATA_CUSTOM``,
   ``AHRS_HELPER``, and ``EVENT``. Pass ``size`` to ``read_data_stream`` for
   all other commands.

.. autoclass:: sbgc32.DataStreamConfig

   .. list-table::
      :header-rows: 1
      :widths: 25 75

      * - Field
        - Meaning
      * - ``command``
        - :class:`~sbgc32.DataStreamCommand` to request periodically.
      * - ``interval_ms``
        - Period between controller packets, from 1 to 65,535 milliseconds.
      * - ``config``
        - Up to eight command-specific bytes. A custom realtime stream stores
          its four little-endian flag bytes here.
      * - ``sync_to_data``
        - Whether the controller synchronizes the stream to data updates.

Debug variables
---------------

.. autoclass:: sbgc32.DebugVarInfo

   .. list-table::
      :header-rows: 1
      :widths: 25 75

      * - Field
        - Meaning
      * - ``index`` / ``name``
        - Stable position and controller-provided ASCII name.
      * - ``raw_type``
        - Protocol type code and flags.
      * - ``raw_value``
        - Unsigned 32-bit value received from the controller, or ``None``
          before a value request.
      * - ``value``
        - Decoded integer or floating-point value, or ``None`` before a value
          request.

IMU and quaternion control
--------------------------

.. autoclass:: sbgc32.ImuType
   :members:

.. autoclass:: sbgc32.SelectImuAction
   :members:

.. autoclass:: sbgc32.ControlQuatStatusFlag
   :members:

.. autoclass:: sbgc32.ControlQuatStatus

   ``requested_fields`` records the request mask. All optional fields are
   ``None`` unless their respective flag was requested. Attitude fields are
   four-component float tuples; packed-attitude fields are raw bytes; speed
   fields retain raw signed protocol units.
