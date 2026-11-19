"""Revised CAN_DRV configuration layout supplied with the updated tester."""

import struct
from dataclasses import dataclass


def _uint(value, name, maximum):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise ValueError(f"{name} must be an integer in 0..{maximum}")
    return value


@dataclass(frozen=True)
class ExternalMotorsControlConfig:
    motors: int
    data_set: int
    mode: int = 0
    default_speed: int = 0
    max_speed: int = 0
    max_acceleration: int = 0
    jerk_slope: int = 0
    max_torque: int = 0

    def encode(self, *, need_confirmation=False):
        motors = _uint(self.motors, "motors", 0x7F)
        mask = _uint(self.data_set, "data_set", 0x3F)
        if not motors or not mask:
            raise ValueError("Select at least one motor and configuration field")
        if type(need_confirmation) is not bool:
            raise TypeError("need_confirmation must be bool")
        payload = bytearray(struct.pack("<BH", motors | (0x80 if need_confirmation else 0), mask))
        if mask & 1:
            mode = _uint(self.mode, "mode", 255)
            if mode not in (0, 1, 2, 255):
                raise ValueError("mode must be Position, Speed, Torque or Restore RC")
            payload.append(mode)
        for bit, name in enumerate(("default_speed", "max_speed", "max_acceleration",
                                    "jerk_slope", "max_torque"), start=1):
            if mask & (1 << bit):
                payload.extend(struct.pack("<H", _uint(getattr(self, name), name, 65535)))
        return bytes(payload)
