SimpleBGC32 Python API
======================

Python interface for the `SimpleBGC32 Serial API
<https://www.basecamelectronics.com/serialapi/>`_. The API is asynchronous:
controller methods return :class:`concurrent.futures.Future` objects. Call
``.result()`` when the decoded response is needed.

Quick start
-----------

.. code-block:: python

   from sbgc32 import SimpleBGC

   with SimpleBGC("COM4") as gimbal:
       angles = gimbal.get_angles().result()
       print(gimbal.format.angles(angles))

The official SerialAPI documentation is authoritative for controller firmware
compatibility, protocol units, and command-specific bit definitions.

.. toctree::
   :maxdepth: 2
   :caption: API reference

   api/device
   api/errors
   api/formatter
   api/types
   api/realtime
   api/control
   api/adjvars
   api/calibration
   api/eeprom
   api/imu
   api/profiles
   api/service
