Control data types
==================

The controller expects values in roll, pitch, yaw order unless stated
otherwise. Prefer the listed enum classes to raw integers.

Basic control
-------------

.. py:class:: sbgc32.ControlAxis

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``mode``
        - ``ControlMode | int``
        - Control mode for one axis.
      * - ``speed``
        - ``float``
        - Target speed; units depend on ``mode``.
      * - ``angle``
        - ``float``
        - Target angle; units depend on ``mode``.

.. py:class:: sbgc32.ControlAxisConfig

   .. list-table::
      :header-rows: 1
      :widths: 34 20 46

      * - Field
        - Type
        - Meaning
      * - ``angle_lpf`` / ``speed_lpf`` / ``rc_lpf``
        - ``int``
        - Low-pass filter settings.
      * - ``acceleration_limit`` / ``jerk_slope``
        - ``int``
        - Motion-limit settings.

.. py:class:: sbgc32.ControlConfig

   .. list-table::
      :header-rows: 1
      :widths: 30 25 45

      * - Field
        - Type
        - Meaning
      * - ``timeout_ms``
        - ``int``
        - Control-command timeout in milliseconds.
      * - ``channel_priorities``
        - ``tuple[int, int, int, int, int]``
        - Priorities of the controller input channels.
      * - ``axes``
        - ``tuple[ControlAxisConfig, ControlAxisConfig, ControlAxisConfig]``
        - Per-axis configuration.
      * - ``rc_expo_rate`` / ``flags`` / ``euler_order``
        - ``int`` / ``ControlConfigFlag`` / ``int``
        - RC response, command flags, and Euler rotation order.

Extended and quaternion control
-------------------------------

.. py:class:: sbgc32.ControlExtAxis

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``mode``
        - ``ControlMode | int``
        - Extended control mode.
      * - ``flags``
        - ``ControlExtFlag | int``
        - Extended-axis flags.
      * - ``speed`` / ``angle``
        - ``int``
        - Raw values selected by the parent data-set mask.

.. py:class:: sbgc32.ControlExt

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``data_set``
        - ``ControlExtDataSet | int``
        - Bit mask of included fields.
      * - ``axes``
        - ``tuple[ControlExtAxis, ControlExtAxis, ControlExtAxis]``
        - Per-axis raw control values.

.. py:class:: sbgc32.ControlQuat

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``mode`` / ``flags``
        - ``ControlQuatMode`` / ``ControlQuatFlag``
        - Quaternion control mode and flags.
      * - ``attitude``
        - ``tuple[float, float, float, float]``
        - Target quaternion.
      * - ``speed``
        - ``tuple[float, float, float]``
        - Target angular speeds.

.. py:class:: sbgc32.ControlQuatConfig

   .. list-table::
      :header-rows: 1
      :widths: 34 20 46

      * - Field
        - Type
        - Meaning
      * - ``data_set`` / ``flags``
        - ``ControlQuatConfigParameter`` / ``ControlQuatConfigFlag``
        - Included settings and configuration flags.
      * - ``max_speed`` / ``acceleration_limit`` / ``jerk_slope``
        - 3-tuples of ``int``
        - Per-axis motion limits.
      * - ``attitude_lpf_frequency`` / ``speed_lpf_frequency``
        - ``int``
        - Attitude and speed low-pass filter settings.

External motors
---------------

.. py:class:: sbgc32.ExternalMotorControl

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``setpoint``
        - ``int``
        - Raw external-motor setpoint.
      * - ``param1``
        - ``int``
        - Firmware-defined auxiliary parameter.

.. py:class:: sbgc32.ExternalMotorsControlConfig

   .. list-table::
      :header-rows: 1
      :widths: 30 25 45

      * - Field
        - Type
        - Meaning
      * - ``motors`` / ``data_set``
        - ``ExternalMotor`` / configuration bit mask
        - Selected motors and fields to change.
      * - ``mode``
        - ``ExternalMotorsControlMode``
        - External-motor control mode.
      * - ``max_speed`` / ``max_acceleration`` / ``jerk_slope`` / ``max_torque``
        - ``int``
        - Motion and torque limits.

Related enums: :class:`~sbgc32.ControlMode`, :class:`~sbgc32.ControlFlag`,
:class:`~sbgc32.ControlExtDataSet`, :class:`~sbgc32.ControlQuatMode`,
:class:`~sbgc32.ExternalMotor`, and :class:`~sbgc32.ExternalMotorAction`.
