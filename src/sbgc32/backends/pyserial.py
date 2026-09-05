"""Cross-platform transport that supplies SerialAPI through pyserial callbacks."""

from __future__ import annotations

import ctypes
from collections import deque
from threading import Event, Lock, Thread
from time import monotonic_ns
from typing import Any

from .._serial_api_library import NativeError, SerialApiLibrary

TxCallback = ctypes.CFUNCTYPE(
    ctypes.c_uint8,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.c_uint16,
)
RxCallback = ctypes.CFUNCTYPE(ctypes.c_uint8, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint8))
AvailableCallback = ctypes.CFUNCTYPE(ctypes.c_uint16, ctypes.c_void_p)
TimeCallback = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p)


class _PySerialTransport:
    """Reader thread and byte queue used by the native SerialAPI callbacks."""

    def __init__(self, port: str, baudrate: int) -> None:
        try:
            import serial
        except ImportError as error:
            raise NativeError("The pyserial backend requires the pyserial dependency.") from error

        self._serial_module = serial
        self._port = port
        self._baudrate = baudrate
        self._buffer: deque[int] = deque()
        self._debug_packets: deque[tuple[int, int, int, bytes]] = deque()
        self._debug_scan = bytearray()
        self._debug_capture_suppressed = False
        self._buffer_lock = Lock()
        self._open()

    def _open(self) -> None:
        self._serial: Any = self._serial_module.Serial(
            self._port,
            self._baudrate,
            timeout=0.1,
            write_timeout=1,
        )
        self._stop_reader = Event()
        self._serial.reset_input_buffer()
        self._reader = Thread(target=self._read_loop, name="sbgc32-pyserial-reader", daemon=True)
        self._reader.start()

    def _read_loop(self) -> None:
        while not self._stop_reader.is_set():
            try:
                data = self._serial.read(self._serial.in_waiting or 1)
            except Exception:  # noqa: BLE001
                return
            if data:
                with self._buffer_lock:
                    self._buffer.extend(data)
                    if not self._debug_capture_suppressed:
                        self._capture_debug_packets(data)

    def _capture_debug_packets(self, data: bytes) -> None:
        """Copy unsolicited P2 CMD_SET_DEBUG_PORT packets without consuming RX."""
        for value in data:
            if not self._debug_scan:
                if value == 0x24:  # '$', P2 frame start
                    self._debug_scan.append(value)
                continue

            self._debug_scan.append(value)
            if (
                len(self._debug_scan) == 4
                and (self._debug_scan[1] + self._debug_scan[2]) & 0xFF != self._debug_scan[3]
            ):
                self._debug_scan.clear()
                if value == 0x24:
                    self._debug_scan.append(value)
                continue

            if len(self._debug_scan) < 4:
                continue

            frame_size = self._debug_scan[2] + 6
            if len(self._debug_scan) < frame_size:
                continue
            if len(self._debug_scan) > frame_size:
                self._debug_scan.clear()
                continue

            frame = self._debug_scan
            payload_size = frame[2]
            payload = frame[4 : 4 + payload_size]
            received_crc = frame[payload_size + 4] | (frame[payload_size + 5] << 8)
            if (
                frame[1] == 249
                and payload_size >= 4
                and self._crc16(frame[1 : 4 + payload_size]) == received_crc
            ):
                packet = (
                    payload[0] | (payload[1] << 8),
                    payload[2],
                    payload[3],
                    bytes(payload[4:]),
                )
                if len(self._debug_packets) == 8:
                    self._debug_packets.popleft()
                self._debug_packets.append(packet)
            self._debug_scan.clear()

    @staticmethod
    def _crc16(data: bytes | bytearray) -> int:
        result = 0
        for value in data:
            for bit in range(8):
                data_bit = 1 if value & (1 << bit) else 0
                crc_bit = result >> 15
                result = (result << 1) & 0xFFFF
                if data_bit != crc_bit:
                    result ^= 0x8005
        return result

    def write(self, data: bytes) -> bool:
        try:
            if self._serial.write(data) != len(data):
                return False
            self._serial.flush()
            return True
        except Exception:  # noqa: BLE001
            return False

    def read_byte(self) -> int | None:
        with self._buffer_lock:
            return self._buffer.popleft() if self._buffer else None

    def available(self) -> int:
        with self._buffer_lock:
            return min(len(self._buffer), 0xFFFE)

    def pop_debug_packet(self) -> tuple[int, int, int, bytes] | None:
        with self._buffer_lock:
            return self._debug_packets.popleft() if self._debug_packets else None

    def suppress_debug_capture(self, suppressed: bool) -> None:
        with self._buffer_lock:
            self._debug_capture_suppressed = suppressed

    def recover(self) -> None:
        self.close()
        with self._buffer_lock:
            self._buffer.clear()
            self._debug_packets.clear()
            self._debug_scan.clear()
        self._open()

    def close(self) -> None:
        self._stop_reader.set()
        try:
            self._serial.cancel_read()
        except Exception:  # noqa: BLE001
            pass
        self._reader.join(timeout=1)
        if self._serial.is_open:
            self._serial.close()


