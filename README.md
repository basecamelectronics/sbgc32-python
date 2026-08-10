SimpleBGC32 Serial API Open Source Python Library
============================================
[![Web-site](https://www.basecamelectronics.com/img/logo.basecam.onwhite.png)](https://www.basecamelectronics.com)

Description
-----------
Python bindings for the BaseCam SimpleBGC32 Serial API. The package opens a
SimpleBGC controller through a Windows COM port and exposes selected protocol
commands through a small Python interface.

Files Description
-----------------


Requirements
------------

- Windows 10 or Windows 11, 64-bit
- Python 3.10 or newer, 64-bit
- `pyserial` 3.5 or newer
- CMake 3.21 or newer
- Visual Studio Build Tools 2022 with:
  - **Desktop development with C++** workload
  - MSVC v143 compiler toolset
  - Windows 10 or Windows 11 SDK

Set up Python
-----------------------
Check the Python version:

```powershell
python --version
```

If `pip` is not installed, install the copy bundled with Python, then verify
it:

```powershell
python -m ensurepip --upgrade
python -m pip --version
```

Update `pip` and install this project from the repository root. This command
also installs the required `pyserial` dependency:

```powershell
python -m pip install --upgrade pip
python -m pip install -e .
```

To list the available serial ports:

```powershell
python -m serial.tools.list_ports
```

Build the native DLL
-----------------------
Before rebuilding, stop any Python scripts and PyCharm debug sessions that use
the library. Windows cannot replace a DLL while it is loaded by a running
process.

From the repository root, run:

```powershell
cmake -S native -B build/native -A x64
cmake --build build/native --config Release
```

The resulting DLL is written to:

```text
src/sbgc32/_native/sbgc_python.dll
```

You do not need to delete this file before rebuilding, CMake overwrites it.
**Warning!** Rebuild the DLL whenever you change native code or a non-Python Serial API
file, for example `vendor/serialAPI/serialAPI_Config.h`.

To use certain functions, set ON necessary moduls in `serialAPI_Config.h`. For example,
for function `get_board_info()` require `SBGC_SERVICE_MODULE = sbgcON` . If it is disabled, the DLL
still builds. These Python methods raise `NativeError` explaining that the module is disabled.

How to use this library
-----------------------
1. Connect the controller.
2. Close any other application using its COM port, such as a serial terminal.
3. Open `examples/QuickStart.py` and set the correct port and baud rate, for
   example `COM4` and `115200`.
4. Run:

```powershell
python examples\QuickStart.py
```

The Quick Start command order is deliberate: it calls `CMD_BOARD_INFO` once to
check the controller and then repeatedly calls `CMD_GET_ANGLES` to read its
current state.

Feedback
--------

If you have any questions or suggestions about using this library, you can contact at:

support@basecamelectronics.com
