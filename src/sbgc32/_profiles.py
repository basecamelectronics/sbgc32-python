from __future__ import annotations

from collections.abc import Iterable

from ._control import make_confirmation
from ._service import format_table
from .types import (
    CommandConfirmation,
    ProfileId,
    ProfileParameters,
    ProfileSet,
    ProfileSetAction,
    ProfileWritingAction,
)

_PARAMETER_SIZES = (134, 104, 151, 221)


def _profile_id(value: ProfileId | int) -> int:
    value = int(value)
    if value not in (0, 1, 2, 3, 4, 0xFF):
        raise ValueError("profile_id must be 0..4 or ProfileId.CURRENT")
    return value


def _confirmation(value: object) -> bool:
    if type(value) is not bool:
        raise TypeError("need_confirmation must be bool")
    return value


def _block(value: object) -> int:
    if type(value) is not int or not 0 <= value < len(_PARAMETER_SIZES):
        raise ValueError("block must be an integer in range 0..3")
    return value


def _parameters(value: object, block: int) -> bytes:
    if not isinstance(value, bytes):
        raise TypeError("parameters must be bytes")
    if len(value) != _PARAMETER_SIZES[block]:
        raise ValueError(
            f"parameters for block {block} must contain {_PARAMETER_SIZES[block]} bytes"
        )
    return value


def read_profile_names(self) -> tuple[str, str, str, str, str]:
    self._ensure_open()
    raw = self._native.read_profile_names(self._device)
    return tuple(
        raw[index : index + 48].split(b"\0", 1)[0].decode("utf-8", "replace")
        for index in range(0, 240, 48)
    )


