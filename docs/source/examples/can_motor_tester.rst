CAN motor tester
================

``examples/CAN_MotorTester/app.py`` is a Tkinter desktop application for
monitoring and controlling two external motor channels, DRV1 and DRV2, through
the sbgc32 library.

Required hardware and software
------------------------------

* A SimpleBGC32 **Extended** controller.
* A **CAN_DRV with a connected motor and encoder**, powered and connected to
  the controller's CAN (Controller Area Network) bus.
* External motor channels assigned and configured in the SimpleBGC graphical
  configuration application. To use both channels, configure the corresponding
  driver, motor and encoder for each channel. Disable polling for an unused
  channel in the tester.
* Controller firmware supporting commands 128 through 131. The official
  specification documents these commands from firmware 2.73.0 onward;
  compatibility with the particular CAN_DRV firmware must also be checked.
* Python 3.10 or newer, Tkinter, and an installed sbgc32 package with its native
  protocol library for the operating system and architecture. PySerial 3.5 or
  newer is installed as an sbgc32 dependency.

The computer communicates with the Extended controller over a serial port;
the controller communicates with CAN_DRV over CAN. A direct computer-to-CAN
adapter is not used by this example. The default serial settings are
115200 bit/s and Serial API (Application Programming Interface) protocol v2.

See the `official Serial API specification
<https://www.basecamelectronics.com/files/SimpleBGC_2_6_Serial_Protocol_Specification.pdf>`_
for command formats, units and firmware requirements.

Installation and launch
-----------------------

Install sbgc32 using the wheel or source-build instructions in the repository
README. Use the same Python environment for installation and launch. The
example uses that installed package; it does not include a separate wheel or
require another protocol implementation.

Use the updated library from this repository: the example now uses the tuple
form of ``control_ext_motors()`` for individual motor setpoints. The original
1.1.0 wheel supplied with the tester does not support this form. For a source
installation, rebuild/install according to the main README before launching.

Check that Tkinter is available:

.. code-block:: powershell

   py -m tkinter

Close the Tkinter demonstration window, then run from the repository root:

.. code-block:: powershell

   py .\examples\CAN_MotorTester\app.py

Close other applications using the controller's serial port. Select the port
and click **Connect**. The application reads the board and firmware versions,
then begins polling the enabled channels. Polling is initially enabled for
both DRV1 and DRV2; command transmission starts only after user interaction.

Monitoring
----------

Each enabled channel requests all 20 state fields with
``CMD_EXT_MOTORS_STATE`` (131). The display includes actual and target angles,
speed and torque, motion limits, current, supply voltage, motor and driver
temperatures, motor on/off state, and the INDEX input state.

The circular indicators use ``ANGLE16`` and ``ANGLE16_SETPOINT``. The text
panel uses the higher-resolution ``ANGLE32`` fields for angles and
``SPEED32`` fields for speed.

The polling target is 50 Hz per driver. Requests are serialized and wait for
completion, so the actual rate depends on response times and other traffic.
A missing reply can delay polling of the other driver. The current library
also requests board information before each motor-state request to check CAN
support. The displayed polling target is not a measured rate.

Actions and configuration
-------------------------

Select action targets independently of the polling checkboxes. The action
buttons send ``CMD_EXT_MOTORS_ACTION`` (128):

* **Off / floating**: disable the motor and leave it floating.
* **Off / brake**: disable the motor with braking.
* **Safe stop**: request controlled deceleration followed by braking.
* **Motor on**: enable the motor.
* **Home position**: request a move to the configured home position.
* **Search home**: request a home search.

Each driver has a separate configuration panel. Check the fields to include,
enter their values, and send the configuration with
``CMD_EXT_MOTORS_CONTROL_CONFIG`` (130). Available fields are Position, Speed
or Torque mode; maximum speed; maximum acceleration; jerk slope; and maximum
torque. Maximum speed and acceleration use raw units of 2 degrees/s and
2 degrees/s squared. Jerk slope is in milliseconds; maximum torque is a
relative value from 0 to 65535.

