""" Windows backend that opens and owns a COM port in the native C library. """

from __future__ import annotations

import sys

from .._serial_api_library import NativeError, NativeLibrary


class NativeWinBackend:
    """ Connect SimpleBGC Serial API to a Win32 COM transport. """

    name = "native_win"

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise NativeError("The native_win backend is available only on Windows.")
        self.library = NativeLibrary()

    def open(self, port: str, baudrate: int) -> int:
        return self.library.open_native(port, baudrate)

    def close(self, device: int) -> None:
        self.library.close(device)
