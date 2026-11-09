"""Periodic SETPOINT16 control using the sbgc32 transport."""

import logging
import threading

from sbgc32 import ConfirmationStatus, ExternalMotorAction, ExternalMotorControl

logger = logging.getLogger(__name__)


class ControlSender:
    def __init__(self):
        self.lock = threading.Lock()
        self.running = False
        self.mask = 0
        self.setpoints = (0, 0)
        self.pending = None
        self.due = 0.0
        self.stop_mask = 0
        self.stop_pending = None

    def configure(self, running, mask, setpoints):
        with self.lock:
            active = bool(running and mask and not self.stop_mask)
            if active and not self.running:
                self.due = 0.0
            self.running, self.mask, self.setpoints = active, mask, tuple(setpoints)

    def request_stop(self):
        """Freeze the current targets and stop them after the last transmission."""
        with self.lock:
            if self.stop_mask or not self.running:
                return False
            self.stop_mask = self.mask
            self.running = False
            return True

    def tick(self, device, now, emit):
        with self.lock:
            try:
                if self.stop_pending is not None:
                    if not self.stop_pending.done():
                        return
                    result = self.stop_pending.result()
                    if result is None or result.status != ConfirmationStatus.RECEIVED:
                        raise ValueError(f"Safe stop not confirmed: {result!r}")
                    mask = self.stop_mask
                    self.stop_pending = None
                    self.stop_mask = 0
                    emit(
                        (
                            "control_stopped",
                            f"Safe stop confirmed for mask 0x{mask:02X}; "
                            "check motor-state telemetry for completion",
                        )
                    )
                    return
                if self.pending is not None:
                    if not self.pending.done():
                        return
                    try:
                        self.pending.result()
                    except Exception:
                        if not self.stop_mask:
                            raise
                        logger.warning(
                            "Last setpoint failed; still attempting safe stop", exc_info=True
                        )
                    self.pending = None
                if self.stop_mask:
                    self.stop_pending = device.ext_motors_action(
                        self.stop_mask,
                        ExternalMotorAction.OFF_SAFE,
                        need_confirmation=True,
                        timeout=1.0,
                    )
                    return
                if not self.running or now < self.due:
                    return
                controls = tuple(
                    ExternalMotorControl(value)
                    for i, value in enumerate(self.setpoints)
                    if self.mask & (1 << i)
                )
                self.pending = device.control_ext_motors(controls, self.mask)
                self.due = now + 0.05
            except Exception as error:
                stopping = bool(self.stop_mask)
                self.running = False
                self.pending = None
                self.stop_pending = None
                self.stop_mask = 0
                if stopping:
                    emit(
                        (
                            "control_stop_error",
                            f"Safe stop failed: {type(error).__name__}: {error}. "
                            "Motors may still be enabled; no automatic retry",
                        )
                    )
                else:
                    emit(("control_error", f"Sending stopped: {type(error).__name__}: {error}"))
