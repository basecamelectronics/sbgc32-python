SimpleBGC32 Python API
======================

This documentation describes the public Python interface for the
`SimpleBGC32 Serial API <https://www.basecamelectronics.com/serialapi/>`_.
For installation, transport backends, and a minimal connection example, see
the project's ``README.md``.

The Python layer provides typed, connection-oriented access to selected
controller commands. The official Serial API documentation remains the source
of truth for command identifiers, firmware compatibility, protocol units, and
bit definitions.

.. toctree::
   :maxdepth: 2
   :caption: Guides

   realtime
   control
   adjvars
   service
   calibration
   eeprom
   imu
   profiles
   execute-formatting

.. toctree::
   :maxdepth: 2
   :caption: API reference

   api/realtime
   api/control
   api/adjvars
   api/service
   api/calibration
   api/eeprom
   api/imu
   api/profiles
   api/execute-formatting
