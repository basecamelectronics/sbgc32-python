"""CMD_EXT_MOTORS_STATE fields in protocol order, converted for display."""

import math
import struct
from dataclasses import dataclass

STATE = struct.Struct("<Bhhhh iihhii HHHHHHHHbb")


@dataclass(frozen=True)
class TelemetryField:
    name: str
    unit: str
    scale: float = 1.0


FIELDS = (
    TelemetryField("CONTROL_MODE", "mode"),
    TelemetryField("TORQUE", "%", 100 / 32767),
    TelemetryField("TORQUE_SETPOINT", "%", 100 / 32767),
    TelemetryField("SPEED16", "rpm", 0.1220740379 / 6),
    TelemetryField("SPEED16_SETPOINT", "rpm", 0.1220740379 / 6),
    TelemetryField("SPEED32", "rpm", 30 / (math.pi * 1e6)),
    TelemetryField("SPEED32_SETPOINT", "rpm", 30 / (math.pi * 1e6)),
    TelemetryField("ANGLE16", "deg", 360 / 16384),
    TelemetryField("ANGLE16_SETPOINT", "deg", 360 / 16384),
    TelemetryField("ANGLE32", "deg", 360 / 2**20),
    TelemetryField("ANGLE32_SETPOINT", "deg", 360 / 2**20),
    TelemetryField("STATE_FLAGS", "flags"),
    TelemetryField("DEFAULT_SPEED", "rpm", 1 / 3),
    TelemetryField("MAX_SPEED", "rpm", 1 / 3),
    TelemetryField("MAX_ACCELERATION", "rpm/s", 1 / 3),
    TelemetryField("JERK_SLOPE", "ms"),
    TelemetryField("MAX_TORQUE", "%", 100 / 65535),
    TelemetryField("CURRENT", "mA"),
    TelemetryField("BATTERY_VOLTAGE", "V", 1 / 1000),
    TelemetryField("MOTOR_TEMPERATURE", "°C"),
    TelemetryField("DRIVER_TEMPERATURE", "°C"),
)


def decode_state(payload):
    if len(payload) != STATE.size:
        raise ValueError(f"Expected {STATE.size} state bytes, received {len(payload)}")
    return tuple(value * field.scale for value, field in zip(STATE.unpack(payload), FIELDS))
