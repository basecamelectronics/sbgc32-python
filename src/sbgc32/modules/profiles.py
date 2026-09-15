"""Asynchronous profile names, parameter blocks and profile-set commands."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import Future
from typing import TYPE_CHECKING, TypeVar

from ..commands import Command
from ..protocol import WireFrame
from ..types import (
    CommandConfirmation,
    ProfileId,
    ProfileParameters,
    ProfileSet,
    ProfileSetAction,
    ProfileWritingAction,
)
from .realtime import decode_confirmation

if TYPE_CHECKING:
    from ..device import SimpleBGC


_PARAMETER_BLOCKS = (
    (Command.CMD_READ_PARAMS_3, Command.CMD_WRITE_PARAMS_3, 134),
    (Command.CMD_READ_PARAMS_EXT, Command.CMD_WRITE_PARAMS_EXT, 104),
    (Command.CMD_READ_PARAMS_EXT2, Command.CMD_WRITE_PARAMS_EXT2, 151),
    (Command.CMD_READ_PARAMS_EXT3, Command.CMD_WRITE_PARAMS_EXT3, 221),
)
_PROFILE_NAME_SIZE = 48
_PROFILE_COUNT = 5
_T = TypeVar("_T")


def _profile_id(value: ProfileId | int) -> int:
    value = int(value)
    if value not in (0, 1, 2, 3, 4, 0xFF):
        raise ValueError("profile_id must be 0..4 or ProfileId.CURRENT")
    return value


def _block(value: object) -> int:
    if type(value) is not int or not 0 <= value < len(_PARAMETER_BLOCKS):
        raise ValueError("block must be an integer in range 0..3")
    return value


def _parameters(value: object, block: int) -> bytes:
    if not isinstance(value, bytes):
        raise TypeError("parameters must be bytes")
    size = _PARAMETER_BLOCKS[block][2]
    if len(value) != size:
        raise ValueError(f"parameters for block {block} must contain {size} bytes")
    return value


def _confirmation(
    self: SimpleBGC,
    command: Command,
    payload: bytes,
    need_confirmation: bool,
    timeout: float | None,
) -> Future[CommandConfirmation | None]:
    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")
    if need_confirmation:
        return self.request_raw(
            int(command), payload, timeout=timeout, route="profiles", decoder=decode_confirmation
        )
    return self.send_raw(int(command), payload, route="profiles")


def _decode_exact(size: int, name: str) -> Callable[[WireFrame], bytes]:
    def decode(frame: WireFrame) -> bytes:
        if len(frame.payload) != size:
            raise ValueError(f"{name} response must contain {size} bytes, got {len(frame.payload)}")
        return frame.payload

    return decode


def _decode_profile_names(frame: WireFrame) -> tuple[str, str, str, str, str]:
    raw = _decode_exact(_PROFILE_NAME_SIZE * _PROFILE_COUNT, "READ_PROFILE_NAMES")(frame)
    return tuple(
        raw[offset : offset + _PROFILE_NAME_SIZE].split(b"\0", 1)[0].decode("utf-8", "replace")
        for offset in range(0, len(raw), _PROFILE_NAME_SIZE)
    )  # type: ignore[return-value]


def _combine(futures: tuple[Future[_T], ...], build: Callable[[tuple[_T, ...]], _T]) -> Future[_T]:
    """Complete one Future when all independent protocol requests finish."""

    result: Future[_T] = Future()
    values: list[_T | None] = [None] * len(futures)
    remaining = len(futures)

    def completed(index: int, future: Future[_T]) -> None:
        nonlocal remaining
        if result.done():
            return
        try:
            values[index] = future.result()
        except BaseException as error:
            result.set_exception(error)
            return
        remaining -= 1
        if remaining == 0:
            result.set_result(build(tuple(values)))  # type: ignore[arg-type]

    for index, future in enumerate(futures):
        future.add_done_callback(
            lambda completed_future, index=index: completed(index, completed_future)
        )
    return result


def read_profile_names(
    self: SimpleBGC, *, timeout: float | None = 1.0
) -> Future[tuple[str, str, str, str, str]]:
    """Read the five EEPROM-stored profile names."""

    return self.request_raw(
        int(Command.CMD_READ_PROFILE_NAMES),
        timeout=timeout,
        route="profiles",
        decoder=_decode_profile_names,
    )


def write_profile_names(
    self: SimpleBGC,
    names: Iterable[str],
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Write the five profile names to EEPROM."""

    try:
        requested = tuple(names)
    except TypeError as error:
        raise TypeError("names must be an iterable of five strings") from error
    if len(requested) != _PROFILE_COUNT or any(not isinstance(name, str) for name in requested):
        raise ValueError("names must contain exactly five strings")
    try:
        encoded = tuple(name.encode("utf-8") for name in requested)
    except UnicodeEncodeError as error:
        raise ValueError("profile names must be UTF-8 encodable") from error
    if any(len(name) > _PROFILE_NAME_SIZE - 1 or b"\0" in name for name in encoded):
        raise ValueError("each profile name must contain at most 47 non-null bytes")
    payload = b"".join(name.ljust(_PROFILE_NAME_SIZE, b"\0") for name in encoded)
    return _confirmation(self, Command.CMD_WRITE_PROFILE_NAMES, payload, need_confirmation, timeout)


