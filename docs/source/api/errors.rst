Connection and module errors
============================

CAN-dependent commands resolve their returned ``Future`` with a specific
exception when the required hardware is unavailable. The predicate functions
allow application code to distinguish this condition from a serial timeout or
other communication failure.

CAN/uDrv scan rejections (``CMD_ERROR``) raise ``ControllerCommandError``.
Its ``command_id``, ``error_code`` and ``error_data`` retain the original reply.
Error-code meanings depend on the command family; a rejection is not classified
as ``CanDeviceNotFoundError`` and ``is_module_not_connected_error`` returns false.
An empty successful scan still returns an empty tuple from the plural methods,
or raises ``CanDeviceNotFoundError`` from the legacy ``scan_can_device`` method.

.. automodule:: sbgc32.errors
   :members:
   :show-inheritance:
