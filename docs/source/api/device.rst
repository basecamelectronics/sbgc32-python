SimpleBGC connection
====================

``SimpleBGC`` owns one serial connection. Its command methods are grouped by
SerialAPI domain on the following pages; this class only brings those methods
together on one connection object.

Commands are asynchronous internally. The reference deliberately displays the
logical result (for example, ``Angles`` or ``None``), rather than the internal
``Future`` wrapper. Call ``.result()`` in application code to obtain that
value or re-raise a communication, timeout, decoding, or controller error.

``format`` provides stateless text helpers. ``types`` is the complete namespace
of value classes and enums, so no individual type imports are required:

.. code-block:: python

   stop_mode = gimbal.types.MotorsOffMode.NORMAL

.. autoclass:: sbgc32.SimpleBGC

Connection operations
---------------------

.. automethod:: sbgc32.SimpleBGC.request_raw

.. automethod:: sbgc32.SimpleBGC.send_raw

.. automethod:: sbgc32.SimpleBGC.receive_unsolicited_raw

.. automethod:: sbgc32.SimpleBGC.close
