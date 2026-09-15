"""Asynchronous EEPROM, I²C-register and internal-file commands."""

from __future__ import annotations

import struct
from concurrent.futures import Future
from typing import TYPE_CHECKING

from ..commands import Command
from ..protocol import WireFrame
from ..types import CommandConfirmation, EepromFile, EepromFileId
from .realtime import decode_confirmation

if TYPE_CHECKING:
    from ..device import SimpleBGC


_EEPROM_PAGE_SIZE = 64
_EEPROM_MAX_ADDRESS = 32767
_EEPROM_MAX_TRANSFER = 192
_EXTERNAL_DATA_SIZE = 128
_FILE_MAX_TRANSFER = 240


def _uint(value: object, name: str, maximum: int) -> int:
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(f"{name} must be an integer in range 0..{maximum}")
    return value


def _bytes(value: object, name: str, minimum: int, maximum: int) -> bytes:
    if not isinstance(value, bytes):
        raise TypeError(f"{name} must be bytes")
    if not minimum <= len(value) <= maximum:
        raise ValueError(f"{name} must contain from {minimum} to {maximum} bytes")
    return value


def _confirmation(value: object) -> bool:
    if type(value) is not bool:
        raise TypeError("need_confirmation must be bool")
    return value


def _eeprom_request(address: object, size: object) -> tuple[int, int]:
    address = _uint(address, "address", _EEPROM_MAX_ADDRESS)
    size = _uint(size, "size", _EEPROM_MAX_TRANSFER)
    if address % _EEPROM_PAGE_SIZE:
        raise ValueError("address must be aligned to 64 bytes")
    if size < _EEPROM_PAGE_SIZE or address + size > _EEPROM_MAX_ADDRESS + 1:
        raise ValueError("EEPROM request is outside the available address range")
    return address, size


def _file_id(value: EepromFileId | int) -> int:
    if isinstance(value, bool):
        raise ValueError("file_id must be an integer in range 0..65535")
    return _uint(int(value), "file_id", 0xFFFF)


def _decode_exact(frame: WireFrame, size: int, name: str) -> bytes:
    if len(frame.payload) != size:
        raise ValueError(f"{name} response must contain {size} bytes, got {len(frame.payload)}")
    return frame.payload


def read_i2c_register(
    self: SimpleBGC,
    device_address: int,
    register_address: int,
    size: int,
    *,
    timeout: float | None = 1.0,
) -> Future[bytes]:
    """Read bytes from a one-byte-addressed device on the controller I²C bus."""

    size = _uint(size, "size", _FILE_MAX_TRANSFER)
    if size == 0:
        raise ValueError("size must be positive")
    payload = bytes(
        (
            _uint(device_address, "device_address", 0xFF),
            _uint(register_address, "register_address", 0xFF),
            size,
        )
    )
    return self.request_raw(
        int(Command.CMD_I2C_READ_REG_BUF),
        payload,
        timeout=timeout,
        route="eeprom",
        decoder=lambda frame: _decode_exact(frame, size, "I2C_READ_REG_BUF"),
    )


def write_i2c_register(
    self: SimpleBGC,
    device_address: int,
    register_address: int,
    data: bytes,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Write bytes to a one-byte-addressed I²C device."""

    payload = bytes(
        (
            _uint(device_address, "device_address", 0xFF),
            _uint(register_address, "register_address", 0xFF),
        )
    ) + _bytes(data, "data", 1, _FILE_MAX_TRANSFER)
    if _confirmation(need_confirmation):
        return self.request_raw(
            int(Command.CMD_I2C_WRITE_REG_BUF),
            payload,
            timeout=timeout,
            route="eeprom",
            decoder=decode_confirmation,
        )
    return self.send_raw(int(Command.CMD_I2C_WRITE_REG_BUF), payload, route="eeprom")


def _decode_eeprom(address: int, size: int, frame: WireFrame) -> bytes:
    payload = _decode_exact(frame, 4 + size, "EEPROM_READ")
    received_address = struct.unpack_from("<I", payload)[0]
    if received_address != address:
        raise ValueError("EEPROM_READ response address does not match the request")
    return payload[4:]


def read_eeprom(
    self: SimpleBGC,
    address: int,
    size: int = _EEPROM_PAGE_SIZE,
    *,
    timeout: float | None = 1.0,
) -> Future[bytes]:
    """Read one or more 64-byte-aligned pages from internal EEPROM."""

    address, size = _eeprom_request(address, size)
    return self.request_raw(
        int(Command.CMD_EEPROM_READ),
        struct.pack("<IH", address, size),
        timeout=timeout,
        route="eeprom",
        decoder=lambda frame: _decode_eeprom(address, size, frame),
    )


def write_eeprom(
    self: SimpleBGC,
    address: int,
    data: bytes,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Write aligned EEPROM data. Incorrect addresses can damage settings."""

    data = _bytes(data, "data", _EEPROM_PAGE_SIZE, _EEPROM_MAX_TRANSFER)
    address, _ = _eeprom_request(address, len(data))
    payload = struct.pack("<I", address) + data
    if _confirmation(need_confirmation):
        return self.request_raw(
            int(Command.CMD_EEPROM_WRITE),
            payload,
            timeout=timeout,
            route="eeprom",
            decoder=decode_confirmation,
        )
    return self.send_raw(int(Command.CMD_EEPROM_WRITE), payload, route="eeprom")


def read_external_data(self: SimpleBGC, *, timeout: float | None = 1.0) -> Future[bytes]:
    """Read the dedicated 128-byte user-data area."""

    return self.request_raw(
        int(Command.CMD_READ_EXTERNAL_DATA),
        timeout=timeout,
        route="eeprom",
        decoder=lambda frame: _decode_exact(frame, _EXTERNAL_DATA_SIZE, "READ_EXTERNAL_DATA"),
    )


def write_external_data(
    self: SimpleBGC,
    data: bytes,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Replace the dedicated 128-byte user-data area."""

    payload = _bytes(data, "data", _EXTERNAL_DATA_SIZE, _EXTERNAL_DATA_SIZE)
    if _confirmation(need_confirmation):
        return self.request_raw(
            int(Command.CMD_WRITE_EXTERNAL_DATA),
            payload,
            timeout=timeout,
            route="eeprom",
            decoder=decode_confirmation,
        )
    return self.send_raw(int(Command.CMD_WRITE_EXTERNAL_DATA), payload, route="eeprom")


def _decode_file(file_id: int, frame: WireFrame) -> EepromFile:
    if len(frame.payload) < 5:
        raise ValueError("READ_FILE response must contain at least five bytes")
    file_size, page_offset = struct.unpack_from("<HH", frame.payload)
    if file_size > _FILE_MAX_TRANSFER or len(frame.payload) != file_size + 5:
        raise ValueError("READ_FILE response has an invalid file size")
    return EepromFile(file_id, page_offset, frame.payload[4:-1], frame.payload[-1])


def read_file(
    self: SimpleBGC,
    file_id: EepromFileId | int,
    page_offset: int = 0,
    max_size: int = _FILE_MAX_TRANSFER,
    *,
    timeout: float | None = 1.0,
) -> Future[EepromFile]:
    """Read up to 240 bytes of one internal filesystem file."""

    selected_file_id = _file_id(file_id)
    max_size = _uint(max_size, "max_size", _FILE_MAX_TRANSFER)
    if max_size == 0:
        raise ValueError("max_size must be positive")
    payload = struct.pack(
        "<3H14s",
        selected_file_id,
        _uint(page_offset, "page_offset", 0xFFFF),
        max_size,
        b"\x00" * 14,
    )
    return self.request_raw(
        int(Command.CMD_READ_FILE),
        payload,
        timeout=timeout,
        route="eeprom",
        decoder=lambda frame: _decode_file(selected_file_id, frame),
    )


def write_file(
    self: SimpleBGC,
    file_id: EepromFileId | int,
    data: bytes,
    *,
    page_offset: int = 0,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Write a chunk of an internal filesystem file."""

    selected_file_id = _file_id(file_id)
    data = _bytes(data, "data", 1, _FILE_MAX_TRANSFER)
    payload = (
        struct.pack("<3H", selected_file_id, len(data), _uint(page_offset, "page_offset", 0xFFFF))
        + data
    )
    if _confirmation(need_confirmation):
        return self.request_raw(
            int(Command.CMD_WRITE_FILE),
            payload,
            timeout=timeout,
            route="eeprom",
            decoder=decode_confirmation,
        )
    return self.send_raw(int(Command.CMD_WRITE_FILE), payload, route="eeprom")


def clear_file_system(self: SimpleBGC, *, confirm: bool = False) -> Future[None]:
    """Erase the internal filesystem after an explicit destructive-action opt-in."""

    if confirm is not True:
        raise ValueError("clear_file_system requires confirm=True")
    return self.send_raw(int(Command.CMD_FS_CLEAR_ALL), route="eeprom")
