Serial API update: September 2026
===================================

Based on ``SimpleBGC_2_6_Serial_Protocol_Specification.pdf``, updated
September 11, 2026. The filename is historical: the document describes
firmware features through 2.74.5. Methods return Futures as before.
Firmware compatibility is command-specific; this update does not make newer
commands available on older controllers.

Added commands and fields
---------------------------

.. list-table:: New public methods on SimpleBGC
   :header-rows: 1
   :widths: 10 30 60

   * - Command
     - Method
     - Request / response
   * - 78
     - ``start_module_flash``
     - DEVICE_ID (u8), FIRMWARE_SIZE (u32, words); confirmation or error.
   * - 81
     - ``write_module_flash``
     - DEVICE_ID (u8), PACKET_ID (u8), ADDRESS (u32, byte offset), DATA_CRC32
       (u32), DATA (4..128 bytes, multiple of 4); confirmation or error.
   * - 83
     - ``finish_module_flash``
     - DEVICE_ID (u8), FILE_CRC32 (u32); confirmation or error.
   * - 136
     - ``read_password_protection``
     - Empty request; FLAGS (u32), RESERVED (4 bytes). Firmware 2.73.6+.
   * - 137
     - ``write_password_protection``
     - FLAGS (u32), RESERVED (4 zero bytes), NEW_PASS_LENGTH (u8), optional
       NEW_PASSWORD (1..32 bytes); confirmation or error. Firmware 2.73.6+.
   * - 139
     - ``get_realtime_data_custom2``
     - DATA_SET_FLAGS (u32), RESERVED (6 zero bytes); selected telemetry.
       Firmware 2.74.2+, STAB_ERR_AMPL requires 2.74.4+.
   * - 143
     - ``set_transparent_proxy``
     - PORT1 (u8), PORT2 (u8); zero means current port. No success reply;
       errors are unsolicited. Firmware 2.74.5+.
   * - 144
     - ``scan_udrv_devices``
     - Empty request; response command 96, repeated UID (12 bytes), ID (u8),
       TYPE (u8). Detects the IMU connection and assigns IDs automatically.

CUSTOM2 fields are returned in wire units in the immutable ``fields`` mapping:

.. list-table:: RealtimeDataCustom2Flag
   :header-rows: 1

   * - Bit
     - Flag
     - Layout / units
   * - 0
     - FRAME_IMU_ANGLES
     - 3 signed 16-bit values; 360/16384 degrees.
   * - 1
     - FRAME_GYRO
     - 3 signed 16-bit values; 0.06103701895 degrees/s.
   * - 2
     - FRAME_ACC
     - 3 signed 16-bit values; 1/512 G.
   * - 3
     - DEBUG
     - 4 signed 16-bit values.
   * - 4
     - MAG_SENS_DATA
     - 3 signed 16-bit values.
   * - 5
     - PIN_STATE
     - 8 bytes: extra_buttons_state (u16), pin_state (u16), reserved (4 bytes).
   * - 6
     - STAB_ERR_AMPL
     - 3 unsigned 16-bit values; 0.001 degrees.
   * - 31
     - INCLUDE_FLAGS
     - Echo u32 flags immediately after the u16 timestamp; validated on receipt.

The PDF's ``PIN_STATE: 12b`` heading is a typo. The eight-byte layout was
explicitly confirmed by the project owner. Input states are packed in groups
of two bits: 0 low, 1 high, 2 unavailable/unassigned.

.. code-block:: python

   from sbgc32 import RealtimeDataCustom2Flag as F

   flags = F.FRAME_IMU_ANGLES | F.PIN_STATE | F.INCLUDE_FLAGS
   sample = gimbal.get_realtime_data_custom2(flags).result()
   print(sample.timestamp_ms, sample.fields[F.FRAME_IMU_ANGLES])
   print(sample.fields[F.PIN_STATE].pin_state)

For periodic data, use ``DataStreamCommand.REALTIME_DATA_CUSTOM2`` and
``DataStreamConfig(..., config=struct.pack("<I", int(flags)))``. Stream reads
continue to return bytes; pass them to ``parse_realtime_data_custom2``.

Changes to existing methods and fields
----------------------------------------

* ``get_board_info(password=...)`` sends an optional length-prefixed password.
  Authenticate a protected port before other commands. Passwords are bytes;
  callers choose the encoding for text. ``None`` omits authentication.
* ``write_password_protection(new_password=None)`` sends a zero length to keep
  the current password. Empty passwords are rejected instead of silently
  changing the meaning of the request.
