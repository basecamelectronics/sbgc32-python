"""Compatibility imports for the native SimpleBGC bridge.

The implementation is private so applications keep importing this stable
module while ABI declarations and DLL handling can
evolve independently.
"""

__all__ = [name for name in globals() if name.startswith("Native")]
