"""ctypes ABI declarations shared by the native bridge.

The names are re-exported here so the ABI has one explicit import location for
new code.  ``sbgc32.native`` remains the supported compatibility import.
"""

from ._native_library import (
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
    NativeRealtimeData,
    NativeScriptDebugInfo,
    NativeStatus,
)

__all__ = [name for name in globals() if name.startswith("Native")]
