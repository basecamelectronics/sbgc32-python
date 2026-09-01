"""ctypes ABI declarations shared by the native bridge.

The names are re-exported here so the ABI has one explicit import location for
new code.  ``sbgc32.native`` remains the supported compatibility import.
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
    NativeError,
    NativeRealtimeData,
    NativeScriptDebugInfo,
    NativeStatus,
)

__all__ = [name for name in globals() if name.startswith("Native")]