* ``BoardInfo3.script_slot_sizes_ext`` exposes slots 6..10 previously discarded
  by the decoder. ``script_slot_sizes`` still contains slots 1..5.
* ``REALTIME_DATA_CUSTOM`` supports bits 28 (FRAME_CAM_ANGLE_20), 29
  (MAIN_IMU_STATE), and 31 (INCLUDE_FLAGS). Requests include the six reserved
  bytes specified in the document. Bit 30 remains unsupported. Existing
  fields and raw units are retained; ``FRAME_CAM_ANGLE`` aliases the existing
  ``STATOR_ROTOR_ANGLE`` name. Responses exceeding 255 bytes are rejected.
* ``get_realtime_data`` expects command 23 in response to legacy command 68.
* ``request_module_list`` accepts 17 modules, including uDrv IDs 14..17,
  and validates DEVICE_NUM against the actual number of 13-byte records.
* ``scan_can_devices`` returns all records. The existing ``scan_can_device``
  returns the first record and retains its no-device exception; the plural
  methods return an empty tuple for an empty successful response.
  A rejected scan raises ``ControllerCommandError`` with the original command
  ID, error code and extra bytes; it is distinct from an empty successful scan.
* ``CMD_CONFIRM`` accepts 0..4 data bytes. Flash errors retain DEVICE_ID and
  PACKET_ID as the two little-endian u16 values in ``error_data``. Confirmations
  and errors are routed by the original request even if the normal reply uses
  another command ID.
* ``ControlConfigFlag.LPF_FREQUENCY_HZ`` and
  ``ControlQuatFlag.ATTITUDE_REMOVE_ABSENT_AXES`` expose the 2.74.1 flags.
* ``TriggerPin`` includes CAN Driver/CAN IMU auxiliary pins.
  ``TriggerPinState.PULLED_UP`` and ``PULLED_DOWN`` add the 2.74.3 input modes.
  Input confirmations contain PIN_ID (low byte) and signed PIN_STATE (next
  byte) in ``command_data``; -1 means the pin is unavailable.

The existing fixed realtime layouts remain 63 and 124 bytes, and extended
board information remains 69 bytes. Profile methods continue to expose opaque
parameter blocks (134, 104, 151 and 221 bytes), preserving new fields in those
blocks without converting them to named Python properties. Existing raw
command/stream interfaces remain available for commands without typed helpers.
This update does not claim a typed wrapper for every command in the PDF.

Flashing and CRC32
--------------------

``sbgc32.crc32`` implements CRC-32/ISO-HDLC with polynomial 0x04C11DB7,
reflected input/output, initial register 0xFFFFFFFF and final XOR 0xFFFFFFFF,
as confirmed by the project owner. The result is unsigned; the check vector
``b"123456789"`` yields ``0xCBF43926``. It uses Python's standard library and
does not change the native SerialAPI CRC16 framing implementation.

``write_module_flash`` computes the chunk CRC automatically unless
``data_crc32`` is supplied explicitly. ``finish_module_flash`` accepts the
CRC of the entire original file. Module IDs come from ``request_module_list``;
they differ from the IDs returned by bus scans. No padding is added implicitly.

.. code-block:: python

   from pathlib import Path
   from sbgc32 import ConfirmationStatus, crc32

   def require_success(reply):
       if reply.status != ConfirmationStatus.RECEIVED:
           raise RuntimeError(
               f"Flash error {reply.error_code}: {reply.error_data.hex()}"
           )

   firmware = Path("module.bin").read_bytes()
   if not firmware or len(firmware) % 4:
       raise ValueError("Firmware must contain a positive multiple of four bytes")

   # Select the intended device_id from request_module_list before this sequence.
   require_success(gimbal.start_module_flash(device_id, len(firmware) // 4).result())
   for packet, offset in enumerate(range(0, len(firmware), 128)):
       require_success(gimbal.write_module_flash(
           device_id, packet & 0xFF, offset, firmware[offset:offset + 128]
       ).result())
   require_success(gimbal.finish_module_flash(device_id, crc32(firmware)).result())

The example waits for every confirmation and stops on errors. It does not
retry writes or flash hardware automatically during tests. The checksum helper
also supports incremental use: ``crc32(next_chunk, previous_crc)``.

Validation
------------

``tests/test_api_2026.py`` exercises wire layouts, boundary checks, CRC vectors,
telemetry parsing, response routing, and both native framing versions without
opening a serial port. Run it with ``python -m pytest tests/test_api_2026.py``.
Actual firmware flashing, password changes, port bridging, and device ID
assignment require separate hardware validation.
