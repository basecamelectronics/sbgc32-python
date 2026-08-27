SimpleBGC32 Serial API Open Source Python Library
============================================
[![Web-site](https://www.basecamelectronics.com/img/logo.basecam.onwhite.png)](https://www.basecamelectronics.com)


-----------
This project provides Python wrapper for the [SimpleBGC32 Serial API](https://github.com/basecamelectronics/sbgc32-serial-api).
It communicates with SimpleBGC controllers through a COM port 
and provides access to selected Serial API commands.

The package uses a native DLL as a bridge to the vendored C Serial API.
The bridge uses PySerial for transport and keeps Serial API structures and
packet handling inside native code.


Files Description
-----------

[`dist/`](dist/) - wheels for import. Interaction with port through native_c (only on Windows) or pyserial;

[`docs/`](docs/) - documentation;

[`examples/`](examples/) - executable examples for connecting to and testing a controller;

[`src/sbgc32/`](src/sbgc32/) - Python package: public API, value types,
command identifiers, and ctypes bindings for the DLL;

[`src/sbgc32/backend`](src/sbgc32/backend/) - backend for interaction with serial port;

[`native/`](native/) - C bridge between Python and the SimpleBGC Serial API;
`sbgc_py_transpot_win32.c` need to interact with port with native C;
`sbgc_py_transpot_pyserial.c` need to interact with port with pyserial;

[`vendor/serialAPI/`](vendor/serialAPI/) - vendored BaseCam SimpleBGC32 Serial
API C library;

[`pyproject.toml`](pyproject.toml) - Python package metadata and dependencies.

[`setup.py`](setup.py) - settings for create a wheel;


Requirements to use the library
-----------------------
- Windows 10 or Windows 11, 64-bit;
- Python 3.10 or newer, 64-bit;
- [PySerial](https://pyserial.readthedocs.io/) 3.5 or newer (installed by the
  package). If you do not use native wheel;
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
cmake -S native -B build/native -G "Visual Studio 1x 202x" -A x64
cmake --build build/native --config Release
```

The result is written to `src\sbgc32\_native\`

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
To bild the wheel, change directory with library and choose the interaction with serial:
	
```powershell
$env:SBGC32_WHEEL_BACKEND = "native_c"
python -m build --wheel --outdir dist\native_c
```
or
```powershell
$env:SBGC32_WHEEL_BACKEND = "pyserial"
python -m build --wheel --outdir dist\pyserial
```


How to use code
-----------------------
Download wheel you need. Place file to workspace.

In powershell or other cmd install wheel:
   ```powershell
   py -m pip install .\sbgc32-...name.whl
   ```
In `.py` file import library:

    ```python
    from sbgc32 import SimpleBGC
    ```
You can also see a description of command use `print(SimpleBGC.name_of_function.__doc__)` 

Documentation
-----------
Build the local documentation site:

```powershell
py -m pip install -r .\docs\requirements.txt
py -m sphinx -W --keep-going -b html .\docs\source .\docs\build\html
```

See [`docs/README.md`](docs/README.md) for details.

Feedback
-----------

If you have any questions or suggestions about using this library, you can contact at:

support@basecamelectronics.com