"""Asynchronous adjustable-variable commands."""

from __future__ import annotations

import math
import struct
from concurrent.futures import Future
from typing import TYPE_CHECKING

from ..commands import Command
from ..protocol import WireFrame
from ..types import (
    AdjustableVariable,
    AdjustableVariableAnalogSlot,
    AdjustableVariableFloat,
    AdjustableVariableInfo,
    AdjustableVariablesConfig,
    AdjustableVariablesState,
    AdjustableVariableTriggerSlot,
    CommandConfirmation,
)
from .realtime import decode_confirmation

if TYPE_CHECKING:
    from ..device import SimpleBGC


def normalize_adj_var_ids(ids: object, *, maximum: int = 40) -> tuple[int, ...]:
    """Validate and normalize an adjustable-variable identifier sequence."""

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
    """Validate integer adjustable-variable records before sending them."""

    try:
        values = tuple(variables)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("variables must be an iterable of AdjustableVariable") from error
    if not 1 <= len(values) <= 40 or any(
        not isinstance(item, AdjustableVariable) for item in values
    ):
        raise ValueError("variables must contain from 1 to 40 AdjustableVariable items")
    ids = normalize_adj_var_ids(tuple(item.id for item in values))
    if any(type(item.value) is not int or not -(2**31) <= item.value < 2**31 for item in values):
        raise ValueError("each adjustable-variable value must be a signed 32-bit integer")
    return tuple(AdjustableVariable(item_id, item.value) for item_id, item in zip(ids, values))


def normalize_adj_vars_float(variables: object) -> tuple[AdjustableVariableFloat, ...]:
    """Validate floating-point adjustable-variable records before sending them."""

    try:
        values = tuple(variables)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("variables must be an iterable of AdjustableVariableFloat") from error
    if not 1 <= len(values) <= 40 or any(
        not isinstance(item, AdjustableVariableFloat) for item in values
    ):
        raise ValueError("variables must contain from 1 to 40 AdjustableVariableFloat items")
    ids = normalize_adj_var_ids(tuple(item.id for item in values))
    if any(
        type(item.value) not in (int, float) or not math.isfinite(item.value) for item in values
    ):
        raise ValueError("each adjustable-variable value must be finite")
    return tuple(
        AdjustableVariableFloat(item_id, float(item.value)) for item_id, item in zip(ids, values)
    )


def _decode_values(
    frame: WireFrame, ids: tuple[int, ...], *, floating: bool
) -> tuple[AdjustableVariable | AdjustableVariableFloat, ...]:
    expected = 1 + len(ids) * 5
    if len(frame.payload) != expected or frame.payload[0] != len(ids):
        raise ValueError("adjustable-variable response has an unexpected length or count")
    result: list[AdjustableVariable | AdjustableVariableFloat] = []
    for offset, expected_id in zip(range(1, expected, 5), ids):
        received_id = frame.payload[offset]
        if received_id != expected_id:
            raise ValueError("adjustable-variable response IDs do not match the request")
        value = struct.unpack_from("<f" if floating else "<i", frame.payload, offset + 1)[0]
        result.append(
            AdjustableVariableFloat(received_id, value)
            if floating
            else AdjustableVariable(received_id, value)
        )
    return tuple(result)


def _get_values(
    self: SimpleBGC, ids: object, *, floating: bool, timeout: float | None
) -> Future[object]:
    normalized = normalize_adj_var_ids(ids)
    tx = Command.CMD_GET_ADJ_VARS_VAL_F if floating else Command.CMD_GET_ADJ_VARS_VAL
    rx = Command.CMD_SET_ADJ_VARS_VAL_F if floating else Command.CMD_SET_ADJ_VARS_VAL
    return self.request_raw(
        int(tx),
        bytes((len(normalized),)) + bytes(normalized),
        response_command_id=int(rx),
        timeout=timeout,
        route="adjvars",
        decoder=lambda frame: _decode_values(frame, normalized, floating=floating),
    )


def get_adj_vars(
    self: SimpleBGC, ids: object, *, timeout: float | None = 1.0
) -> Future[tuple[AdjustableVariable, ...]]:
    """Read the integer values for the requested adjustable-variable IDs."""

    return _get_values(self, ids, floating=False, timeout=timeout)


def get_adj_var(
    self: SimpleBGC, id: int, *, timeout: float | None = 1.0
) -> Future[AdjustableVariable]:
    """Read one integer adjustable-variable value."""

    result: Future[AdjustableVariable] = Future()
    future = get_adj_vars(self, (id,), timeout=timeout)
    future.add_done_callback(lambda done: _complete_single(done, result))
    return result


def _complete_single(source: Future[object], target: Future[object]) -> None:
    try:
        target.set_result(source.result()[0])
    except BaseException as error:
        target.set_exception(error)


def get_adj_vars_float(
    self: SimpleBGC, ids: object, *, timeout: float | None = 1.0
) -> Future[tuple[AdjustableVariableFloat, ...]]:
    """Read floating-point values for the requested adjustable-variable IDs."""

    return _get_values(self, ids, floating=True, timeout=timeout)


