## Settings of SimpleBGC
Import SimpleBGC for use: `from sbgc32 import SimpleBGC`

default: `with SimpleBGC(port="COMX") as name:`

SimpleBGC have parametrs:
- port 
- baudrate, default 115200
- startup_delay, default 1.0
- script_slot_count, default 10

You can also use CMD_NAME for command/ Import `from sbgc32 import Command` 
and write Command.CMD_NAME. For example
```python
board = gimbal.execute(Command.CMD_BOARD_INFO)
```

## CMD_BOARD_INFO
```python
board = gimbal.get_board_info()
print(f"Board:    {board.board_version}")
print(f"Firmware: {board.firmware_version}")
print(f"Features: 0x{board.board_features:04X}")
```

## CMD_BOARD_INFO_3
```python
board3 = gimbal.get_board_info_3()

print(f"Device ID:              {board3.device_id.hex().upper()}")
print(f"MCU ID:                 {board3.mcu_id.hex().upper()}")
print(f"EEPROM size:            {board3.eeprom_size} bytes")
print(f"Flash size:             {board3.flash_size_pages} pages")
print(f"Profile-set slots:      {board3.profile_set_slots}")
print(f"Current profile set:    {board3.profile_set_current}")
print(f"Script slot sizes:      {board3.script_slot_sizes}")
print(f"IMU calibration info:   {board3.imu_calib_info.hex().upper()}")
print(f"Hardware flags:         0x{board3.hardware_flags:04X}")
print(f"Extended features:      0x{board3.board_features_ext2:08X}")
print(f"CAN main current limit: {board3.can_driver_main_limit}")
print(f"CAN aux current limit:  {board3.can_driver_aux_limit}")
print(f"Adjustable variables:   {board3.adjustable_variables_total}")
```

## CMD_GET_ANGLES
Need `from time import sleep`

```python
try:
	while True:
		try:
			angles = gimbal.get_angles()
			print(
				f"IMU: roll={angles.imu.roll:7.2f}°, "
				f"pitch={angles.imu.pitch:7.2f}°, "
				f"yaw={angles.imu.yaw:7.2f}°",
				flush=True,
			)

		except NativeError as error:
			print(f"\nCommunication error: {error}", flush=True)
			sleep(1.0)
		else:
			sleep(0.5)

except KeyboardInterrupt:
	print("\nStopped.")
```

## CMD_GET_ANGLES_EXT
Need `from time import sleep`

```python
try:
	while True:
		try:
			angles = gimbal.get_angles_ext()

			roll, pitch, yaw = angles.axis_gae
			print(roll.imu_angle)
			print(roll.target_angle)
			print(roll.frame_cam_angle)
			print(roll.reserved)

		except NativeError as error:
			print(f"\nCommunication error: {error}", flush=True)
			sleep(1.0)
		else:
			sleep(0.5)

except KeyboardInterrupt:
	print("\nStopped.")
```

SerialAPI-compatible names are also available:
`angles.AxisGAE[0].IMU_Angle`
`angles.AxisGAE[0].targetAngle`
`angles.AxisGAE[0].frameCamAngle`


## CMD_RESET
```python
print("Reset the board...")

gimbal.reset(
	delay_ms=100,
	need_confirmation=True,
	restore_state=True,
	confirmation_timeout=2.0,
	startup_delay=5.0,
)

print("Board was reset")
print("firmware:", gimbal.get_board_info().firmware_version)
```

## CMD_RUN_SCRIPT 
Simple script, ypu can write it to the board in GUI:
```
CONFIG INIT_SYSTEM_ON_FINISH(0)

DELAY TIMEOUT(1)
DELAY TIMEOUT(1)
DELAY TIMEOUT(1)
```

In SimpleSBGC set the 5 in script_slot_count, if your board have not 10 slots. 
You can use this code to see slot count.
```python
b3 = gimbal.get_board_info_3()
print(f"Count of script slots: {len(b3.script_slot_sizes)}")
```

Example
```python
gimbal.run_script(slot=1, debug=True)
debug_1 = gimbal.read_script_debug_info(timeout=2.0)
debug_2 = gimbal.read_script_debug_info(timeout=2.0)
print(debug_1, debug_2)

gimbal.stop_script(slot=1)
```

## CMD_REALTIME_DATA 
Old version of CMD_REALTIME_DATA_3. For new boards use CMD_REALTIME_DATA_3.
```python
data = gimbal.get_realtime_data()

print(f"Battery: {data.bat_level / 100:.2f} V")
print(f"Active profile: {data.cur_profile}")
print(f"System error mask: 0x{data.system_error:04X}")
print(f"I2C errors: {data.i2c_error_count}")
print(f"Motor power: {data.motor_power}")
```


## CMD_REALTIME_DATA_3 
```python
data = gimbal.get_realtime_data_3()

print(f"Battery: {data.bat_level / 100:.2f} V")
print(f"Active profile: {data.cur_profile}")
print(f"System error mask: 0x{data.system_error:04X}")
print(f"I2C errors: {data.i2c_error_count}")
print(f"Motor power: {data.motor_power}")
```

## CMD_REALTIME_DATA_4
```python
data = gimbal.get_realtime_data_4()

print(f"Battery: {data.bat_level / 100:.2f} V")
print(f"Current: {data.current} mA")
print(f"IMU temperature: {data.imu_temperature} C")
print(f"Frame IMU temperature: {data.frame_imu_temperature} C")
print(f"Motor outputs: {data.motor_out}")
print(f"Calibration mode: {data.calib_mode}")
print(f"System state flags: 0x{data.system_state_flags:08X}")
```