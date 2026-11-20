## CAN motor tester

The `examples/CAN_MotorTester` application provides a graphical interface for monitoring and controlling two external motor channels.

### Requirements

- A **SimpleBGC32 Extended controller**.
- A **CAN_DRV with a connected motor and encoder**, powered and connected to the controller’s CAN bus;
- External motor channels configured in the SimpleBGC configuration application;
- Compatible controller and CAN_DRV firmware;
- Python 3.10 or newer with Tkinter;
- The sbgc32 library version 1.2.0 or newer.

For two-channel operation, connect and configure the corresponding driver, 
motor and encoder for each channel. Disable polling for unused channels.

### Start

First follow the [installation instructions](../../README.md#how-to-use-code).
The prebuilt wheel includes the native DLL; a source checkout needs a CMake build.

Close other applications using the controller’s serial port. From the repository root, run:

```powershell
.\.venv\Scripts\python.exe .\examples\CAN_MotorTester\app.py
```

Select the serial port and click **Connect**. Then enable Poll DRV1/DRV2 for the connected drivers.

### Features

- Monitor DRV1 and DRV2: angles, speed, torque, current, voltage, temperatures and motor status.
- Configure Position, Speed and Torque modes, default speed, maximum speed, acceleration, jerk slope and torque.
- Enable motors, brake, perform a safe stop and request home positioning or a home search.
- Send independent setpoints to each motor.
- Restore saved RC control with **Restore RC (255)**.
- Display selected telemetry signals as connected lines in a separate white graph window.

The target polling rate is 50 Hz per driver. Setpoints are sent every 50 ms. Actual rates depend on device response times and communication load.

### Realtime graphs

Install the optional plotting dependencies in the same Python environment as
the tester, from the repository root:

```powershell
py -m pip install -r .\examples\CAN_MotorTester\requirements-plots.txt
```

Start the tester normally and click **Show graphs**. The Tkinter controls stay
in the main window; PyQtGraph and PySide6 run in a separate process. Connect to
the controller and enable **Poll DRV1/DRV2** to supply live telemetry. Graphs
use the existing state responses and do not open another serial connection.

- The separate graph window uses a white theme and **one shared plot**, with up to ten signals at once.
- Click **+ Add signal** on the left to add a signal row.
  Click **Remove** in a row to remove it. Removing a row does not discard telemetry history.
- For each signal, select **DRV1/DRV2** and a telemetry field from the dropdown.
  Its checkbox shows or hides the curve. Signals from both drivers and with
  different units can be combined; all use the same numerical Y scale.
  Units appear in the legend. Clicking a legend sample also toggles its curve.
- **Time window** sets a shared range from 0.1 to 300 seconds. **Follow live**
  scrolls with time. Drag/zoom a time axis to inspect history; enable Follow
  live to return to the current data.
- **Auto Y** fits the amplitude automatically. Uncheck it and set **Min/Max**
  for a fixed range, or zoom vertically with the mouse.
- **Pause display** freezes the view while acquisition continues. **Clear
  history** discards the retained samples. Neither button changes motor control.
