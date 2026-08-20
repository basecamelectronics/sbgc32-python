from sbgc32 import SimpleBGC
from sbgc32.native import NativeError
from time import sleep


def main() -> None:

    s = "COM" + input("COM port: ")
    print("Opening COM port...", flush=True)

    with SimpleBGC(port=s) as gimbal:

        print("Connection established.", flush=True)


        # CMD_BOARD_INFO

        board = gimbal.get_board_info()

        # Also you can use execute with parameters
        # board = gimbal.execute(Command.CMD_BOARD_INFO)

        print(f"Board:    {board.board_version}", flush=True)
        print(f"Firmware: {board.firmware_version}", flush=True)
        print(f"Features: 0x{board.board_features:04X}", flush=True)


        # CMD_GET_ANGLES

        sleep(0.5)
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
            print("\nStopped.", flush=True)

if __name__ == "__main__":
    main()