Actions and configuration requests wait for controller confirmation. A
confirmation acknowledges the command; it does not prove that a move or home
search has finished. Failed requests are not automatically retried. These
configuration commands change runtime parameters; the application does not
issue a save-to-nonvolatile-memory command.

Periodic setpoint control
-------------------------

Select DRV1, DRV2 or both in the control panel, set the sliders, and click
**Start sending**. The application sends individual signed 16-bit setpoints
every 50 ms (a target rate of 20 Hz), using ``CMD_EXT_MOTORS_CONTROL`` (129)
with ``DATA_SET = 0``. It waits for transmission completion before queuing
another update and uses the latest slider values.

Slider values are raw protocol values. Their meaning depends on the selected
motor mode:

* Position: 16384 units per revolution.
* Speed: approximately 0.122074 degrees/s per unit.
* Torque: +/-32767 corresponds to maximum available torque.

**Home (0)** sets a slider to zero. It is different from the **Home position**
action: in Speed or Torque mode, zero means zero speed or torque. When sending
is stopped, changing a slider alone does not transmit a command.

Setpoint packets do not request controller confirmation. Successful
transmission alone does not establish that the motor reached its target.

Stopping and reconnecting
-------------------------

**Stop sending** stops periodic setpoint transmission and sends
``ExternalMotorAction.OFF_SAFE`` to the motors selected in the control panel
when the button is pressed. The request follows the last pending setpoint
transmission and asks the controller to decelerate and switch off with braking.
No further setpoints are queued. Changing the selection during this operation
does not change its targets. Restart and action buttons remain disabled while
the application waits for confirmation.

A timeout or rejection produces an explicit stop error; the application does
not claim that the motors are off and does not automatically retry. A
successful confirmation acknowledges the request, not completion of physical
deceleration. Check the motor-state telemetry for the resulting state.

To resume motion, enable the desired motors with **Motor on** and use
**Start sending**. Starting transmission alone does not enable motors.
Disconnecting or closing the window does not itself send a motor-stop command.
Stop the motors and check their state before disconnecting; behavior after
communication loss depends on device settings.

**Reset SBGC** sends a controller reset and closes the connection. Wait for
the controller to restart, then reconnect manually. Periodic control is not
automatically resumed, and queued actions or configurations are not replayed.

Implementation and current limitations
--------------------------------------

Device communication runs in a background thread. The Tkinter thread receives
updates through an event queue. Command results are checked asynchronously
through Future objects, keeping serial waits outside the interface event loop.

Setpoints use the public ``control_ext_motors()`` method with one
``ExternalMotorControl`` per selected motor, in ascending motor-ID order.
The library writes exactly one record for each selected mask bit.

Remaining limitations:

* State decoding expects the full 45-byte data block. The library removes the
  response header without checking its motor ID or data-set mask against the
  request. Sequential polling does not eliminate the risk of a delayed reply
  being attributed to another request.
* The interface supports two motor channels and 16-bit setpoints only.

Diagnostics and verification
----------------------------

The application writes connection details and raw motor-state responses to
``examples/CAN_MotorTester/motor-state.log``. Rotation keeps the current log
and up to two backups, each with a configured limit of approximately 1 MB.
The example directory must be writable for logging.

For a bounded diagnostic probe that only reads board/module information and
motor state, disconnect the application and run:

.. code-block:: powershell

   py .\examples\CAN_MotorTester\diagnose_motors.py COM8

Replace ``COM8`` with the actual controller port. For missing telemetry,
check channel assignment, power, CAN wiring and device firmware, then inspect
the log or diagnostic output.

Run the example's tests without hardware from the repository root:

.. code-block:: powershell

   py -m unittest discover -s .\examples\CAN_MotorTester -p "test_motor_*.py" -v

These tests use simulated device responses. They check payload construction,
state decoding, scheduling, stop ordering and confirmation/error handling.
Library packet regression tests are in ``tests/test_ext_motors_control.py``.
They do not establish
operation on a physical Extended + CAN_DRV setup or guarantee a polling rate.
