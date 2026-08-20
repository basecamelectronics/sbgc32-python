SimpleBGC32 Serial API Open Source Python Library
============================================
[![Web-site](https://www.basecamelectronics.com/img/logo.basecam.onwhite.png)](https://www.basecamelectronics.com)

Description Change!!!
-----------
This project provides Python bindings for the [SimpleBGC32 Serial API](https://github.com/basecamelectronics/sbgc32-serial-api).
It communicates with SimpleBGC controllers through a Windows COM port and
exposes selected Serial API commands through a typed Python interface.

The package uses a small native DLL as a bridge to the vendored C Serial API.
The bridge uses PySerial for transport and keeps Serial API structures and
packet handling inside native code.

Before building the DLL, configure the required Serial API modules in
[`vendor/serialAPI/serialAPI_Config.h`](vendor/serialAPI/serialAPI_Config.h).
For example, `SBGC_SERVICE_MODULE` is required for board information, motors,
scripts, menu commands, and beeper functions; `SBGC_CONTROL_MODULE` is
required for `CMD_CONTROL`; `SBGC_ADJVAR_MODULE` is required for Adjustable
Variables.

Files Description
-----------
[`src/sbgc32/`](src/sbgc32/) - Python package: public API, value types,
command identifiers, PySerial transport, and ctypes bindings for the DLL;

[`native/`](native/) - C bridge between Python and the SimpleBGC Serial API;
`CMakeLists.txt` builds `sbgc_python.dll` from the command-specific bridge
source files;

[`vendor/serialAPI/`](vendor/serialAPI/) - vendored BaseCam SimpleBGC32 Serial
API C library and its configuration file;

[`examples/`](examples/) - executable examples for connecting to and testing a
controller;

[`docs/`](docs/) - command notes and usage examples;

[`pyproject.toml`](pyproject.toml) - Python package metadata and dependencies.

[`setuo.py`](setup.py) - settings for create a wheel;

[`dist/`](dist/) - wheels for import;

Requirements (to change the library, not wheel)
-----------------------
- Windows 10 or Windows 11, 64-bit;
- Python 3.10 or newer, 64-bit;
- [PySerial](https://pyserial.readthedocs.io/) 3.5 or newer (installed by the
  package). If you do not use native wheel;
- CMake 3.21 or newer;
- Visual Studio Build Tools 2022 with:
  - **Desktop development with C++** workload;
  - MSVC v143 C++ x64/x86 build tools;
  - Windows 10 SDK or Windows 11 SDK.

Install the Python package
-----------------------
All commands below use `py`, the standard Windows Python Launcher. `python`
may be used instead if it points to the same Python installation.

From the repository root, check Python and install the package in editable
mode:

```powershell
py --version
py -m ensurepip --upgrade
py -m pip install --upgrade pip
py -m pip install -e .
```

Install pyserial, if it do not exist:

```python
py install pyserial
```

List available serial ports when necessary:

```powershell
py -m serial.tools.list_ports
```
How to use this library to make you wheel
-----------------------
`Build the native DLL`
-----------------------

Stop Python scripts, terminals, and IDE debug sessions that use the library.
Windows cannot replace a DLL while a running process has loaded it.

Configure and build the 64-bit DLL from the repository root:

```powershell
cmake -S native -B build/native -G "Visual Studio 17 2022" -A x64
cmake --build build/native --config Release
```

The result is written to:

```text
src\sbgc32\_native\sbgc_python.dll
```

Rebuild the DLL after changing a file in `native/` or changing a non-Python
Serial API file, especially `vendor/serialAPI/serialAPI_Config.h`.

#### CMake cannot find a C compiler

If configuration fails with:

```text
CMake Error: CMAKE_C_COMPILER not set, after EnableLanguage
```

CMake cannot find Microsoft C/C++ build tools. This is unrelated to whether
you typed `py` or `python` for Python commands.

Install or modify **Visual Studio Build Tools 2022**, select **Desktop development with C++**, 
**MSVC v143 x64/x86 tools**, and a **Windows SDK**. Then open a
new PowerShell window and remove only the failed generated configuration before
running the two CMake commands again:

```powershell
Remove-Item -Recurse -Force build\native
cmake -S native -B build/native -G "Visual Studio 17 2022" -A x64
cmake --build build/native --config Release
```

`Bild the wheel`
-----------------------
To bild the wheel, change directory with library and in cmd:
   ```powershell
   py -m build --wheel
   ```

How to use code with library (not wheel)
-----------------------
1. Connect the controller and close all other programs using its COM port;
2. Run the example:

   ```powershell
   py examples\QuickStart.py
   ```
    Or your own code;

3. Write COM port;

The Quick Start sequence first requests `CMD_BOARD_INFO` and then repeatedly
reads `CMD_GET_ANGLES`.

You can also see a description of command use `print(SimpleBGC.name_of_function.__doc__)` 


How to use code with wheel
-----------------------
Download wheel you need. Place file to workspace.

In powershell or other cmd install wheel:
   ```powershell
   py -m pip install .\sbgc32-0.2.0-...name.whl
   ```
In .py file import library:
    ```python
    from sbgc32 import SimpleBGC
    ```

Feedback
-----------

If you have any questions or suggestions about using this library, you can contact at:

support@basecamelectronics.com