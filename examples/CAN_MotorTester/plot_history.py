"""Bounded numeric history used only by the plotting process."""

import numpy as np
from motor_telemetry import FIELDS


class PlotHistory:
    def __init__(self, capacity=15000):
        self.capacity = capacity
        self.data = np.empty((2, capacity, len(FIELDS) + 1), dtype=np.float64)
        self.clear()

    def clear(self):
        self.counts = [0, 0]
        self.positions = [0, 0]
        self.last_time = [None, None]
        self.last_sequence = [None, None]
        self.valid = [False, False]

    def _write(self, motor, timestamp, values):
        position = self.positions[motor]
        self.data[motor, position, 0] = timestamp
        self.data[motor, position, 1:] = np.nan if values is None else values
        self.positions[motor] = (position + 1) % self.capacity
        self.counts[motor] = min(self.counts[motor] + 1, self.capacity)

    def append(self, motor, timestamp, sequence, values):
        if motor not in (0, 1) or not np.isfinite(timestamp):
            raise ValueError("Invalid telemetry source or timestamp")
        if values is not None and len(values) != len(FIELDS):
            raise ValueError(f"Expected all {len(FIELDS)} telemetry fields")
        previous = self.last_time[motor]
        if previous is not None:
            if timestamp <= previous:
                return
            # Slow but successful polling still forms a continuous trace.
            # Only actual missing samples or explicit failures break the line.
            if sequence != self.last_sequence[motor] + 1:
                self._write(motor, (previous + timestamp) / 2, None)
        self._write(motor, timestamp, values)
        self.last_time[motor] = timestamp
        self.last_sequence[motor] = sequence
        self.valid[motor] = values is not None

    def snapshot(self):
        result = []
        for motor in range(2):
            count, position = self.counts[motor], self.positions[motor]
            if count < self.capacity:
                result.append(self.data[motor, :count].copy())
            else:
                result.append(
                    np.concatenate((self.data[motor, position:], self.data[motor, :position]))
                )
        return result
