EEPROM and file system
======================

This block gives low-level access to I²C registers, EEPROM pages, controller
external data, and the internal file system. It is intended for tools that
already understand the corresponding firmware layout.

EEPROM reads and writes are aligned to 64-byte pages. Read a complete value,
modify only the intended bytes, and write the page back so reserved bytes are
preserved.

.. warning::

   ``clear_file_system(confirm=True)`` irreversibly removes files stored by
   the controller. There is no recovery operation in the Python API.

.. seealso::

   :doc:`EEPROM API reference <api/eeprom>`
