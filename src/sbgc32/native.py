"""Compatibility imports for the native SimpleBGC bridge.

The implementation is private so applications keep importing this stable
module while ABI declarations and DLL handling can
evolve independently.
"""

from . import _native_abi

__all__ = _native_abi.__all__
globals().update({name: getattr(_native_abi, name) for name in __all__})
