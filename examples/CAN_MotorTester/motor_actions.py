"""One-shot external motor actions through sbgc32."""

import logging
import queue

from sbgc32 import ConfirmationStatus, ExternalMotorAction

ACTIONS = (
    ("Off / floating", ExternalMotorAction.OFF_FLOATING),
    ("Off / brake", ExternalMotorAction.OFF_BRAKE),
    ("Safe stop", ExternalMotorAction.OFF_SAFE),
    ("Motor on", ExternalMotorAction.ON),
    ("Home position", ExternalMotorAction.HOME_POSITION),
    ("Search home", ExternalMotorAction.SEARCH_HOME),
)
logger = logging.getLogger(__name__)


class ActionRunner:
    def __init__(self, device, requests, emit):
        self.device, self.requests, self.emit = device, requests, emit
        self.pending = None

    def tick(self):
        if self.pending is not None:
            label, future = self.pending
            if not future.done():
                return
            self.pending = None
            try:
                result = future.result()
                if result is None or result.status != ConfirmationStatus.RECEIVED:
                    raise ValueError(f"Command not confirmed: {result!r}")
                message = f"{label}: controller confirmed command"
            except Exception as error:
                message = f"{label}: {type(error).__name__}: {error} (no automatic retry)"
            logger.info(message)
            self.emit(("action", message))
        try:
            mask, action, label = self.requests.get_nowait()
        except queue.Empty:
            return
        try:
            logger.info("Motor action TX: mask=0x%02X action=%d", mask, action)
            future = self.device.ext_motors_action(
                mask, action, need_confirmation=True, timeout=1.0
            )
            self.pending = (label, future)
        except Exception as error:
            self.emit(("action", f"{label}: {type(error).__name__}: {error}"))
