EEPROM API reference
====================

:doc:`EEPROM and file-system guide <../eeprom>`

All methods below belong to an open ``SimpleBGC`` instance. Addresses, file
IDs, and data layouts are firmware-specific.

I²C, EEPROM, and external data
------------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 40 26

   * - Method
     - Parameters
     - Result
   * - ``g.read_i2c_register(device_address, register_address, size)``
     - 8-bit I²C device/register addresses; read size ``1..240`` bytes.
     - Raw bytes.
   * - ``g.write_i2c_register(device_address, register_address, data, *, need_confirmation=False)``
     - 8-bit I²C addresses and ``1..240`` bytes.
     - Confirmation or ``None``.
   * - ``g.read_eeprom(address, size=64)``
     - 64-byte aligned address; a 64-byte aligned size up to 192 bytes.
     - Raw EEPROM bytes.
   * - ``g.write_eeprom(address, data, *, need_confirmation=False)``
     - 64-byte aligned address and ``64..192`` bytes.
     - Confirmation or ``None``.
   * - ``g.read_external_data()`` / ``g.write_external_data(data, *, need_confirmation=False)``
     - No parameters to read; exactly 128 bytes to write.
     - Raw bytes / confirmation or ``None``.

Controller file system
----------------------

.. list-table::
   :header-rows: 1
   :widths: 34 40 26

   * - Method
     - Parameters
     - Result
   * - ``g.read_file(file_id, page_offset=0, max_size=240)``
     - :class:`~sbgc32.EepromFileId` or 16-bit ID, page offset, and size.
     - :class:`~sbgc32.EepromFile`.
   * - ``g.write_file(file_id, data, *, page_offset=0, need_confirmation=False)``
     - File ID, ``1..240`` bytes, and page offset.
     - Confirmation or ``None``.
   * - ``g.clear_file_system(*, confirm=False)``
     - Must be called with ``confirm=True``.
     - ``None``; permanently removes every file.

Public data types
-----------------

.. toctree::
   :maxdepth: 1

   eeprom-types