def write_profile_names(
    self,
    names: Iterable[str],
    *,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()
    try:
        names = tuple(names)
    except TypeError as error:
        raise TypeError("names must be an iterable of five strings") from error
    if len(names) != 5 or any(not isinstance(name, str) for name in names):
        raise ValueError("names must contain exactly five strings")
    try:
        encoded = tuple(name.encode("utf-8") for name in names)
    except UnicodeEncodeError as error:
        raise ValueError("profile names must be UTF-8 encodable") from error
    if any(len(name) > 47 or b"\0" in name for name in encoded):
        raise ValueError("each profile name must contain at most 47 non-null bytes")
    raw = b"".join(name.ljust(48, b"\0") for name in encoded)
    return make_confirmation(
        self._native.write_profile_names(
            self._device, raw, need_confirmation=_confirmation(need_confirmation)
        )
    )


def manage_profile_set(
    self,
    slot: ProfileSet | int,
    action: ProfileSetAction | int,
    *,
    need_confirmation: bool = False,
    confirm: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()
    try:
        slot = ProfileSet(slot)
        action = ProfileSetAction(action)
    except ValueError as error:
        raise ValueError("unsupported profile-set slot or action") from error
    if action is ProfileSetAction.CLEAR and confirm is not True:
        raise ValueError("clearing a profile set requires confirm=True")
    return make_confirmation(
        self._native.manage_profile_set(
            self._device,
            int(slot),
            int(action),
            need_confirmation=_confirmation(need_confirmation),
        )
    )


def set_profile_writing(
    self,
    action: ProfileWritingAction | int,
    *,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()
    try:
        action = ProfileWritingAction(action)
    except ValueError as error:
        raise ValueError(
            "action must be ProfileWritingAction.START or ProfileWritingAction.STOP"
        ) from error
    return make_confirmation(
        self._native.set_profile_writing(
            self._device,
            int(action),
            need_confirmation=_confirmation(need_confirmation),
        )
    )


def read_profile_parameter_block(
    self, block: int, profile_id: ProfileId | int = ProfileId.CURRENT
) -> bytes:
    self._ensure_open()
    block = _block(block)
    return self._native.read_profile_params(
        self._device, block, _profile_id(profile_id), _PARAMETER_SIZES[block]
    )


def write_profile_parameter_block(
    self,
    block: int,
    parameters: bytes,
    *,
    need_confirmation: bool = False,
) -> CommandConfirmation | None:
    self._ensure_open()
    block = _block(block)
    return make_confirmation(
        self._native.write_profile_params(
            self._device,
            block,
            _parameters(parameters, block),
            need_confirmation=_confirmation(need_confirmation),
        )
    )


def read_params_3(self, profile_id: ProfileId | int = ProfileId.CURRENT) -> bytes:
    return read_profile_parameter_block(self, 0, profile_id)


def read_params_ext(self, profile_id: ProfileId | int = ProfileId.CURRENT) -> bytes:
    return read_profile_parameter_block(self, 1, profile_id)


def read_params_ext2(self, profile_id: ProfileId | int = ProfileId.CURRENT) -> bytes:
    return read_profile_parameter_block(self, 2, profile_id)


def read_params_ext3(self, profile_id: ProfileId | int = ProfileId.CURRENT) -> bytes:
    return read_profile_parameter_block(self, 3, profile_id)


def write_params_3(
    self, parameters: bytes, *, need_confirmation: bool = False
) -> CommandConfirmation | None:
    return write_profile_parameter_block(self, 0, parameters, need_confirmation=need_confirmation)


def write_params_ext(
    self, parameters: bytes, *, need_confirmation: bool = False
) -> CommandConfirmation | None:
    return write_profile_parameter_block(self, 1, parameters, need_confirmation=need_confirmation)


def write_params_ext2(
    self, parameters: bytes, *, need_confirmation: bool = False
) -> CommandConfirmation | None:
    return write_profile_parameter_block(self, 2, parameters, need_confirmation=need_confirmation)


def write_params_ext3(
    self, parameters: bytes, *, need_confirmation: bool = False
) -> CommandConfirmation | None:
    return write_profile_parameter_block(self, 3, parameters, need_confirmation=need_confirmation)


def read_profile_parameters(
    self, profile_id: ProfileId | int = ProfileId.CURRENT
) -> ProfileParameters:
    self._ensure_open()
    profile_id = _profile_id(profile_id)
    return ProfileParameters(
        params_3=read_params_3(self, profile_id),
        params_ext=read_params_ext(self, profile_id),
        params_ext2=read_params_ext2(self, profile_id),
        params_ext3=read_params_ext3(self, profile_id),
    )


def write_profile_parameters(
    self,
    parameters: ProfileParameters,
    *,
    need_confirmation: bool = False,
) -> None:
    self._ensure_open()
    if not isinstance(parameters, ProfileParameters):
        raise TypeError("parameters must be ProfileParameters")
    blocks = (
        _parameters(parameters.params_3, 0),
        _parameters(parameters.params_ext, 1),
        _parameters(parameters.params_ext2, 2),
        _parameters(parameters.params_ext3, 3),
    )
    set_profile_writing(self, ProfileWritingAction.START, need_confirmation=need_confirmation)
    try:
        for block, data in enumerate(blocks):
            write_profile_parameter_block(self, block, data, need_confirmation=need_confirmation)
    finally:
        set_profile_writing(self, ProfileWritingAction.STOP, need_confirmation=need_confirmation)


def use_profile_defaults(
    self, profile_id: ProfileId | int = ProfileId.CURRENT, *, confirm: bool = False
) -> None:
    self._ensure_open()
    if confirm is not True:
        raise ValueError("use_profile_defaults requires confirm=True")
    self._native.use_profile_defaults(self._device, _profile_id(profile_id))


def format_profile_names(names: tuple[str, str, str, str, str]) -> str:
    if (
        not isinstance(names, tuple)
        or len(names) != 5
        or any(not isinstance(name, str) for name in names)
    ):
        raise TypeError("names must be a tuple of five strings")
    return format_table(
        ("Profile", "Name"),
        tuple((str(index), name or f"Profile {index}") for index, name in enumerate(names, 1)),
    )


def format_profile_parameters(parameters: ProfileParameters) -> str:
    if not isinstance(parameters, ProfileParameters):
        raise TypeError("parameters must be ProfileParameters")
    return format_table(
        ("Block", "Profile", "Bytes"),
        (
            ("Params 3", str(parameters.params_3[0]), str(len(parameters.params_3))),
            (
                "Params Ext",
                str(parameters.params_ext[0]),
                str(len(parameters.params_ext)),
            ),
            (
                "Params Ext2",
                str(parameters.params_ext2[0]),
                str(len(parameters.params_ext2)),
            ),
            (
                "Params Ext3",
                str(parameters.params_ext3[0]),
                str(len(parameters.params_ext3)),
            ),
        ),
    )
