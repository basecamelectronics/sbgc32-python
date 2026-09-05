Calibration
===========

The calibration methods start a controller-side procedure and return without
waiting for it to finish. Do not move the gimbal while a procedure is running.
Use :meth:`~sbgc32.SimpleBGC.request_calib_info` to inspect progress and
firmware-reported status.

.. code-block:: python

   from sbgc32 import ImuType

   gimbal.calib_acc()
   info = gimbal.request_calib_info(ImuType.MAIN)
   print(gimbal.format_calib_info(info))

Battery calibration changes a safety-relevant measurement. Cogging calibration
can create motor movement. Review the controller manual and use a safe setup
before invoking either operation.

.. seealso::

   :doc:`Calibration API reference <api/calibration>`
