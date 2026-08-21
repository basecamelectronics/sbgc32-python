""" Cross-platform transport that supplies SerialAPI through pyserial callbacks. """

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
    """ Reader thread and byte queue used by the native SerialAPI callbacks. """

    def __init__(self, port: str, baudrate: int) -> None:
        try:
            import serial
        except ImportError as error:
            raise NativeError("The pyserial backend requires the pyserial dependency.") from error

        self._serial_module = serial
        self._port = port
        self._baudrate = baudrate
        self._buffer: deque[int] = deque()
        self._buffer_lock = Lock()
        self._open()

    def _open(self) -> None:
        self._serial: Any = self._serial_module.Serial(
            self._port, self._baudrate, timeout=0.1, write_timeout=1,
        )
        self._stop_reader = Event()
        self._serial.reset_input_buffer()
        self._reader = Thread(target=self._read_loop, name="sbgc32-pyserial-reader", daemon=True)
        self._reader.start()

    def _read_loop(self) -> None:
        while not self._stop_reader.is_set():
            try:
                data = self._serial.read(self._serial.in_waiting or 1)
            except Exception:
                return
            if data:
                with self._buffer_lock:
                    self._buffer.extend(data)

    def write(self, data: bytes) -> bool:
        try:
            if self._serial.write(data) != len(data):
                return False
            self._serial.flush()
            return True
        except Exception:
            return False

    def read_byte(self) -> int | None:
        with self._buffer_lock:
            return self._buffer.popleft() if self._buffer else None

    def available(self) -> int:
        with self._buffer_lock:
            return min(len(self._buffer), 0xFFFE)

    def recover(self) -> None:
        self.close()
        with self._buffer_lock:
            self._buffer.clear()
        self._open()

    def close(self) -> None:
        self._stop_reader.set()
        try:
            self._serial.cancel_read()
        except Exception:
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
    except Exception:
        return 1


@RxCallback
def _serial_receive_byte(context: int, data: ctypes.POINTER(ctypes.c_uint8)) -> int:
    try:
        value = _transport_from_context(context).read_byte()
        if value is None:
            return 1
        data[0] = value
        return 0
    except Exception:
        return 1


@AvailableCallback
def _serial_available_bytes(context: int) -> int:
    try:
        return _transport_from_context(context).available()
    except Exception:
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
            ctypes.c_void_p, TxCallback, RxCallback, AvailableCallback, TimeCallback,
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


class PySerialBackend:
    """Connect SimpleBGC through pyserial on any supported operating system."""

    name = "pyserial"

    def __init__(self) -> None:
        self.library = PySerialLibrary()

    def open(self, port: str, baudrate: int) -> int:
        return self.library.open(port, baudrate)

    def close(self, device: int) -> None:
        self.library.close(device)
