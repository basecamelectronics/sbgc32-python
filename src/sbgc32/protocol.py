from __future__ import annotations

import ctypes
import sys
from dataclasses import dataclass
from pathlib import Path

_MAX_PAYLOAD = 255
_PROTOCOL_V1 = 1
_PROTOCOL_V2 = 2


class ProtocolError(RuntimeError):
    """Raised when the C protocol codec rejects an operation."""


class _NativeWireFrame(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("protocol_version", ctypes.c_uint8),
        ("command_id", ctypes.c_uint8),
        ("payload_size", ctypes.c_uint8),
        ("payload", ctypes.c_uint8 * _MAX_PAYLOAD),
    ]


class _NativeParser(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("protocol_version", ctypes.c_uint8),
        ("state", ctypes.c_uint8),
        ("header", ctypes.c_uint8 * 3),
        ("trailer", ctypes.c_uint8 * 2),
        ("payload", ctypes.c_uint8 * _MAX_PAYLOAD),
        ("buffered_size", ctypes.c_uint16),
        ("expected_size", ctypes.c_uint16),
    ]


@dataclass(frozen=True, slots=True)
class WireFrame:
    """A validated frame received from the controller."""

    protocol_version: int
    command_id: int
    payload: bytes


def _default_library_path() -> Path:
    filename = {
        "win32": "sbgc_python_protocol.dll",
        "darwin": "libsbgc_python_protocol.dylib",
    }.get(sys.platform, "libsbgc_python_protocol.so")
    return Path(__file__).with_name("_native") / filename


class ProtocolCodec:
    """C-backed, incremental encoder and parser for one SerialAPI port."""

    def __init__(self, protocol_version: int = _PROTOCOL_V2, *, library_path: Path | None = None):
        if protocol_version not in (_PROTOCOL_V1, _PROTOCOL_V2):
            raise ValueError("protocol_version must be 1 or 2")

        path = _default_library_path() if library_path is None else Path(library_path)
        if not path.is_file():
            raise ProtocolError(f"Protocol codec DLL was not found: {path}")

        self._library = ctypes.CDLL(str(path))
        self._configure_abi()
        self.protocol_version = protocol_version
        self._parser = _NativeParser()
        self._library.sbgc_py_protocol_parser_init(ctypes.byref(self._parser), protocol_version)

    def _configure_abi(self) -> None:
        library = self._library

        library.sbgc_py_protocol_parser_init.argtypes = [
            ctypes.POINTER(_NativeParser),
            ctypes.c_uint8,
        ]
        library.sbgc_py_protocol_parser_init.restype = None

        library.sbgc_py_protocol_reset_reading.argtypes = [ctypes.POINTER(_NativeParser)]
        library.sbgc_py_protocol_reset_reading.restype = None

        library.sbgc_py_protocol_encode.argtypes = [
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        library.sbgc_py_protocol_encode.restype = ctypes.c_int

        library.sbgc_py_protocol_parser_feed.argtypes = [
            ctypes.POINTER(_NativeParser),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(_NativeWireFrame),
            ctypes.POINTER(ctypes.c_uint8),
        ]
        library.sbgc_py_protocol_parser_feed.restype = ctypes.c_int

    def reset(self) -> None:
        """Discard a partial frame after reconnecting or a transport fault."""

        self._library.sbgc_py_protocol_reset_reading(ctypes.byref(self._parser))

    def encode(self, command_id: int, payload: bytes = b"") -> bytes:
        """Build one full wire frame, including framing checksums."""

        if not 1 <= command_id <= 255:
            raise ValueError("command_id must be in range 1..255")

        if len(payload) > _MAX_PAYLOAD:
            raise ValueError("payload cannot exceed 255 bytes")

        payload_buffer = None
        payload_pointer = None
        if payload:
            payload_buffer = (ctypes.c_uint8 * len(payload)).from_buffer_copy(payload)
            payload_pointer = ctypes.cast(payload_buffer, ctypes.POINTER(ctypes.c_uint8))

        output = (ctypes.c_uint8 * (len(payload) + 6))()
        output_size = ctypes.c_size_t()
        status = self._library.sbgc_py_protocol_encode(
            self.protocol_version,
            command_id,
            payload_pointer,
            len(payload),
            output,
            len(output),
            ctypes.byref(output_size),
        )
        self._raise_for_status(status, "encode frame")
        return bytes(output[: output_size.value])

    def feed(self, data: bytes) -> tuple[WireFrame, ...]:
        """Consume arbitrary received bytes and return every complete frame."""
        if not data:
            return ()

        source = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
        offset = 0
        frames: list[WireFrame] = []

        while offset < len(data):
            consumed = ctypes.c_size_t()
            ready = ctypes.c_uint8()
            native_frame = _NativeWireFrame()
            pointer = ctypes.cast(ctypes.byref(source, offset), ctypes.POINTER(ctypes.c_uint8))
            status = self._library.sbgc_py_protocol_parser_feed(
                ctypes.byref(self._parser),
                pointer,
                len(data) - offset,
                ctypes.byref(consumed),
                ctypes.byref(native_frame),
                ctypes.byref(ready),
            )
            self._raise_for_status(status, "parse received bytes")

            if consumed.value == 0:
                raise ProtocolError("Protocol parser made no progress")
            offset += consumed.value

            if ready.value:
                frames.append(
                    WireFrame(
                        protocol_version=native_frame.protocol_version,
                        command_id=native_frame.command_id,
                        payload=bytes(native_frame.payload[: native_frame.payload_size]),
                    )
                )

        return tuple(frames)

    @staticmethod
    def _raise_for_status(status: int, operation: str) -> None:
        if status == 0:
            return
        messages = {
            -1: "invalid argument",
            -2: "unsupported protocol version",
            -3: "output buffer is too small",
        }
        raise ProtocolError(f"Cannot {operation}: {messages.get(status, f'error {status}')}")
