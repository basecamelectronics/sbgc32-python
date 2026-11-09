"""External motor telemetry, using sbgc32 for all protocol requests."""

import logging
import math
import struct

DATA_SET = (1 << 20) - 1
# Fields in DATA_SET bit order (Serial API specification, pages 50–51).
STATE = struct.Struct("<Bhhhh iihhii HHHHHHHbb")
# sbgc32 checks the response length excluding MOTOR_ID, including DATA_SET.
RESULT_SIZE = 4 + STATE.size
RESPONSE_TIMEOUT = 1.0
POLL_INTERVAL = 1 / 50
logger = logging.getLogger(__name__)


def format_state(payload):
    if len(payload) != STATE.size:
        raise ValueError(f"Expected {STATE.size} state bytes, received {len(payload)}")
    (
        mode,
        torque,
        torque_target,
        speed16,
        speed16_target,
        speed,
        speed_target,
        angle16,
        angle16_target,
        angle,
        angle_target,
        flags,
        max_speed,
        acceleration,
        jerk,
        max_torque,
        current,
        voltage,
        motor_temp,
        driver_temp,
    ) = STATE.unpack(payload)
    modes = {0: "Position", 1: "Speed", 2: "Torque"}
    states = ("Off / brake", "On", "Off / floating", "Off / safe stop")
    return (
        f"{modes.get(mode, f'Unknown ({mode})')} | {states[flags & 3]} | Index: {bool(flags & 4)}\n"
        f"Angle: {angle * 360 / 2**20:.2f}° | Target: {angle_target * 360 / 2**20:.2f}°\n"
        f"Speed: {math.degrees(speed / 1e6):.2f}°/s | Target: {math.degrees(speed_target / 1e6):.2f}°/s\n"
        f"Torque: {torque / 32767:.1%} | Target: {torque_target / 32767:.1%}\n"
        f"Limits: {max_speed * 2}°/s, {acceleration * 2}°/s², torque {max_torque / 65535:.1%} | Jerk: {jerk} ms\n"
        f"Current: {current} mA | Voltage: {voltage / 1000:.2f} V\n"
        f"Temperature: motor {motor_temp}°C / driver {driver_temp}°C"
    )


def angles16(payload):
    if len(payload) != STATE.size:
        raise ValueError(f"Expected {STATE.size} state bytes, received {len(payload)}")
    values = STATE.unpack(payload)
    return values[7] * 360 / 16384, values[8] * 360 / 16384


class MotorReader:
    """Serialize state requests: library matches replies by command, not motor ID."""

    def __init__(self, device, enabled, emit):
        self.device = device
        self.enabled = enabled
        self.due = [0.0, 0.0]
        self.emit = emit
        self.pending = None

    def tick(self, now):
        if self.pending is not None:
            index, future = self.pending
            if not future.done():
                return
            self.pending = None
            actual = target = flags = None
            try:
                payload = future.result()
                message = format_state(payload)
                actual, target = angles16(payload)
                flags = STATE.unpack(payload)[11]
            except Exception as error:
                logger.warning("DRV%d state failed: %s: %s", index + 1, type(error).__name__, error)
                if isinstance(error, TimeoutError):
                    message = (
                        f"No state reply within {RESPONSE_TIMEOUT:g} s (mask 0x{1 << index:02X}).\n"
                        "Check auxiliary motor assignment in SimpleBGC GUI.\n"
                        "See motor-state.log for request details."
                    )
                else:
                    message = f"Unavailable — {type(error).__name__}: {error}"
            if self.enabled[index].is_set():
                self.emit(("motor", (index, message, actual, target, flags)))
        ready = [i for i in range(2) if self.enabled[i].is_set() and now >= self.due[i]]
        if not ready:
            return
        index = min(ready, key=lambda i: self.due[i])
        self.due[index] = now + POLL_INTERVAL
        try:
            logger.info(
                "Request DRV%d: CMD=131 mask=0x%02X data_set=0x%08X result_size=%d timeout=%.1fs",
                index + 1,
                1 << index,
                DATA_SET,
                RESULT_SIZE,
                RESPONSE_TIMEOUT,
            )
            future = self.device.request_motor_state(
                1 << index, DATA_SET, RESULT_SIZE, timeout=RESPONSE_TIMEOUT
            )
            self.pending = (index, future)
        except Exception as error:
            self.emit(
                (
                    "motor",
                    (index, f"Unavailable — {type(error).__name__}: {error}", None, None, None),
                )
            )
