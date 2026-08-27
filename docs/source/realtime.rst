Realtime data
=============

The realtime API offers two communication patterns:

* request a single current value, for example the gimbal angles;
* configure a periodic controller stream and read its raw packets.

All examples assume an open :class:`~sbgc32.SimpleBGC` connection. A serial
port may only be opened by one application at a time.

Read current angles
-------------------

Use :meth:`~sbgc32.SimpleBGC.get_angles` when a compact, converted view of the
IMU, target, and target-speed angles is sufficient. The returned
:class:`~sbgc32.Angles` object exposes each axis as named ``roll``, ``pitch``,
and ``yaw`` values.

.. code-block:: python

   from sbgc32 import SimpleBGC

   with SimpleBGC("COM4") as gimbal:
       angles = gimbal.get_angles()
       print(f"IMU roll: {angles.imu.roll:.2f}°")
       print(f"Target pitch: {angles.target.pitch:.2f}°")

For the extended protocol representation, use
:meth:`~sbgc32.SimpleBGC.get_angles_ext`. Its ``axis_gae`` items retain the
raw angle values, while the ``imu``, ``target``, and ``frame_cam`` properties
provide converted axis triples.

Realtime packets
----------------

:meth:`~sbgc32.SimpleBGC.get_realtime_data_3` returns the fixed
``REALTIME_DATA_3`` packet. The legacy
:meth:`~sbgc32.SimpleBGC.get_realtime_data` method is an alias with the same
result. :meth:`~sbgc32.SimpleBGC.get_realtime_data_4` returns the extended
``REALTIME_DATA_4`` packet and includes every ``RealtimeData3`` field.

.. code-block:: python

   data = gimbal.get_realtime_data_3()
   print(f"Battery: {data.bat_level / 100:.2f} V")
   print(f"Controller error mask: 0x{data.system_error:04X}")

``RealtimeData3`` and ``RealtimeData4`` deliberately preserve most protocol
fields in their raw form. In particular, angle arrays, sensor readings,
temperatures, flags, and error fields should be interpreted using the firmware
documentation for the connected controller. ``bat_level`` is represented in
centivolts, as shown above.

Request a custom packet
-----------------------

``REALTIME_DATA_CUSTOM`` lets the application select only the fields it needs.
Combine :class:`~sbgc32.RealtimeDataCustomFlag` members with ``|`` and pass the
result to :meth:`~sbgc32.SimpleBGC.get_realtime_data_custom`.

.. code-block:: python

   from sbgc32 import RealtimeDataCustomFlag as RTD

   flags = RTD.IMU_ANGLES | RTD.RC_DATA | RTD.COMM_ERRORS
   data = gimbal.get_realtime_data_custom(flags)

   print(f"Timestamp: {data.timestamp_ms} ms")
   print("IMU angles:", data.fields[RTD.IMU_ANGLES])
   print("RC data:", data.fields[RTD.RC_DATA])

The result is a :class:`~sbgc32.RealtimeDataCustom` object. Its ``fields``
mapping is keyed by the requested flag, so a field can be accessed without
depending on its position in the packet. ``raw_payload`` is retained for
diagnostics and protocol-level inspection.

The library computes the request size from the selected flags and rejects a
selection whose protocol payload would exceed 255 bytes.

Periodic data streams
---------------------

Create one :class:`~sbgc32.DataStreamConfig` and reuse the same object to
start, read, and stop a stream. ``interval_ms`` must be between 1 and 65,535.
The meaning of ``config`` is command-specific.

.. code-block:: python

   from sbgc32 import DataStreamCommand, DataStreamConfig

   stream = DataStreamConfig(
       command=DataStreamCommand.REALTIME_DATA_3,
       interval_ms=20,
   )

   gimbal.start_data_stream(stream)
   try:
       payload = gimbal.read_data_stream(stream)
       print(payload.hex(" "))
   finally:
       gimbal.stop_data_stream(stream)

For ``REALTIME_DATA_3``, ``REALTIME_DATA_4``, ``AHRS_HELPER``, and ``EVENT``,
the library knows the protocol payload length. For other stream commands,
pass the expected length through ``size`` to
:meth:`~sbgc32.SimpleBGC.read_data_stream`.

For a custom realtime stream, encode the selected flags in the first four
little-endian bytes of ``config``:

.. code-block:: python

   flags = RTD.IMU_ANGLES | RTD.RC_DATA
   stream = DataStreamConfig(
       command=DataStreamCommand.REALTIME_DATA_CUSTOM,
       interval_ms=50,
       config=int(flags).to_bytes(4, byteorder="little"),
   )

``read_data_stream`` returns the raw payload. It does not convert a custom
stream into ``RealtimeDataCustom`` automatically; retain the configuration and
decode the bytes according to the same selected flags when protocol-level
processing is required.

RC inputs
---------

Use :meth:`~sbgc32.SimpleBGC.read_rc_inputs` to read one to 42 controller RC
sources. Source IDs may be integers or :class:`~sbgc32.RcInputSource` values.
The return tuple follows the input order; inactive inputs are represented by
``None`` and active values are normalized to the standard ``-500`` to ``500``
range.

.. code-block:: python

   from sbgc32 import RcInputSource

   roll, pitch = gimbal.read_rc_inputs((
       RcInputSource.ROLL,
       RcInputSource.PITCH,
   ))

Debug variables
---------------

First request metadata, then use it to request values. The metadata list must
be retained and supplied unchanged to the values request.

.. code-block:: python

   variables = gimbal.request_debug_var_info_3()
   print(gimbal.format_debug_var_info_3(variables))

   values = gimbal.request_debug_var_values_3(variables)
   for variable in values:
       print(variable.name, variable.value)

``DebugVarInfo.raw_type`` preserves the protocol type and flags.
``raw_value`` is the unsigned 32-bit value received from the controller;
``value`` is its decoded integer or floating-point representation.

IMU selection and quaternion status
-----------------------------------

:meth:`~sbgc32.SimpleBGC.select_imu_3` selects the main or frame IMU, or
performs one of the extended actions in
:class:`~sbgc32.SelectImuAction`. Some actions change controller calibration;
request a confirmation when the connected firmware supports it.

``CMD_CONTROL_QUAT_STATUS`` is available through
:meth:`~sbgc32.SimpleBGC.get_control_quat_status` on firmware 2.73 and newer.
Request only the status fields needed by combining
:class:`~sbgc32.ControlQuatStatusFlag` members. The resulting
:class:`~sbgc32.ControlQuatStatus` contains ``None`` for fields that were not
requested. Quaternion speed fields retain their raw protocol units.
