Connection and module errors
============================

CAN-dependent commands resolve their returned ``Future`` with a specific
exception when the required hardware is unavailable. The predicate functions
allow application code to distinguish this condition from a serial timeout or
other communication failure.

.. automodule:: sbgc32.errors
   :members:
   :show-inheritance:
