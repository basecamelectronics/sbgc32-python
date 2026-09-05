from __future__ import annotations

from ._control import make_confirmation
from .types import CommandConfirmation, EepromFile, EepromFileId

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


def read_i2c_register(self, device_address: int, register_address: int, size: int) -> bytes:
    self._ensure_open()
    size = _uint(size, "size", _FILE_MAX_TRANSFER)
    if size == 0:
        raise ValueError("size must be positive")
    return self._native.read_i2c_reg(
        self._device,
        _uint(device_address, "device_address", 0xFF),
        _uint(register_address, "register_address", 0xFF),
        size,
    )


def write_i2c_register(
    self,
    device_address: int,
    register_address: int,
    data: bytes,
    *,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()
    return make_confirmation(
        self._native.write_i2c_reg(
            self._device,
            _uint(device_address, "device_address", 0xFF),
            _uint(register_address, "register_address", 0xFF),
            _bytes(data, "data", 1, _FILE_MAX_TRANSFER),
            need_confirmation=_confirmation(need_confirmation),
        )
    )


def read_eeprom(self, address: int, size: int = _EEPROM_PAGE_SIZE) -> bytes:
    self._ensure_open()
    address, size = _eeprom_request(address, size)
    return self._native.read_eeprom(self._device, address, size)


def write_eeprom(
    self,
    address: int,
    data: bytes,
    *,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()
    data = _bytes(data, "data", _EEPROM_PAGE_SIZE, _EEPROM_MAX_TRANSFER)
    address, _ = _eeprom_request(address, len(data))
    return make_confirmation(
        self._native.write_eeprom(
            self._device,
            address,
            data,
            need_confirmation=_confirmation(need_confirmation),
        )
    )


def read_external_data(self) -> bytes:
    self._ensure_open()
    return self._native.read_external_data(self._device)


def write_external_data(
    self,
    data: bytes,
    *,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()
    return make_confirmation(
        self._native.write_external_data(
            self._device,
            _bytes(data, "data", _EXTERNAL_DATA_SIZE, _EXTERNAL_DATA_SIZE),
            need_confirmation=_confirmation(need_confirmation),
        )
    )


def _file_id(value: EepromFileId | int) -> int:
    return _uint(int(value), "file_id", 0xFFFF)


def read_file(
    self,
    file_id: EepromFileId | int,
    page_offset: int = 0,
    max_size: int = _FILE_MAX_TRANSFER,
) -> EepromFile:
    self._ensure_open()
    max_size = _uint(max_size, "max_size", _FILE_MAX_TRANSFER)
    if max_size == 0:
        raise ValueError("max_size must be positive")
    result = self._native.read_eeprom_file(
        self._device,
        _file_id(file_id),
        _uint(page_offset, "page_offset", 0xFFFF),
        max_size,
    )
    return EepromFile(
        file_id=_file_id(file_id),
        page_offset=result[1],
        data=result[0],
        error_code=result[2],
    )


def write_file(
    self,
    file_id: EepromFileId | int,
    data: bytes,
    *,
    page_offset: int = 0,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()
    return make_confirmation(
        self._native.write_eeprom_file(
            self._device,
            _file_id(file_id),
            _uint(page_offset, "page_offset", 0xFFFF),
            _bytes(data, "data", 1, _FILE_MAX_TRANSFER),
            need_confirmation=_confirmation(need_confirmation),
        )
    )


def clear_file_system(self, *, confirm: bool = False) -> None:
    self._ensure_open()
    if confirm is not True:
        raise ValueError("clear_file_system requires confirm=True")
    self._native.clear_file_system(self._device)
