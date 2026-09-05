"""ctypes ABI declarations shared by the native bridge.

The names are re-exported here so the ABI has one explicit import location for
new code.  ``sbgc32.native`` remains the supported compatibility import.
"""

from . import _serial_api_library

__all__ = tuple(name for name in dir(_serial_api_library) if name.startswith("Native"))
globals().update({name: getattr(_serial_api_library, name) for name in __all__})