def get_adj_var_float(
    self: SimpleBGC, id: int, *, timeout: float | None = 1.0
) -> Future[AdjustableVariableFloat]:
    """Read one floating-point adjustable-variable value."""

    result: Future[AdjustableVariableFloat] = Future()
    future = get_adj_vars_float(self, (id,), timeout=timeout)
    future.add_done_callback(lambda done: _complete_single(done, result))
    return result


def _set_values(
    self: SimpleBGC,
    variables: object,
    *,
    floating: bool,
    need_confirmation: bool,
    timeout: float | None,
) -> Future[CommandConfirmation | None]:
    normalized = normalize_adj_vars_float(variables) if floating else normalize_adj_vars(variables)
    payload = bytearray((len(normalized),))
    for item in normalized:
        payload.append(item.id)
        payload.extend(struct.pack("<f" if floating else "<i", item.value))
    command = Command.CMD_SET_ADJ_VARS_VAL_F if floating else Command.CMD_SET_ADJ_VARS_VAL
    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")
    if need_confirmation:
        return self.request_raw(
            int(command),
            bytes(payload),
            timeout=timeout,
            route="adjvars",
            decoder=decode_confirmation,
        )
    return self.send_raw(int(command), bytes(payload), route="adjvars")


def set_adj_vars(
    self: SimpleBGC,
    variables: object,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Set several integer adjustable-variable values."""

    return _set_values(
        self, variables, floating=False, need_confirmation=need_confirmation, timeout=timeout
    )


def set_adj_var(
    self: SimpleBGC,
    id: int,
    value: int,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Set one integer adjustable-variable value."""

    return set_adj_vars(
        self, (AdjustableVariable(id, value),), need_confirmation=need_confirmation, timeout=timeout
    )


def set_adj_vars_float(
    self: SimpleBGC,
    variables: object,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Set several floating-point adjustable-variable values."""

    return _set_values(
        self, variables, floating=True, need_confirmation=need_confirmation, timeout=timeout
    )


def set_adj_var_float(
    self: SimpleBGC,
    id: int,
    value: float,
    *,
    need_confirmation: bool = False,
    timeout: float | None = 1.0,
) -> Future[CommandConfirmation | None]:
    """Set one floating-point adjustable-variable value."""

    return set_adj_vars_float(
        self,
        (AdjustableVariableFloat(id, value),),
        need_confirmation=need_confirmation,
        timeout=timeout,
    )


def _save(
    self: SimpleBGC, payload: bytes, need_confirmation: bool, timeout: float | None
) -> Future[CommandConfirmation | None]:
    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")
    if need_confirmation:
        return self.request_raw(
            int(Command.CMD_SAVE_PARAMS_3),
            payload,
            timeout=timeout,
            route="adjvars",
            decoder=decode_confirmation,
        )
    return self.send_raw(int(Command.CMD_SAVE_PARAMS_3), payload, route="adjvars")


def save_adj_vars(
    self: SimpleBGC, ids: object, *, need_confirmation: bool = False, timeout: float | None = 1.0
) -> Future[CommandConfirmation | None]:
    """Persist only the selected adjustable variables in controller memory."""

    return _save(self, bytes(normalize_adj_var_ids(ids, maximum=102)), need_confirmation, timeout)


def save_all_adj_vars(
    self: SimpleBGC, *, need_confirmation: bool = False, timeout: float | None = 1.0
) -> Future[CommandConfirmation | None]:
    """Persist every adjustable variable in controller memory."""

    return _save(self, b"", need_confirmation, timeout)


def _normalize_config(config: object) -> AdjustableVariablesConfig:
    if not isinstance(config, AdjustableVariablesConfig):
        raise TypeError("config must be an AdjustableVariablesConfig")
    if (
        len(config.trigger_slots) != 10
        or len(config.analog_slots) != 15
        or len(config.reserved) != 8
    ):
        raise ValueError(
            "config must contain 10 trigger slots, 15 analog slots, and 8 reserved bytes"
        )
    if not isinstance(config.reserved, bytes):
        raise TypeError("config.reserved must be bytes")
    for slot in config.trigger_slots:
        if (
            not isinstance(slot, AdjustableVariableTriggerSlot)
            or type(slot.source) is not int
            or not 0 <= slot.source <= 255
            or len(slot.actions) != 5
            or any(type(action) is not int or not 0 <= action <= 255 for action in slot.actions)
        ):
            raise ValueError("trigger slots must contain byte source and five byte actions")
    for slot in config.analog_slots:
        if not isinstance(slot, AdjustableVariableAnalogSlot) or any(
            type(value) is not int or not 0 <= value <= 255
            for value in (slot.source, slot.variable_id, slot.min_value, slot.max_value)
        ):
            raise ValueError("analog slots must contain byte values")
    return config


def _encode_config(config: object) -> bytes:
    config = _normalize_config(config)
    payload = bytearray()
    for slot in config.trigger_slots:
        payload.extend((slot.source, *slot.actions))
    for slot in config.analog_slots:
        payload.extend((slot.source, slot.variable_id, slot.min_value, slot.max_value))
    payload.extend(config.reserved)
    return bytes(payload)


def _decode_config(frame: WireFrame) -> AdjustableVariablesConfig:
    if len(frame.payload) != 128:
        raise ValueError("READ_ADJ_VARS_CFG response must contain 128 bytes")
    trigger_slots = tuple(
        AdjustableVariableTriggerSlot(payload[0], tuple(payload[1:6]))
        for payload in (frame.payload[offset : offset + 6] for offset in range(0, 60, 6))
    )
    analog_slots = tuple(
        AdjustableVariableAnalogSlot(*frame.payload[offset : offset + 4])
        for offset in range(60, 120, 4)
    )
    return AdjustableVariablesConfig(trigger_slots, analog_slots, frame.payload[120:])


def read_adj_vars_config(
    self: SimpleBGC, *, timeout: float | None = 1.0
) -> Future[AdjustableVariablesConfig]:
    """Read trigger and analog-slot adjustable-variable configuration."""

    return self.request_raw(
        int(Command.CMD_READ_ADJ_VARS_CFG), timeout=timeout, route="adjvars", decoder=_decode_config
    )


def write_adj_vars_config(
    self: SimpleBGC, config: object, *, need_confirmation: bool = False, timeout: float | None = 1.0
) -> Future[CommandConfirmation | None]:
    """Write trigger and analog-slot adjustable-variable configuration."""

    payload = _encode_config(config)
    if type(need_confirmation) is not bool:
        raise TypeError("need_confirmation must be bool")
    if need_confirmation:
        return self.request_raw(
            int(Command.CMD_WRITE_ADJ_VARS_CFG),
            payload,
            timeout=timeout,
            route="adjvars",
            decoder=decode_confirmation,
        )
    return self.send_raw(int(Command.CMD_WRITE_ADJ_VARS_CFG), payload, route="adjvars")


def get_adj_vars_state(
    self: SimpleBGC,
    trigger_slot: int,
    analog_source_id: int,
    analog_variable_id: int,
    lut_source_id: int,
    lut_variable_id: int,
    *,
    timeout: float | None = 1.0,
) -> Future[AdjustableVariablesState]:
    """Read the computed state of selected trigger, analog and LUT sources."""

    values = (trigger_slot, analog_source_id, analog_variable_id, lut_source_id, lut_variable_id)
    if any(type(value) is not int for value in values):
        raise TypeError("adjustable-variable state selectors must be integers")
    if (
        not 0 <= trigger_slot < 10
        or not 0 <= analog_source_id <= 0xFFFF
        or not 0 <= lut_source_id <= 0xFFFF
        or not 0 <= analog_variable_id <= 255
        or not 0 <= lut_variable_id <= 255
    ):
        raise ValueError("adjustable-variable state selectors are out of range")
    payload = struct.pack("<BHBHB", *values)

    def decode(frame: WireFrame) -> AdjustableVariablesState:
        if len(frame.payload) != 15:
            raise ValueError("ADJ_VARS_STATE response must contain 15 bytes")
        return AdjustableVariablesState(*struct.unpack("<hBhfhf", frame.payload))

    return self.request_raw(
        int(Command.CMD_ADJ_VARS_STATE), payload, timeout=timeout, route="adjvars", decoder=decode
    )


def _decode_info(frame: WireFrame) -> tuple[AdjustableVariableInfo, ...]:
    if not frame.payload:
        raise ValueError("ADJ_VARS_INFO response is empty")
    offset = 1
    result = []
    while offset < len(frame.payload):
        if offset + 10 > len(frame.payload):
            raise ValueError("ADJ_VARS_INFO response contains a truncated record")
        variable_id, name_length = frame.payload[offset : offset + 2]
        offset += 2 + name_length
        if offset + 8 > len(frame.payload):
            raise ValueError("ADJ_VARS_INFO response contains a truncated record")
        minimum, maximum, value = struct.unpack_from("<hhi", frame.payload, offset)
        offset += 8
        result.append(AdjustableVariableInfo(variable_id, minimum, maximum, value))
    return tuple(result)


def get_adj_vars_info(
    self: SimpleBGC, start_id: int = 0, *, timeout: float | None = 1.0
) -> Future[tuple[AdjustableVariableInfo, ...]]:
    """Read adjustable-variable metadata, following every controller page."""

    if type(start_id) is not int or not 0 <= start_id <= 255:
        raise ValueError("start_id must be an integer in range 0..255")
    result: Future[tuple[AdjustableVariableInfo, ...]] = Future()
    collected: list[AdjustableVariableInfo] = []

    def request_page(next_id: int) -> None:
        page = self.request_raw(
            int(Command.CMD_ADJ_VARS_INFO),
            bytes((next_id,)),
            timeout=timeout,
            route="adjvars",
            decoder=_decode_info,
        )

        def continuation(done: Future[tuple[AdjustableVariableInfo, ...]]) -> None:
            try:
                records = done.result()
                collected.extend(records)
                following = records[-1].id + 1 if records else 256
                if not records or following > 255 or following <= next_id:
                    result.set_result(tuple(collected))
                else:
                    request_page(following)
            except BaseException as error:
                result.set_exception(error)

        page.add_done_callback(continuation)

    request_page(start_id)
    return result
