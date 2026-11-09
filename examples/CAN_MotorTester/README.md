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

### Launch

Close other applications using the controller’s serial port. From the repository root, run:

```powershell
py .\examples\CAN_MotorTester\app.py
```

Select the serial port and click **Connect**. The application displays board information and starts polling the enabled motor channels.

### Features

- Display actual and target angles, speed, torque, current, voltage and temperatures.
- Monitor motor state and the INDEX input.
- Enable motors, request braking or floating mode, perform a safe stop, and request home positioning or a home search.
- Configure Position, Speed or Torque mode and motion limits.
- Send independent 16-bit setpoints to DRV1 and DRV2.
- Reset the controller and inspect communication logs.

The target polling rate is 50 Hz per driver. Setpoints are sent every 50 ms. Actual rates depend on device response times and communication load.

### Operation notes

Setpoint sliders use raw protocol values whose meaning depends on the motor mode. 
**Home (0)** sets the selected slider to zero. It does not execute the **Home position** action.

**Stop sending** stops periodic setpoint transmission and requests **Safe stop**
(`OFF_SAFE`) for the motors selected in the control panel when the button is
pressed. The request is sent after the last pending setpoint transmission and
asks the controller to decelerate the motors and switch them off with braking.
Restart and action buttons remain disabled while confirmation is pending.
A timeout or rejection is displayed as a failed stop; motors may still be
enabled. Confirmation acknowledges the request; use telemetry to check the
actual motor state. Failed stops are not automatically retried.

To resume motion after a safe stop, enable the desired motors with **Motor on**
and use **Start sending**. Starting transmission alone does not enable motors.

Disconnecting or closing the application does not send a motor-stop command. 
Stop the motors and check their state before disconnecting.

Actions and configuration changes require controller confirmation and are not automatically retried. 
After resetting the controller, reconnect manually.

Communication details are recorded in `motor-state.log` beside the application.

### Verification

The example includes tests using simulated device responses:

```powershell
py -m unittest discover -s .\examples\CAN_MotorTester -p "test_motor_*.py" -v
```

Passing these tests does not confirm operation on physical hardware. 
Verify the application with your Extended controller, CAN_DRV firmware, motor and encoder before relying on its behavior.

Detailed operation and current limitations are described in the **CAN motor tester** documentation page.
