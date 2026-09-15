SimpleBGC32 Serial API Open Source Python Library
============================================
[![Web-site](https://www.basecamelectronics.com/img/logo.basecam.onwhite.png)](https://www.basecamelectronics.com)


-----------
This project is a Python implementation of the [SimpleBGC32 Serial API](https://github.com/basecamelectronics/sbgc32-serial-api).
It communicates with SimpleBGC controllers through a COM port 
and provides access to Serial API commands.

For standard use, you need Python 3.10+ and a wheel matching your operating system.

How to use code
-----------------------
Download wheel you need from the GitHub Release or latest wheel from [`dist/`](dist/). Place file to workspace.

In powershell or other cmd install wheel:

```powershell
py -m pip install .\sbgc32-...-name.whl
```

In `.py` file import library:

```powershell
from sbgc32 import SimpleBGC
```

Use example QuickStart to print board info and angles.
Use example Motors to rotate the gimbal along the axis yaw on 35 degrees.
Use example BodeTestAutomation to analyze motors and tune PID. To use this example
with graphics, download and import numpy and matplotlib:

```powershell
pip install numpy
pip install matplotlib
```

Files Description
-----------

[`dist/`](dist/) - latest compatible wheel;

[`docs/`](docs/) - documentation;

[`examples/`](examples/) - executable examples for connecting to and testing a controller;

[`src/sbgc32/`](src/sbgc32/) - Python package: value types, command identifiers, and ctypes bindings for the DLL;

[`src/sbgc32/modules`](src/sbgc32/modules/) - modules from SerialAPI;

[`native/`](native/) - C bridge between Python and the codec SerialAPI;

[`vendor/serialAPI/`](vendor/serialAPI/) - vendored BaseCam SimpleBGC32 Serial API C library;

[`pyproject.toml`](pyproject.toml) - Python package metadata and dependencies.

[`setup.py`](setup.py) - settings for create a wheel;


Requirements to build the library by yourself
-----------------------
- Windows 10 or Windows 11, 64-bit;
- Python 3.10 or newer, 64-bit;
- [PySerial](https://pyserial.readthedocs.io/) 3.5 or newer;
- CMake 3.21 or newer;
- Visual Studio Build Tools 2022 (or newer) with:
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

```powershell
py -m pip install pyserial
```

List available serial ports when necessary:

```powershell
py -m serial.tools.list_ports
```


How to build this library by yourself to make your wheel
-----------------------
`Build the native DLL`
-----------------------

Stop Python scripts, terminals, and IDE debug sessions that use the library.
Windows cannot replace a DLL while a running process has loaded it.

Configure and build the 64-bit DLL from the repository root:

```powershell
cmake -S . -B build/native -A x64
cmake --build build/native --config Release
```

The result is written to `src\sbgc32\_native\`

Rebuild the DLL after changing a file in `native/` or in `vendor/`.

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
cmake -S . -B build/native -A x64
cmake --build build/native --config Release
```

`Bild the wheel`
-----------------------
Download `build` packet:

```powershell
py -m pip install build
```

To build the wheel, change directory with library and build it:
	
```powershell
py -m build --wheel --outdir dist
```

Documentation
-----------
Build the local documentation site:

```powershell
py -m pip install -r .\docs\requirements.txt
py -m sphinx -E -W --keep-going -b html .\docs\source .\docs\build\html
```

See [`docs/README.md`](docs/README.md) for details.

You can also see a description of command use `print(SimpleBGC.name_of_function.__doc__)` 

Feedback
-----------

If you have any questions or suggestions about using this library, you can contact at:

support@basecamelectronics.com
