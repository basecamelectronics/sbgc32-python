"""External motor telemetry, using sbgc32 for all protocol requests."""

import logging

from motor_telemetry import STATE as STATE
from motor_telemetry import decode_state

DATA_SET = (1 << 21) - 1
# sbgc32 checks the response length excluding MOTOR_ID, including DATA_SET.
RESULT_SIZE = 4 + STATE.size
RESPONSE_TIMEOUT = 1.0
POLL_INTERVAL = 1 / 50
logger = logging.getLogger(__name__)


def format_state(payload):
    return format_values(decode_state(payload))


def format_values(values):
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
        default_speed,
        max_speed,
        acceleration,
        jerk,
        max_torque,
        current,
        voltage,
        motor_temp,
        driver_temp,
    ) = values
    mode, flags = int(mode), int(flags)
    modes = {0: "Position", 1: "Speed", 2: "Torque"}
    states = ("Off / brake", "On", "Off / floating", "Off / safe stop")
    return (
        f"{modes.get(mode, f'Unknown ({mode})')} | {states[flags & 3]} | Index: {bool(flags & 4)}\n"
        f"Angle: {angle:.2f}° | Target: {angle_target:.2f}°\n"
        f"Speed: {speed:.2f} rpm | Target: {speed_target:.2f} rpm\n"
        f"Torque: {torque:.1f}% | Target: {torque_target:.1f}%\n"
        f"Default speed: {default_speed:.2f} rpm\n"
        f"Limits: {max_speed:.2f} rpm, {acceleration:.2f} rpm/s, torque {max_torque:.1f}% | Jerk: {jerk:g} ms\n"
        f"Current: {current:g} mA | Voltage: {voltage:.2f} V\n"
        f"Temperature: motor {motor_temp:g}°C / driver {driver_temp:g}°C"
    )


def angles16(payload):
    values = decode_state(payload)
    return values[7], values[8]


class MotorReader:
    """Serialize state requests: library matches replies by command, not motor ID."""

    def __init__(self, device, enabled, emit, sample_emit=None):
        self.device = device
        self.enabled = enabled
        self.due = [0.0, 0.0]
        self.emit = emit
        self.pending = None
        self.sample_emit = sample_emit

    def tick(self, now):
        if self.pending is not None:
            index, future = self.pending
            if not future.done():
                return
            self.pending = None
            actual = target = flags = None
            values = None
            try:
                payload = future.result()
                values = decode_state(payload)
                message = format_values(values)
                actual, target = values[7:9]
                flags = int(values[11])
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
                if self.sample_emit is not None:
                    self.sample_emit(index, now, values)
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
            if self.sample_emit is not None:
                self.sample_emit(index, now, None)
            self.emit(
                (
                    "motor",
                    (index, f"Unavailable — {type(error).__name__}: {error}", None, None, None),
                )
            )
