Calibration API reference
=========================

:doc:`Calibration guide <../calibration>`

Methods below belong to an open ``SimpleBGC`` instance. Starting a calibration
does not wait for it to complete.

Status and standard calibrations
--------------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 40 26

   * - Method
     - Parameters
     - Result
   * - ``g.request_calib_info(imu_type=ImuType.MAIN)``
     - Main or frame :class:`~sbgc32.ImuType`.
     - :class:`~sbgc32.CalibInfo`.
   * - ``g.calib_acc()`` / ``g.calib_gyro()`` / ``g.calib_mag()``
     - No parameters.
     - ``None``; starts the selected calibration.
   * - ``g.calib_poles()`` / ``g.calib_offset()``
     - No parameters.
     - ``None``; starts the selected motor calibration.
   * - ``g.calib_encoders_offset(motor=255)``
     - Axis ``0``, ``1``, ``2``, or ``255`` for all axes.
     - ``None``.
   * - ``g.calib_encoders_fld_offset()``
     - No parameters.
     - ``None``.

Special calibrations
--------------------

.. list-table::
   :header-rows: 1
   :widths: 34 40 26

   * - Method
     - Parameters
     - Result
   * - ``g.calib_bat(voltage, *, need_confirmation=False)``
     - Battery ``voltage`` in 0.01 V units.
     - Confirmation or ``None``.
   * - ``g.calib_orient_corr(*, need_confirmation=False)``
     - No parameters.
     - Confirmation or ``None``.
   * - ``g.calib_acc_ext_ref(reference, *, need_confirmation=False)``
     - Three signed 16-bit acceleration reference values.
     - Confirmation or ``None``.
   * - ``g.calib_cogging(cogging, *, need_confirmation=False)``
     - :class:`~sbgc32.CalibCogging` configuration.
     - Confirmation or ``None``.
   * - ``g.format_calib_info(info)``
     - :class:`~sbgc32.CalibInfo` returned previously.
     - Text table (``str``).

Public data types
-----------------

.. toctree::
   :maxdepth: 1

   calibration-types
