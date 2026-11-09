"""Bounded read-only state probe. Close other connections before running."""

import argparse
import struct

from sbgc32 import SimpleBGC


def probe(port):
    with SimpleBGC(port=port) as device:
        board = device.get_board_info().result(timeout=3)
        print(f"Board={board.board_version} Firmware={board.firmware_version}", flush=True)
        try:
            print(f"Modules: {device.request_module_list().result(timeout=3)!r}", flush=True)
        except Exception as error:
            print(f"Module list: {type(error).__name__}: {error}", flush=True)
        for mask in (1, 2):
            # Request only CONTROL_MODE first; then compare with the full set.
            for data_set in (1, 0xFFFFF):
                payload = struct.pack("<BI", mask, data_set)
                print(f"CMD=131 request={payload.hex(' ')}", flush=True)
                try:
                    frame = device.request_raw(131, payload, timeout=1).result(timeout=3)
                    print(
                        f"Reply CMD={frame.command_id} payload={frame.payload.hex(' ')}", flush=True
                    )
                except Exception as error:
                    print(f"Raw request: {type(error).__name__}: {error}", flush=True)
                try:
                    data = device.request_motor_state(mask, data_set, 255, timeout=1).result(
                        timeout=3
                    )
                    print(f"Library reply: {data!r}", flush=True)
                except Exception as error:
                    print(f"Library request: {type(error).__name__}: {error}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port", help="Controller COM port")
    probe(parser.parse_args().port)
