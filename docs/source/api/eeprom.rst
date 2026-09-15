EEPROM and file-system commands
===============================

The EEPROM module accesses I2C registers, raw EEPROM addresses, external data
and the controller file system. Read commands return bytes or ``EepromFile``;
write and clear commands return ``None`` or a requested confirmation.

.. autofunction:: sbgc32.modules.eeprom.read_i2c_register
.. autofunction:: sbgc32.modules.eeprom.write_i2c_register
.. autofunction:: sbgc32.modules.eeprom.read_eeprom
.. autofunction:: sbgc32.modules.eeprom.write_eeprom
.. autofunction:: sbgc32.modules.eeprom.read_external_data
.. autofunction:: sbgc32.modules.eeprom.write_external_data
.. autofunction:: sbgc32.modules.eeprom.read_file
.. autofunction:: sbgc32.modules.eeprom.write_file
.. autofunction:: sbgc32.modules.eeprom.clear_file_system
