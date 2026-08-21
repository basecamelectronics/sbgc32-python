from .native_win import NativeWinBackend
from .pyserial import PySerialBackend


def create_backend(name: str) -> NativeWinBackend | PySerialBackend:
    """ Create the selected transport backend. """
    if name == "native_win":
        return NativeWinBackend()
    if name == "pyserial":
        return PySerialBackend()
    raise ValueError(f"Unknown SimpleBGC backend: {name!r}.")


__all__ = ["NativeWinBackend", "PySerialBackend", "create_backend"]
