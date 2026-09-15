from time import sleep

from sbgc32 import (
    ControlAxis,
    ControlMode,
    SimpleBGC,
)

"""\
Turn the yaw axis by +35 degrees, then safely switch the motors off.

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

    with SimpleBGC(port=port) as gimbal:
        print("Connection established.", flush=True)

        print("WARNING: this example moves the yaw axis. Keep the workspace clear.")
        input("Press Enter to enable the motors and start the movement. ")

        gimbal.motors_on().result()

        try:
            start_yaw = gimbal.get_angles().result().imu.yaw
            target_yaw = normalize_degrees(start_yaw + TURN_DEGREES)

            confirmation = gimbal.control(
                (
                    disable,
                    disable,
                    ControlAxis(
                        mode=ControlMode.SPEED_ANGLE,
                        angle=target_yaw,
                        speed=YAW_SPEED_DEGREES_PER_SECOND,
                    ),
                ),
                need_confirmation=True,
            ).result()

            print(confirmation)
            print(f"Yaw target: {start_yaw:.1f}° -> {target_yaw:.1f}°")

            sleep(0.5)
            input("Press Enter to switch the motors off. ")

        finally:
            gimbal.motors_off(gimbal.types.MotorsOffMode.SAFE_STOP).result()
            print("Motors switched off.")


if __name__ == "__main__":
    main()
