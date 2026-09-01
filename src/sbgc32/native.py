"""Compatibility imports for the native SimpleBGC bridge.

The implementation is private so applications keep importing this stable
module while ABI declarations and DLL handling can
evolve independently.
"""

from ._serial_api_library import (
    NativeAdjustableVariable,
    NativeAdjustableVariableFloat,
    NativeAdjustableVariableTriggerSlot,
    NativeAdjustableVariableAnalogSlot,
    NativeAdjustableVariablesConfig,
    NativeAdjustableVariablesStateRequest,
    NativeAdjustableVariablesState,
    NativeAdjustableVariableInfo,
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
    NativeControlExtAxis,
    NativeControlExt,
    NativeControlQuat,
    NativeControlQuatConfig,
    NativeExternalMotorControl,
    NativeExternalMotorsControlConfig,
    NativeControlExtAxis,
    NativeControlExt,
    NativeControlQuat,
    NativeControlQuatConfig,
    NativeExternalMotorControl,
    NativeExternalMotorsControlConfig,
    NativeError,
    NativeLibrary,
    NativeRealtimeData,
    NativeScriptDebugInfo,
    NativeStatus,
)

__all__ = [name for name in globals() if name.startswith("Native")]
