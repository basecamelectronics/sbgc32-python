CAN motor tester
================

``examples/CAN_MotorTester/app.py`` monitors and controls CAN_DRV motors
connected to a SimpleBGC32 Extended controller.

Features
--------

* Read angles, speed, torque, current, voltage, temperatures and motor status
  for DRV1 and DRV2.
* Configure Position, Speed or Torque mode, default speed, maximum speed,
  acceleration, jerk slope and torque. Restore saved RC control with
  **Restore RC (255)**.
* Send independent motor setpoints, enable motors, brake, stop and search home.
* View selected telemetry signals as connected lines in a separate white graph
  window, with zoom, time range, pause and history controls.

Start
-----

Connect CAN_DRV, motor and encoder to the controller and configure the external
motor channel in the SimpleBGC GUI. Connect the controller to the computer by USB.

With Python and sbgc32 installed, run these commands from the project folder:

.. code-block:: powershell

   .\.venv\Scripts\python.exe -m pip install -r .\examples\CAN_MotorTester\requirements-plots.txt
   .\.venv\Scripts\python.exe .\examples\CAN_MotorTester\app.py

Select the COM port, click **Connect**, and enable **Poll DRV1/DRV2** for the
connected drivers.

Use the configuration panel to select a mode and set parameters, then click
**Send DRV1/DRV2 config**. Speed is entered in rpm and acceleration in rpm/s.
Select the motor, click **Motor on**, set its slider and click **Start sending**.
**Stop sending** requests a safe stop. **Restore RC (255)** returns control to
the saved RC configuration after setpoint sending has been stopped.

Graphs
------

Click **Show graphs**, then **+ Add signal** to add a signal.
Choose the driver and parameter in each row. **Remove** removes a row.

Use **Time window** for the visible interval, **Follow live** for automatic
scrolling and **Auto Y** for vertical scaling. **Pause display** freezes the
view; **Clear history** clears recorded samples.
