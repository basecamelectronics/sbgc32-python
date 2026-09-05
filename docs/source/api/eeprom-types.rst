EEPROM data types
=================

.. py:class:: sbgc32.EepromFile

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``file_id``
        - ``int``
        - Requested file identifier.
      * - ``page_offset``
        - ``int``
        - Page offset returned by the controller.
      * - ``data``
        - ``bytes``
        - File payload returned by the controller.
      * - ``error_code``
        - ``int``
        - Firmware file-system status.

Use :class:`~sbgc32.EepromFileId` when the requested file has a named
firmware-defined identifier.
