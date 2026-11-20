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
**Cloning the repository or downloading its source ZIP does not include the
compiled native library.** On Windows this file is
`sbgc_python_protocol.dll`. It is included in the platform wheel from
[GitHub Releases](https://github.com/basecamelectronics/sbgc32-python/releases).
Choose one of the following installation methods before running examples.


### Run examples with a prebuilt wheel (recommended)

Download the wheel for your operating system, then
create an environment in the repository root. For Windows x64 and Pyton version 3.13:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install "C:\path\to\sbgc32-VERSION-py3-none-win_amd64.whl"
```

Replace the wheel path with the downloaded file. The wheel installs both the
Python package and DLL into `.venv\Lib\site-packages\sbgc32`. No manual DLL
copying or C++ compiler is needed. Use this environment to run the examples.

Check the installation without connecting hardware:

```powershell
.\.venv\Scripts\python.exe -c "import sbgc32; from sbgc32.protocol import ProtocolCodec; print(sbgc32.__file__); ProtocolCodec(); print('Native library: OK')"
```

Then also see `How to use the examples`.


### Develop the library from source

Build the native library first using the CMake instructions below, then run
`python -m pip install -e .` with your environment's Python. An editable install
loads `src/sbgc32` and expects the compiled DLL in `src/sbgc32/_native`.
Installing with `pip install -e .` does not compile the DLL.

### Missing DLL after cloning

If the error points to `src\sbgc32\_native\sbgc_python_protocol.dll`, Python
is loading the source package. Either build the DLL from this checkout, or
use the prebuilt-wheel environment described above.

To switch an existing environment from an editable install to a wheel:

```powershell
.\.venv\Scripts\python.exe -m pip uninstall sbgc32
.\.venv\Scripts\python.exe -m pip install "C:\path\to\sbgc32-VERSION-py3-none-win_amd64.whl"
```


### How to use the examples

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

Use example CAN_MotorTester to provides a graphical interface 
for monitoring and controlling two external motor channels. 
Download the requirements and run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\examples\CAN_MotorTester\requirements-plots.txt
.\.venv\Scripts\python.exe .\examples\CAN_MotorTester\app.py
```
For more information for this example, see README in [`examples/CAN_MotorTester/README.md`](examples/CAN_MotorTester/README.md) . 


### More about repository

Files Description
-----------

[`docs/`](docs/) - documentation;

[`examples/`](examples/) - executable examples for connecting to and testing a controller;

[`src/sbgc32/`](src/sbgc32/) - Python package: value types, command identifiers, and ctypes bindings for the DLL;

[`src/sbgc32/modules`](src/sbgc32/modules/) - modules from SerialAPI;

[`native/`](native/) - C protocol codec and its local headers;

[`pyproject.toml`](pyproject.toml) - Python package metadata and dependencies;

[`setup.py`](setup.py) - settings for create a wheel.


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

This section is for source development. Build the native DLL using the CMake
commands below **before** installing the package in editable mode. To run
examples with a ready-made DLL, use the prebuilt-wheel instructions above.

From the repository root, check Python and install the package in editable mode:

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

Rebuild the DLL after changing a source or header in `native/`.


`Bild the wheel`
-----------------------
Download `build` packet:

```powershell
py -m pip install build
```

To build the wheel, change directory to library and build it:
	
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
