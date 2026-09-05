from time import sleep

from sbgc32 import (
    ControlAxis,
    ControlMode,
    MotorsOffMode,
    SimpleBGC,
)

"""\
Turn the yaw axis by +35 degrees, then safely switch the motors off.

Requires firmware 2.70b7 or newer for ControlMode.ANGLE_SHORTEST.
Run this example only when the camera and gimbal have a clear workspace.
"""

TURN_DEGREES = 35.0
YAW_SPEED_DEGREES_PER_SECOND = 35.0

disable = ControlAxis(mode=ControlMode.IGNORE)


def normalize_degrees(angle: float) -> float:
    """Return an equivalent Euler angle in the [-180, 180) range."""
    return (angle + 180.0) % 360.0 - 180.0


def main() -> None:
    port = "COM" + input("COM port number: ")

    with SimpleBGC(port=port, backend="pyserial") as gimbal:
        print("Connection established.", flush=True)

        print("WARNING: this example moves the yaw axis. Keep the workspace clear.")
        input("Press Enter to enable the motors and start the movement. ")

        gimbal.motors_on()

        try:
            # Turn yaw on absolute angle.

            start_yaw = gimbal.get_angles().imu.yaw
            target_yaw = normalize_degrees(start_yaw + TURN_DEGREES)

            gimbal.control(
                (
                    disable,
                    disable,
                    ControlAxis(
                        mode=ControlMode.ANGLE,
                        angle=target_yaw,
                        speed=YAW_SPEED_DEGREES_PER_SECOND,
                    ),
                )
            )

            print(f"Yaw target: {start_yaw:.1f}° -> {target_yaw:.1f}°")
            print("The controller will use the shortest permitted path.")

            sleep(0.5)
            input("Press Enter to switch the motors off. ")

        finally:
            gimbal.motors_off(MotorsOffMode.SAFE_STOP)
            print("Motors switched off.")


if __name__ == "__main__":
    main()
