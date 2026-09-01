"""Adjustable-variable commands and validation."""

from __future__ import annotations

import math
from collections.abc import Sequence

from ._control import make_confirmation
from ._service import format_table
from ._serial_api_library import (
    NativeAdjustableVariable,
    NativeAdjustableVariableAnalogSlot,
    NativeAdjustableVariableFloat,
    NativeAdjustableVariableTriggerSlot,
    NativeAdjustableVariablesConfig,
    NativeAdjustableVariablesStateRequest,
)
from .types import (
    AdjustableVariable,
    AdjustableVariableAnalogSlot,
    AdjustableVariableFloat,
    AdjustableVariableInfo,
    AdjustableVariableTriggerSlot,
    AdjustableVariablesConfig,
    AdjustableVariablesState,
    CommandConfirmation,
)


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


def normalize_adj_vars_float(variables: object) -> tuple[AdjustableVariableFloat, ...]:
    try:
        values = tuple(variables)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("variables must be an iterable of AdjustableVariableFloat") from error
    if not 1 <= len(values) <= 40:
        raise ValueError("variables must contain from 1 to 40 entries")
    if any(not isinstance(item, AdjustableVariableFloat) for item in values):
        raise TypeError("each item must be an AdjustableVariableFloat")
    ids = normalize_adj_var_ids(tuple(item.id for item in values))
    try:
        normalized_values = tuple(float(item.value) for item in values)
    except (OverflowError, TypeError, ValueError) as error:
        raise ValueError("each adjustable-variable value must be finite") from error
    if any(type(item.value) not in (int, float) or not math.isfinite(value) for item, value in zip(values, normalized_values)):
        raise ValueError("each adjustable-variable value must be finite")
    return tuple(AdjustableVariableFloat(id=item_id, value=value) for item_id, value in zip(ids, normalized_values))


def get_adj_vars_float(self, ids: object) -> tuple[AdjustableVariableFloat, ...]:
    self._ensure_open()
    result = self._native.get_adj_vars_float(self._device, normalize_adj_var_ids(ids))
    return tuple(AdjustableVariableFloat(id=item.id, value=item.value) for item in result)


def get_adj_var_float(self, id: int) -> AdjustableVariableFloat:
    return get_adj_vars_float(self, (id,))[0]


def set_adj_vars_float(self, variables: object, *, need_confirmation: bool = False) -> CommandConfirmation | None:
    self._ensure_open()
    normalized = normalize_adj_vars_float(variables)
    return make_confirmation(self._native.set_adj_vars_float(
        self._device,
        tuple(NativeAdjustableVariableFloat(id=item.id, value=item.value) for item in normalized),
        need_confirmation=need_confirmation,
    ))


def set_adj_var_float(self, id: int, value: float, *, need_confirmation: bool = False) -> CommandConfirmation | None:
    return set_adj_vars_float(
        self, (AdjustableVariableFloat(id=id, value=value),), need_confirmation=need_confirmation
    )


def _normalize_config(config: object) -> AdjustableVariablesConfig:
    if not isinstance(config, AdjustableVariablesConfig):
        raise TypeError("config must be an AdjustableVariablesConfig")
    if len(config.trigger_slots) != 10 or len(config.analog_slots) != 15 or len(config.reserved) != 8:
        raise ValueError("config must contain 10 trigger slots, 15 analog slots, and 8 reserved bytes")
    if any(not isinstance(slot, AdjustableVariableTriggerSlot) for slot in config.trigger_slots):
        raise TypeError("each trigger slot must be an AdjustableVariableTriggerSlot")
    if any(not isinstance(slot, AdjustableVariableAnalogSlot) for slot in config.analog_slots):
        raise TypeError("each analog slot must be an AdjustableVariableAnalogSlot")
    if any(type(slot.source) is not int or not 0 <= slot.source <= 0xFF or len(slot.actions) != 5 or
           any(type(action) is not int or not 0 <= action <= 0xFF for action in slot.actions)
           for slot in config.trigger_slots):
        raise ValueError("trigger slot values must be bytes and actions must contain 5 bytes")
    if any(type(value) is not int or not 0 <= value <= 0xFF
           for slot in config.analog_slots
           for value in (slot.source, slot.variable_id, slot.min_value, slot.max_value)):
        raise ValueError("analog slot values must be bytes")
    if not isinstance(config.reserved, bytes):
        raise TypeError("config.reserved must be bytes")
    return config


def read_adj_vars_config(self) -> AdjustableVariablesConfig:
    self._ensure_open()
    config = self._native.read_adj_vars_config(self._device)
    return AdjustableVariablesConfig(
        trigger_slots=tuple(
            AdjustableVariableTriggerSlot(source=slot.source, actions=tuple(slot.actions))
            for slot in config.trigger_slots
        ),
        analog_slots=tuple(
            AdjustableVariableAnalogSlot(
                source=slot.source,
                variable_id=slot.variable_id,
                min_value=slot.min_value,
                max_value=slot.max_value,
            ) for slot in config.analog_slots
        ),
        reserved=bytes(config.reserved),
    )


