"""Compatibility imports for the native SimpleBGC bridge.

The implementation is private so applications keep importing this stable
module while ABI declarations and DLL handling can
evolve independently.
"""

from ._serial_api_library import (
    NativeAdjustableVariable,
    NativeAngles,
    NativeAnglesExt,
    NativeAxis3,
    NativeAxisGAE,
    NativeAxisRealtimeData,
    NativeBoardInfo,
    NativeBoardInfo3,
    NativeConfirmation,
    NativeControlAxisConfig,
    NativeControlConfig,
    NativeError,
    NativeLibrary,
    NativeRealtimeData,
    NativeScriptDebugInfo,
    NativeStatus,
)

__all__ = [name for name in globals() if name.startswith("Native")]
