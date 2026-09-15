from time import sleep

from sbgc32 import SimpleBGC


def main() -> None:

    s = "COM" + input("COM port: ")
    print("Opening COM port...", flush=True)

    with SimpleBGC(
        port=s,
    ) as gimbal:
        print("Connection established.", flush=True)

        # CMD_BOARD_INFO
        board = gimbal.get_board_info()

        print(f"Board:    {board.result().board_version}", flush=True)
        print(f"Firmware: {board.result().firmware_version}", flush=True)

        # You can also use 'format_*' function for convenient view.
        # print(gimbal.format.format_board_info(board.result()))

        # CMD_GET_ANGLES
        try:
            while True:
                angles = gimbal.get_angles().result()
                print(gimbal.format.angles(angles), flush=True)

                sleep(0.5)

        except KeyboardInterrupt:
            print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()