def _transport_from_context(context: int) -> _PySerialTransport:
    reference = ctypes.cast(context, ctypes.POINTER(ctypes.py_object))
    return reference.contents.value


@TxCallback
def _serial_transmit(context: int, data: ctypes.POINTER(ctypes.c_uint8), size: int) -> int:
    try:
        return 0 if _transport_from_context(context).write(ctypes.string_at(data, size)) else 1
    except Exception:  # noqa: BLE001
        return 1


@RxCallback
def _serial_receive_byte(context: int, data: ctypes.POINTER(ctypes.c_uint8)) -> int:
    try:
        value = _transport_from_context(context).read_byte()
        if value is None:
            return 1
        data[0] = value
        return 0
    except Exception:  # noqa: BLE001
        return 1


@AvailableCallback
def _serial_available_bytes(context: int) -> int:
    try:
        return _transport_from_context(context).available()
    except Exception:  # noqa: BLE001
        return 0


@TimeCallback
def _serial_time_ms(context: int) -> int:
    del context
    return (monotonic_ns() // 1_000_000) & 0xFFFFFFFF


class PySerialLibrary(SerialApiLibrary):
    """SerialAPI wrapper that retains the Python callback context for each device."""

    def __init__(self) -> None:
        super().__init__(library_stem="sbgc_python_pyserial")
        self._library.sbgc_py_open.argtypes = [
            ctypes.c_void_p,
            TxCallback,
            RxCallback,
            AvailableCallback,
            TimeCallback,
        ]
        self._library.sbgc_py_open.restype = ctypes.c_void_p
        self._transports: dict[int, _PySerialTransport] = {}
        self._contexts: dict[int, ctypes.py_object] = {}

    def open(self, port: str, baudrate: int) -> int:
        if not isinstance(port, str) or not port:
            raise ValueError("Port must be a non-empty string.")
        if not 1 <= baudrate <= 0xFFFFFFFF:
            raise ValueError("Baudrate must be in range 1..4294967295")

        transport = _PySerialTransport(port, baudrate)
        context = ctypes.py_object(transport)
        context_pointer = ctypes.cast(ctypes.pointer(context), ctypes.c_void_p)
        handle = self._library.sbgc_py_open(
            context_pointer,
            _serial_transmit,
            _serial_receive_byte,
            _serial_available_bytes,
            _serial_time_ms,
        )
        if not handle:
            transport.close()
            raise NativeError(f"Cannot open {port} at {baudrate} baud.")

        device = int(handle)
        self._transports[device] = transport
        self._contexts[device] = context
        return device

    def close(self, device: int) -> None:
        try:
            super().close(device)
        finally:
            transport = self._transports.pop(device, None)
            self._contexts.pop(device, None)
            if transport is not None:
                transport.close()

    def recover(self, device: int) -> None:
        try:
            self._transports[device].recover()
        except KeyError as error:
            raise NativeError("Cannot recover a closed SimpleBGC connection.") from error
        super().recover(device)

    def read_debug_port(self, device: int) -> tuple[int, int, int, bytes, int]:
        try:
            transport = self._transports[device]
        except KeyError as error:
            raise NativeError("Cannot read Debug Port on a closed SimpleBGC connection.") from error

        packet = transport.pop_debug_packet()
        if packet is not None:
            time_ms, port_and_direction, command_id, payload = packet
            return time_ms, port_and_direction, command_id, payload, len(payload)

        # Keep a copy while the C parser receives this same record: it carries
        # the variable payload length that the vendor structure does not expose.
        result = super().read_debug_port(device)
        packet = transport.pop_debug_packet()
        if packet is None:
            return result
        time_ms, port_and_direction, command_id, payload = packet
        return time_ms, port_and_direction, command_id, payload, len(payload)


class PySerialBackend:
    """Connect SimpleBGC through pyserial on any supported operating system."""

    name = "pyserial"

    def __init__(self) -> None:
        self.library = PySerialLibrary()

    def open(self, port: str, baudrate: int) -> int:
        return self.library.open(port, baudrate)

    def close(self, device: int) -> None:
        self.library.close(device)
