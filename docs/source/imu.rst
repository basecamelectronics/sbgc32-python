IMU and AHRS
============

This module covers communication with external IMUs/sensors and the AHRS
helper commands. Its structures intentionally expose firmware-level values;
consult the Serial API specification for coordinate systems, units, and flag
semantics.

Build AHRS mode values with :func:`~sbgc32.pack_ahrs_helper_mode` rather than
combining raw bits manually:

.. code-block:: python

   from sbgc32 import AhrsHelperDirection, pack_ahrs_helper_mode

   mode = pack_ahrs_helper_mode(direction=AhrsHelperDirection.GET)
   helper = gimbal.get_ahrs_helper(mode)
   print(gimbal.format_ahrs_helper(helper))

For external commands, choose ``ExternalImuCommandType.TX`` when no response
is expected. ``RX`` requires an empty payload and an explicit response size;
``TX_RX`` requires a response of the same length as the sent payload.

.. seealso::

   :doc:`IMU and AHRS API reference <api/imu>`
