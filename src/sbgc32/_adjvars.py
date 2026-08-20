"""Adjustable-variable commands and validation."""

from __future__ import annotations

from ._control import make_confirmation
from .native import NativeAdjustableVariable
from .types import AdjustableVariable, CommandConfirmation


def normalize_adj_var_ids(ids: object, *, maximum: int = 40) -> tuple[int, ...]:
    try:
        values = tuple(ids)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("ids must be an iterable of adjustable-variable IDs") from error
    if not 1 <= len(values) <= maximum:
        raise ValueError(f"ids must contain from 1 to {maximum} entries")
    if any(type(item) is not int or not 0 <= item <= 0xFF for item in values):
        raise ValueError("each adjustable-variable ID must be an integer in range 0..255")
    if len(set(values)) != len(values):
        raise ValueError("adjustable-variable IDs must not repeat in one request")
    return values


def normalize_adj_vars(variables: object) -> tuple[AdjustableVariable, ...]:
    try:
        values = tuple(variables)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("variables must be an iterable of AdjustableVariable") from error
    if not 1 <= len(values) <= 40:
        raise ValueError("variables must contain from 1 to 40 entries")
    if any(not isinstance(item, AdjustableVariable) for item in values):
        raise TypeError("each item must be an AdjustableVariable")
    ids = normalize_adj_var_ids(tuple(item.id for item in values))
    if any(type(item.value) is not int or not -0x80000000 <= item.value <= 0x7FFFFFFF for item in values):
        raise ValueError("each adjustable-variable value must be a signed 32-bit integer")
    return tuple(AdjustableVariable(id=item_id, value=item.value) for item_id, item in zip(ids, values))


def get_adj_vars(self, ids: object) -> tuple[AdjustableVariable, ...]:
    self._ensure_open()
    normalized_ids = normalize_adj_var_ids(ids)
    result = self._native.get_adj_vars(self._device, normalized_ids)
    return tuple(AdjustableVariable(id=item.id, value=item.value) for item in result)


def get_adj_var(self, id: int) -> AdjustableVariable:
    return get_adj_vars(self, (id,))[0]


def set_adj_vars(self, variables: object, *, need_confirmation: bool = False) -> CommandConfirmation | None:
    self._ensure_open()
    normalized_variables = normalize_adj_vars(variables)
    return make_confirmation(self._native.set_adj_vars(
        self._device,
        tuple(NativeAdjustableVariable(id=item.id, value=item.value) for item in normalized_variables),
        need_confirmation=need_confirmation,
    ))


def set_adj_var(self, id: int, value: int, *, need_confirmation: bool = False) -> CommandConfirmation | None:
    return set_adj_vars(self, (AdjustableVariable(id=id, value=value),), need_confirmation=need_confirmation)


def save_adj_vars(self, ids: object, *, need_confirmation: bool = False) -> CommandConfirmation | None:
    self._ensure_open()
    return make_confirmation(self._native.save_adj_vars(
        self._device, normalize_adj_var_ids(ids, maximum=102), need_confirmation=need_confirmation
    ))


def save_all_adj_vars(self, *, need_confirmation: bool = False) -> CommandConfirmation | None:
    self._ensure_open()
    return make_confirmation(self._native.save_adj_vars(
        self._device, None, need_confirmation=need_confirmation
    ))
