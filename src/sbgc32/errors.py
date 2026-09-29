"""Controller rejections and unavailable hardware features."""

from __future__ import annotations

from .commands import Command

__all__ = [
    "ControllerCommandError",
    "CanDeviceNotFoundError",
    "CanNotSupportedError",
    "ExternalMotorNotFoundError",
    "is_can_device_not_found_error",
    "is_can_not_supported_error",
    "is_external_motor_not_found_error",
    "is_module_not_connected_error",
]


class ControllerCommandError(RuntimeError):
    """A CMD_ERROR reply, preserving the command-specific error code and data."""

    def __init__(self, command_id: int, error_code: int, error_data: bytes = b"") -> None:
        self.command_id = command_id
        self.error_code = error_code
        self.error_data = bytes(error_data)
        try:
            command_name = Command(command_id).name
        except ValueError:
            command_name = "command"
        super().__init__(
            f"Controller rejected {command_name} (#{command_id}): "
            f"error code {error_code}, error_data={self.error_data.hex(' ') or '<empty>'}"
        )


class CanNotSupportedError(RuntimeError):
    """Raised when a command needs CAN but the controller has no CAN port."""


class CanDeviceNotFoundError(TimeoutError):
    """Raised when no CAN device answers a scan request."""


class ExternalMotorNotFoundError(TimeoutError):
    """Raised when a requested external motor does not reply on the CAN bus."""


def is_can_not_supported_error(error: BaseException) -> bool:
    """Return ``True`` when an operation needs a CAN port the board lacks."""

    return isinstance(error, CanNotSupportedError)


def is_can_device_not_found_error(error: BaseException) -> bool:
    """Return ``True`` when a CAN scan found no responding device."""

    return isinstance(error, CanDeviceNotFoundError)


def is_external_motor_not_found_error(error: BaseException) -> bool:
    """Return ``True`` when an addressed external motor did not reply."""

    return isinstance(error, ExternalMotorNotFoundError)


def is_module_not_connected_error(error: BaseException) -> bool:
    """Return ``True`` when a required CAN device or CAN port is unavailable."""

    return (
        is_can_not_supported_error(error)
        or is_can_device_not_found_error(error)
        or is_external_motor_not_found_error(error)
    )