def write_adj_vars_config(
    self, config: object, *, need_confirmation: bool = False
) -> CommandConfirmation | None:
    self._ensure_open()
    normalized = _normalize_config(config)
    native = NativeAdjustableVariablesConfig()
    for index, slot in enumerate(normalized.trigger_slots):
        native.trigger_slots[index].source = slot.source
        native.trigger_slots[index].actions[:] = slot.actions
    for index, slot in enumerate(normalized.analog_slots):
        native.analog_slots[index].source = slot.source
        native.analog_slots[index].variable_id = slot.variable_id
        native.analog_slots[index].min_value = slot.min_value
        native.analog_slots[index].max_value = slot.max_value
    native.reserved[:] = normalized.reserved
    return make_confirmation(self._native.write_adj_vars_config(
        self._device, native, need_confirmation=need_confirmation
    ))


def get_adj_vars_state(
    self,
    trigger_slot: int,
    analog_source_id: int,
    analog_variable_id: int,
    lut_source_id: int,
    lut_variable_id: int,
) -> AdjustableVariablesState:
    values = (trigger_slot, analog_source_id, analog_variable_id, lut_source_id, lut_variable_id)
    if any(type(value) is not int for value in values):
        raise TypeError("adjustable-variable state selectors must be integers")
    if not 0 <= trigger_slot < 10 or not 0 <= analog_source_id <= 0xFFFF or not 0 <= lut_source_id <= 0xFFFF or \
       not 0 <= analog_variable_id <= 0xFF or not 0 <= lut_variable_id <= 0xFF:
        raise ValueError("adjustable-variable state selectors are out of range")
    self._ensure_open()
    state = self._native.get_adj_vars_state(
        self._device,
        NativeAdjustableVariablesStateRequest(
            trigger_slot, analog_source_id, analog_variable_id, lut_source_id, lut_variable_id
        ),
    )
    return AdjustableVariablesState(
        trigger_rc_data=state.trigger_rc_data,
        trigger_action=state.trigger_action,
        analog_source_value=state.analog_source_value,
        analog_variable_value=state.analog_variable_value,
        lut_source_value=state.lut_source_value,
        lut_variable_value=state.lut_variable_value,
    )


def get_adj_vars_info(self, start_id: int = 0) -> tuple[AdjustableVariableInfo, ...]:
    if type(start_id) is not int or not 0 <= start_id <= 0xFF:
        raise ValueError("start_id must be an integer in range 0..255")
    self._ensure_open()
    result: list[AdjustableVariableInfo] = []
    next_id = start_id
    for _ in range(102):
        page = self._native.get_adj_vars_info(self._device, next_id)
        if not page:
            break
        result.extend(
            AdjustableVariableInfo(
                id=item.id,
                min_value=item.min_value,
                max_value=item.max_value,
                value=item.value,
            ) for item in page
        )
        following_id = page[-1].id + 1
        if following_id > 0xFF or following_id <= next_id:
            break
        next_id = following_id
    return tuple(result)


def format_adj_vars(variables: Sequence[AdjustableVariable | AdjustableVariableFloat]) -> str:
    if any(not isinstance(variable, (AdjustableVariable, AdjustableVariableFloat)) for variable in variables):
        raise TypeError("variables must contain AdjustableVariable or AdjustableVariableFloat")
    rows = tuple(
        (str(variable.id), f"{variable.value:g}" if isinstance(variable, AdjustableVariableFloat) else str(variable.value))
        for variable in variables
    )
    return format_table(("ID", "Value"), rows) if rows else "No adjustable variables"


def format_adj_vars_info(variables: Sequence[AdjustableVariableInfo]) -> str:
    if any(not isinstance(variable, AdjustableVariableInfo) for variable in variables):
        raise TypeError("variables must contain AdjustableVariableInfo")
    rows = tuple(
        (str(variable.id), str(variable.min_value), str(variable.max_value), str(variable.value))
        for variable in variables
    )
    return format_table(("ID", "Min", "Max", "Value"), rows) if rows else "No adjustable variables"


def format_adj_vars_config(config: AdjustableVariablesConfig) -> str:
    if not isinstance(config, AdjustableVariablesConfig):
        raise TypeError("config must be AdjustableVariablesConfig")
    trigger_rows = tuple(
        (str(index), str(slot.source), " ".join(str(action) for action in slot.actions))
        for index, slot in enumerate(config.trigger_slots)
    )
    analog_rows = tuple(
        (str(index), str(slot.source), str(slot.variable_id), str(slot.min_value), str(slot.max_value))
        for index, slot in enumerate(config.analog_slots)
    )
    return "\n\n".join((
        format_table(("Trigger", "Source", "Actions"), trigger_rows),
        format_table(("Analog", "Source", "Variable", "Min", "Max"), analog_rows),
    ))


def format_adj_vars_state(state: AdjustableVariablesState) -> str:
    if not isinstance(state, AdjustableVariablesState):
        raise TypeError("state must be AdjustableVariablesState")
    return format_table(("Field", "Value"), (
        ("Trigger RC", str(state.trigger_rc_data)),
        ("Trigger action", str(state.trigger_action)),
        ("Analog source", str(state.analog_source_value)),
        ("Analog variable", f"{state.analog_variable_value:g}"),
        ("LUT source", str(state.lut_source_value)),
        ("LUT variable", f"{state.lut_variable_value:g}"),
    ))
