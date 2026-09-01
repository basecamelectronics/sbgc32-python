Service data types
==================

The service module also uses firmware enums such as
:class:`~sbgc32.MotorsOffMode` and :class:`~sbgc32.MenuCommands`.

Board and persistent state
--------------------------

.. py:class:: sbgc32.BoardInfo

   .. list-table::
      :header-rows: 1
      :widths: 34 20 46

      * - Field group
        - Type
        - Meaning
      * - ``board_ver`` / ``firmware_ver`` / ``build_number``
        - ``int``
        - Board and firmware version information.
      * - ``state_flags`` / ``board_features`` / ``board_features_ext``
        - ``int``
        - Firmware state and supported-feature bit masks.
      * - ``main_imu_sensor_model`` / ``frame_imu_sensor_model``
        - ``int``
        - Detected IMU sensor models.

.. py:class:: sbgc32.BoardInfo3

   .. list-table::
      :header-rows: 1
      :widths: 34 20 46

      * - Field group
        - Type
        - Meaning
      * - ``device_id`` / ``mcu_id``
        - ``bytes``
        - Controller and MCU identifiers.
      * - ``eeprom_size`` / ``flash_size_pages`` / ``script_slot_sizes``
        - ``int`` or tuples
        - Memory capacity and script-slot layout.
      * - ``hardware_flags`` / ``board_features_ext2``
        - ``int``
        - Extended hardware and feature bit masks.
      * - ``can_driver_main_limit`` / ``can_driver_aux_limit`` / ``adjustable_variables_total``
        - ``int``
        - CAN limits and available adjustable-variable count.

.. py:class:: sbgc32.StateVars

   .. list-table::
      :header-rows: 1
      :widths: 34 20 46

      * - Field group
        - Type
        - Meaning
      * - ``sub_error`` / ``max_acc`` / ``work_time`` / ``startup_count``
        - ``int``
        - Persistent maintenance counters.
      * - temperature, current, and energy fields
        - ``int`` / ``float``
        - Minimum/maximum temperatures and accumulated electrical data.
      * - ``reserved``
        - ``bytes``
        - Reserved protocol data; preserve it when writing a read value back.

PID and motor synchronization
-----------------------------

.. py:class:: sbgc32.AutoPidConfig

   .. list-table::
      :header-rows: 1
      :widths: 30 25 45

      * - Field
        - Type
        - Meaning
      * - ``profile_id`` / ``config_flags``
        - ``int`` / ``AutoPidFlag``
        - Target profile and legacy Auto PID flags.
      * - ``gain_vs_stability`` / ``momentum`` / ``action``
        - ``int``
        - Legacy Auto PID tuning settings.

.. py:class:: sbgc32.AutoPid2Axis

   .. list-table::
      :header-rows: 1
      :widths: 30 25 45

      * - Field group
        - Type
        - Meaning
      * - ``axis_flags`` / ``gain`` / ``stimulus_gain``
        - ``int``
        - Axis selection and tuning gains.
      * - frequency and margin fields
        - ``float``
        - Effective/problem frequency and allowed margin.

.. py:class:: sbgc32.AutoPid2Config

   .. list-table::
      :header-rows: 1
      :widths: 30 25 45

      * - Field group
        - Type
        - Meaning
      * - ``action`` / ``command_flags`` / ``general_flags``
        - ``int``
        - Auto PID2 operation and flags.
      * - ``axes``
        - three ``AutoPid2Axis`` values
        - Per-axis tuning configuration.
      * - frequency and multi-position fields
        - ``float`` / tuples
        - Test range and optional test positions.

.. py:class:: sbgc32.AutoPidState

   Contains the current P/I/D values, LPF frequencies, iteration count, and
   three per-axis states reported by legacy Auto PID.

.. py:class:: sbgc32.PidValues

   Contains ``profile_id`` and three-axis ``p``, ``i``, and ``d`` PID tuples.

.. py:class:: sbgc32.SyncMotorsConfig

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``axis``
        - ``int``
        - Axis to synchronize.
      * - ``power`` / ``time_ms`` / ``angle``
        - ``int``
        - Synchronization power, duration, and optional target angle.

Debug, script, and CAN results
------------------------------

.. py:class:: sbgc32.DebugPortPacket

   Fields: ``time_ms`` (packet timestamp), ``port_and_direction`` (port and
   direction flags), ``command_id``, and raw ``payload_buffer`` with
   ``payload_size``.

.. py:class:: sbgc32.ScriptDebugInfo

   Fields: ``current_command_counter`` and firmware ``error_code``.

.. py:class:: sbgc32.MenuExecutionResult

   Fields: ``started`` and ``finished`` confirmation results.

.. py:class:: sbgc32.CanModuleInfo

   Fields: ``can_id``, ``board_ver``, ``bootloader_ver``, and ``firmware_ver``.

.. py:class:: sbgc32.CanDeviceScan

   Fields: device ``uid``, ``can_id``, and ``can_type``.