def manage_profile_set(
    self: SimpleBGC,
    slot: ProfileSet | int,
    action: ProfileSetAction | int,
    *,
    need_confirmation: bool = False,
    confirm: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Save, load or clear one profile-set slot."""

    try:
        selected_slot = ProfileSet(slot)
        selected_action = ProfileSetAction(action)
    except ValueError as error:
        raise ValueError("unsupported profile-set slot or action") from error
    if selected_action is ProfileSetAction.CLEAR and confirm is not True:
        raise ValueError("clearing a profile set requires confirm=True")
    return _confirmation(
        self,
        Command.CMD_PROFILE_SET,
        bytes((int(selected_slot), int(selected_action))) + bytes(8),
        need_confirmation,
        timeout,
    )


def set_profile_writing(
    self: SimpleBGC,
    action: ProfileWritingAction | int,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Start or stop a multi-block profile update."""

    try:
        selected_action = ProfileWritingAction(action)
    except ValueError as error:
        raise ValueError(
            "action must be ProfileWritingAction.START or ProfileWritingAction.STOP"
        ) from error
    return _confirmation(
        self,
        Command.CMD_WRITE_PARAMS_SET,
        bytes((int(selected_action),)),
        need_confirmation,
        timeout,
    )


def read_profile_parameter_block(
    self: SimpleBGC,
    block: int,
    profile_id: ProfileId | int = ProfileId.CURRENT,
    *,
    timeout: float | None = 1.0,
) -> Future[bytes]:
    """Read one raw profile parameter block."""

    index = _block(block)
    command, _, size = _PARAMETER_BLOCKS[index]
    return self.request_raw(
        int(command),
        bytes((_profile_id(profile_id),)),
        timeout=timeout,
        route="profiles",
        decoder=_decode_exact(size, command.name.removeprefix("CMD_")),
    )


def write_profile_parameter_block(
    self: SimpleBGC,
    block: int,
    parameters: bytes,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Write one validated raw profile parameter block."""

    index = _block(block)
    _, command, _ = _PARAMETER_BLOCKS[index]
    return _confirmation(self, command, _parameters(parameters, index), need_confirmation, timeout)


def read_params_3(
    self: SimpleBGC, profile_id: ProfileId | int = ProfileId.CURRENT, *, timeout: float | None = 1.0
) -> Future[bytes]:
    """Read the legacy ``PARAMS_3`` block for one profile."""

    return read_profile_parameter_block(self, 0, profile_id, timeout=timeout)


def read_params_ext(
    self: SimpleBGC, profile_id: ProfileId | int = ProfileId.CURRENT, *, timeout: float | None = 1.0
) -> Future[bytes]:
    """Read the ``PARAMS_EXT`` block for one profile."""

    return read_profile_parameter_block(self, 1, profile_id, timeout=timeout)


def read_params_ext2(
    self: SimpleBGC, profile_id: ProfileId | int = ProfileId.CURRENT, *, timeout: float | None = 1.0
) -> Future[bytes]:
    """Read the ``PARAMS_EXT2`` block for one profile."""

    return read_profile_parameter_block(self, 2, profile_id, timeout=timeout)


def read_params_ext3(
    self: SimpleBGC, profile_id: ProfileId | int = ProfileId.CURRENT, *, timeout: float | None = 1.0
) -> Future[bytes]:
    """Read the ``PARAMS_EXT3`` block for one profile."""

    return read_profile_parameter_block(self, 3, profile_id, timeout=timeout)


def write_params_3(
    self: SimpleBGC,
    parameters: bytes,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Write one validated ``PARAMS_3`` block."""

    return write_profile_parameter_block(
        self, 0, parameters, need_confirmation=need_confirmation, timeout=timeout
    )


def write_params_ext(
    self: SimpleBGC,
    parameters: bytes,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Write one validated ``PARAMS_EXT`` block."""

    return write_profile_parameter_block(
        self, 1, parameters, need_confirmation=need_confirmation, timeout=timeout
    )


def write_params_ext2(
    self: SimpleBGC,
    parameters: bytes,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Write one validated ``PARAMS_EXT2`` block."""

    return write_profile_parameter_block(
        self, 2, parameters, need_confirmation=need_confirmation, timeout=timeout
    )


def write_params_ext3(
    self: SimpleBGC,
    parameters: bytes,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Write one validated ``PARAMS_EXT3`` block."""

    return write_profile_parameter_block(
        self, 3, parameters, need_confirmation=need_confirmation, timeout=timeout
    )


def read_profile_parameters(
    self: SimpleBGC,
    profile_id: ProfileId | int = ProfileId.CURRENT,
    *,
    timeout: float | None = 1.0,
) -> Future[ProfileParameters]:
    """Read all four profile blocks without blocking the caller."""

    profile_id = _profile_id(profile_id)
    requests = tuple(
        read_profile_parameter_block(self, index, profile_id, timeout=timeout)
        for index in range(len(_PARAMETER_BLOCKS))
    )
    return _combine(requests, lambda values: ProfileParameters(*values))


def write_profile_parameters(
    self: SimpleBGC,
    parameters: ProfileParameters,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[None]:
    """Write all profile blocks in the required START → blocks → STOP order."""

    if not isinstance(parameters, ProfileParameters):
        raise TypeError("parameters must be ProfileParameters")
    blocks = tuple(
        _parameters(value, index)
        for index, value in enumerate(
            (
                parameters.params_3,
                parameters.params_ext,
                parameters.params_ext2,
                parameters.params_ext3,
            )
        )
    )
    result: Future[None] = Future()
    first_error: BaseException | None = None

    def start() -> Future[CommandConfirmation | None]:
        return set_profile_writing(
            self, ProfileWritingAction.START, need_confirmation=need_confirmation, timeout=timeout
        )

    def stop() -> Future[CommandConfirmation | None]:
        return set_profile_writing(
            self, ProfileWritingAction.STOP, need_confirmation=need_confirmation, timeout=timeout
        )

    actions: tuple[Callable[[], Future[CommandConfirmation | None]], ...] = (
        start,
        *(
            lambda index=index, data=data: write_profile_parameter_block(
                self, index, data, need_confirmation=need_confirmation, timeout=timeout
            )
            for index, data in enumerate(blocks)
        ),
        stop,
    )

    def run(stage: int) -> None:
        nonlocal first_error
        try:
            current = actions[stage]()
        except BaseException as error:
            result.set_exception(error)
            return

        def completed(future: Future[CommandConfirmation | None]) -> None:
            nonlocal first_error
            try:
                future.result()
            except BaseException as error:
                if stage == 0 or stage == len(actions) - 1:
                    result.set_exception(first_error or error)
                    return
                first_error = error
                run(len(actions) - 1)
                return
            if stage == len(actions) - 1:
                if first_error is None:
                    result.set_result(None)
                else:
                    result.set_exception(first_error)
                return
            run(stage + 1)

        current.add_done_callback(completed)

    run(0)
    return result


def use_profile_defaults(
    self: SimpleBGC, profile_id: ProfileId | int = ProfileId.CURRENT, *, confirm: bool = False
) -> Future[None]:
    """Restore default settings for one profile after explicit confirmation."""

    if confirm is not True:
        raise ValueError("use_profile_defaults requires confirm=True")
    return self.send_raw(
        int(Command.CMD_USE_DEFAULTS), bytes((_profile_id(profile_id),)), route="profiles"
    )
