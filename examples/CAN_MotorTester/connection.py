"""Application diagnostics around the supplied SimpleBGC transport."""

import logging

from sbgc32 import SimpleBGC

logger = logging.getLogger(__name__)


def state_decoder(decoder):
    def decode(frame):
        payload = frame.payload
        logger.info(
            "Motor state RX: command=%d length=%d payload=%s",
            frame.command_id,
            len(payload),
            payload.hex(" "),
        )
        if frame.command_id == 67:
            raise ValueError(
                "Received CMD_CONFIRM (67), not motor-state telemetry (131). "
                f"Payload: {payload.hex(' ')}. See motor-state.log."
            )
        if frame.command_id == 255:
            raise ValueError(f"Controller returned CMD_ERROR (255): {payload.hex(' ')}")
        if frame.command_id != 131:
            raise ValueError(f"Expected state command 131, received {frame.command_id}")
        if len(payload) < 5:
            raise ValueError(
                f"Truncated motor-state header: {len(payload)} bytes; expected at least 5"
            )
        try:
            return decoder(frame) if decoder is not None else frame
        except ValueError as error:
            raise ValueError(
                f"{error}; received {len(payload)} payload bytes "
                f"({len(payload) - 5} data bytes). See motor-state.log."
            ) from error

    return decode


class DiagnosticSimpleBGC(SimpleBGC):
    def request_raw(self, command_id, payload=b"", **kwargs):
        if command_id == 131:
            kwargs["decoder"] = state_decoder(kwargs.get("decoder"))
        return super().request_raw(command_id, payload, **kwargs)
