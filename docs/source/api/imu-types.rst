IMU and AHRS data types
=======================

.. py:class:: sbgc32.ExternalImuDebugInfo

   .. list-table::
      :header-rows: 1
      :widths: 34 20 46

      * - Field group
        - Type
        - Meaning
      * - reference-source and error fields
        - ``int``
        - Main/frame reference sources and their errors.
      * - ``external_imu_status`` / packet counters
        - ``int``
        - External IMU status, packets received, and parse errors.
      * - ``dcm`` / ``acceleration_body``
        - float tuples
        - Direction cosine matrix and body acceleration.

.. py:class:: sbgc32.AhrsHelper

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``z_vector``
        - ``tuple[float, float, float]``
        - Reference vertical vector.
      * - ``h_vector``
        - ``tuple[float, float, float]``
        - Reference horizontal vector.

.. py:class:: sbgc32.GyroCorrection

   Fields: ``imu_type`` (:class:`~sbgc32.ImuType`), three signed 16-bit
   ``zero_correction`` values, and optional signed 16-bit
   ``zero_heading_correction``.

.. py:class:: sbgc32.HelperData

   Fields: three signed 16-bit ``frame_acceleration`` values plus
   ``frame_angle_roll`` and ``frame_angle_pitch``.

.. py:class:: sbgc32.HelperDataExt

   Extends ``HelperData`` with :class:`~sbgc32.HelperDataFlag`, three
   ``frame_speed`` values, and ``frame_heading``.

Related enums: :class:`~sbgc32.ExternalImuCommandType`,
:class:`~sbgc32.ExternalSensorCommandFlag`,
:class:`~sbgc32.AhrsHelperDirection`, :class:`~sbgc32.AhrsHelperLocation`,
:class:`~sbgc32.AhrsHelperCorrection`, :class:`~sbgc32.AhrsHelperTranslation`,
:class:`~sbgc32.AhrsHelperReference`, and :class:`~sbgc32.AhrsHelperOption`.
