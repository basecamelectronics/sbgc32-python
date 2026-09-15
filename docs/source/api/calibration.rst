Calibration commands
====================

Calibration commands start a controller operation or read its progress.
Commands that only start an operation return ``None``; operations with a
requested confirmation return ``CommandConfirmation``. Invalid calibration
arguments are rejected before a frame is sent.

.. autofunction:: sbgc32.modules.calib.request_calib_info
.. autofunction:: sbgc32.modules.calib.calib_acc
.. autofunction:: sbgc32.modules.calib.calib_gyro
.. autofunction:: sbgc32.modules.calib.calib_mag
.. autofunction:: sbgc32.modules.calib.calib_poles
.. autofunction:: sbgc32.modules.calib.calib_offset
.. autofunction:: sbgc32.modules.calib.calib_encoders_fld_offset
.. autofunction:: sbgc32.modules.calib.calib_encoders_offset
.. autofunction:: sbgc32.modules.calib.calib_bat
.. autofunction:: sbgc32.modules.calib.calib_orient_corr
.. autofunction:: sbgc32.modules.calib.calib_acc_ext_ref
.. autofunction:: sbgc32.modules.calib.calib_cogging
