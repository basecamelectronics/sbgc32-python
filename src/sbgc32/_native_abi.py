"""ctypes ABI declarations shared by the native bridge.

The names are re-exported here so the ABI has one explicit import location for
new code.  ``sbgc32.native`` remains the supported compatibility import.
"""

__all__ = [name for name in globals() if name.startswith("Native")]
