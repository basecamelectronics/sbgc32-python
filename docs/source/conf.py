"""Sphinx configuration for the SimpleBGC32 Python API documentation."""

from __future__ import annotations

from enum import Enum
import inspect
from pathlib import Path
import re
import sys

DOCS_SOURCE = Path(__file__).resolve().parent
PROJECT_ROOT = DOCS_SOURCE.parents[1]
sys.path.insert(0, str(DOCS_SOURCE))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from theme_colors import CLASSIC_THEME_OPTIONS

project = "SimpleBGC32 Python API"
copyright = "BaseCam Electronics"
author = "Nikita Toporkov"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

autodoc_typehints = "signature"
autodoc_member_order = "bysource"
autodoc_class_signature = "mixed"
autoclass_content = "both"
toc_object_entries_show_parents = "hide"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

templates_path = ["_templates"]
exclude_patterns = ["_build"]
html_theme = "classic"
html_theme_options = CLASSIC_THEME_OPTIONS
html_static_path = ["_static"]
html_css_files = ["basecam.css"]


def _logical_result(annotation: str | None) -> str | None:
    """Show the value resolved by an asynchronous command, not its Future."""

    if annotation is None:
        return None
    match = re.fullmatch(r"(?:[\w.]+\.)?Future\[(.*)\]", annotation)
    return match.group(1) if match else annotation


def simplify_api_signature(
    app: object,
    what: str,
    name: str,
    obj: object,
    options: object,
    signature: str | None,
    return_annotation: str | None,
) -> tuple[str | None, str | None] | None:
    """Keep the reference focused on an operation and its logical result."""

    if what in {"function", "method"}:
        return "()", _logical_result(return_annotation)
    if what == "class":
        return "", return_annotation
    return None


_PARAMETER_TEXT = {
    "timeout": "Maximum time to wait for the controller response, in seconds.",
    "need_confirmation": "Whether the controller must acknowledge the command.",
    "confirm": "Explicit safety confirmation for a destructive operation.",
    "profile_id": "Controller profile to read or modify.",
    "config": "Structured configuration record for this command.",
    "parameters": "Validated raw parameter data for the selected command block.",
    "payload": "Raw SerialAPI payload bytes.",
    "data": "Decoded controller data to format or transmit.",
    "values": "Values to send to the controller.",
    "variables": "Adjustable-variable records to read, write or format.",
    "ids": "Adjustable-variable identifiers.",
    "id": "Protocol identifier of the selected item.",
    "address": "Start address in the selected controller memory area.",
    "size": "Number of bytes to read.",
    "block": "Zero-based profile parameter block number.",
    "mode": "Protocol mode that selects the operation behaviour.",
    "action": "Protocol action to perform.",
    "state": "Structured controller state to write or format.",
    "control": "Structured motion-control request.",
    "outputs": "Mapping of selected servo outputs to their values.",
    "slot": "One-based controller script or profile-set slot.",
    "message": "Bytes passed to the controller command.",
}

_EXAMPLE_ARGUMENTS = {
    "ids": "(1, 2)",
    "id": "1",
    "address": "0",
    "size": "16",
    "block": "0",
    "profile_id": "types.ProfileId.CURRENT",
    "payload": "b''",
    "message": "b'hello'",
    "slot": "1",
    "mode": "0",
    "action": "0",
    "value": "0",
    "target": "0",
    "command_id": "1",
    "max_devices": "13",
}

_VALUE_MEANINGS = {
    "MotorsOffMode": {
        "NORMAL": "Disable the motors normally.",
        "BREAK": "Stop the motors using braking.",
        "SAFE_STOP": "Use the controller safe-stop procedure.",
    }
}

_ENUM_CONTEXTS = {
    "SerialApiStatus": "Reports the SerialAPI communication outcome",
    "ControllerErrorCode": "Reports why the controller rejected a command",
    "TransparentCommandPort": "Selects the destination serial port",
    "TransparentCommandDevice": "Selects the destination device",
    "TransparentCommandFlag": "Controls transparent-command delivery",
    "EepromFileId": "Selects the controller file-system item",
    "ProfileId": "Selects a controller profile",
    "ProfileSet": "Selects a profile-set slot",
    "ProfileSetAction": "Selects the profile-set operation",
    "ProfileWritingAction": "Controls profile-writing mode",
    "ExternalImuCommandType": "Selects external-IMU message direction",
    "ExternalSensorCommandFlag": "Selects external-sensor message priority",
    "MotorsOffMode": "Selects how the main motors stop",
    "BeeperMode": "Adds a standard beeper signal",
    "AutoPidFlag": "Configures the legacy Auto PID operation",
    "AutoPid2Action": "Selects the Auto PID 2 operation",
    "AutoPid2AxisFlag": "Configures one Auto PID 2 axis",
    "AutoPid2GeneralFlag": "Configures Auto PID 2 behaviour",
    "SyncMotorAxis": "Selects the motor axis to synchronize",
    "DebugPortAction": "Starts or stops Debug Port output",
    "DebugPortFilter": "Suppresses this packet class on Debug Port",
    "ControlMode": "Selects CMD_CONTROL behaviour for one axis",
    "ControlFlag": "Adds a CMD_CONTROL axis option",
    "ControlConfigFlag": "Configures CMD_CONTROL_CONFIG behaviour",
    "ControlExtDataSet": "Includes this field in CMD_CONTROL_EXT",
    "ControlExtFlag": "Adds a CMD_CONTROL_EXT option",
    "ControlQuatFlag": "Adds a quaternion-control option",
    "ControlQuatConfigParameter": "Includes this quaternion-control setting",
    "ControlQuatConfigFlag": "Configures quaternion-control motion profiling",
    "ExternalMotor": "Selects this external motor ID",
    "ExternalMotorAction": "Selects the external-motor action",
    "ExternalMotorParameter": "Selects the external-motor payload format",
    "ExternalMotorsControlConfigParameter": "Includes this external-motor setting",
    "ExternalMotorsControlMode": "Selects external-motor control mode",
    "ConfirmationStatus": "Reports command-confirmation status",
    "RcInputSource": "Selects the RC input source",
    "ImuType": "Selects the IMU",
    "AhrsHelperDirection": "Selects AHRS Helper transfer direction",
    "AhrsHelperLocation": "Selects the AHRS Helper location",
    "AhrsHelperCorrection": "Selects AHRS Helper vector correction",
    "AhrsHelperTranslation": "Selects AHRS Helper vector translation",
    "AhrsHelperReference": "Selects the AHRS Helper reference frame",
    "AhrsHelperOption": "Adds an AHRS Helper option",
    "HelperDataFlag": "Selects the Helper Data coordinate-system option",
    "SelectImuAction": "Selects the IMU operation",
    "ControlQuatMode": "Selects quaternion-control mode",
    "ControlQuatStatusFlag": "Requests this quaternion-control status field",
    "DataStreamCommand": "Selects data produced by a periodic stream",
    "RealtimeDataCustomFlag": "Requests this custom realtime-data field",
    "CalibCoggingAction": "Selects the cogging-calibration operation",
    "CalibCoggingAxis": "Selects a cogging-calibration axis",
    "MenuCommandFlag": "Controls menu-command confirmation",
    "TriggerPin": "Selects the controller output pin",
    "TriggerPinState": "Selects the output electrical state",
    "ServoOutput": "Selects the servo output",
}

_VALUE_LABELS = {
    "TX_RX_OK": "command transmitted and reply received",
    "TX_BUS_BUSY_ERROR": "transmit bus is busy",
    "RX_EMPTY_BUFF_ERROR": "reply buffer is empty",
    "RX_BUFFER_REALTIME_ERROR": "realtime reply buffer error",
    "RX_HEADER_CHECKSUM_ERROR": "reply header checksum is invalid",
    "RX_PAYLOAD_CHECKSUM_ERROR": "reply payload checksum is invalid",
    "RX_NOT_FOUND_ERROR": "expected reply was not received",
    "RX_BUFFER_OVERFLOW_ERROR": "reply buffer overflow",
    "NO_ERROR": "no controller error",
    "CMD_SIZE": "invalid command size",
    "WRONG_PARAMS": "invalid command parameters",
    "CRYPTO": "cryptographic validation error",
    "UNKNOWN_COMMAND": "unsupported command identifier",
    "WRONG_STATE": "command is unavailable in the current controller state",
    "NOT_SUPPORTED": "feature is not supported by this controller",
    "OPERATION_FAILED": "controller operation failed",
    "NOT_RECEIVED": "confirmation has not arrived",
    "RECEIVED": "controller accepted the command",
    "ERROR": "controller returned an error confirmation",
}


def _annotation(annotation: object) -> str:
    """Format an annotation compactly for an autodoc field list."""

    if annotation is inspect.Parameter.empty:
        return "object"
    if isinstance(annotation, str):
        return annotation
    value = inspect.formatannotation(annotation)
    return value.removeprefix("typing.").replace("NoneType", "None")


def _parameter_description(parameter: inspect.Parameter) -> str:
    """Return a concise, stable description for a documented parameter."""

    if parameter.name in _PARAMETER_TEXT:
        return _PARAMETER_TEXT[parameter.name]
    if parameter.default is not inspect.Parameter.empty:
        return f"Optional {parameter.name.replace('_', ' ')} setting."
    return f"Value used for {parameter.name.replace('_', ' ')}."


def _example_argument(parameter: inspect.Parameter) -> str:
    """Choose a readable placeholder for a public API example."""

    return _EXAMPLE_ARGUMENTS.get(parameter.name, parameter.name)


def _logical_annotation(annotation: object) -> str:
    """Convert a Python annotation to the result displayed to API users."""

    if annotation is inspect.Signature.empty:
        return "None"
    return _logical_result(_annotation(annotation)) or "None"


def _function_errors(name: str, obj: object) -> list[tuple[str, str]]:
    """Document only errors that the function explicitly declares or raises."""

    source = inspect.getsource(obj)
    found = set(re.findall(r"raise\s+([A-Za-z_][A-Za-z0-9_]*)", source))
    descriptions = {
        "TypeError": "If an argument has an incompatible type.",
        "ValueError": "If an argument is outside the supported range or format.",
        "RuntimeError": "If the operation cannot run in the current local state.",
        "ConnectionError": "If the connection has already been closed.",
        "OSError": "If the serial transport cannot complete the operation.",
    }
    errors = [(error, descriptions[error]) for error in descriptions if error in found]
    if name in {
        "sbgc32.modules.service.request_motor_state",
        "sbgc32.modules.service.read_motor_state",
    }:
        errors.append(("CanNotSupportedError", "If the controller does not provide a CAN port."))
        errors.append(("ExternalMotorNotFoundError", "If the requested external motor does not reply."))
    if name in {
        "sbgc32.modules.service.scan_can_device",
        "sbgc32.modules.service.request_module_list",
    }:
        errors.append(("CanNotSupportedError", "If the controller does not provide a CAN port."))
    if name == "sbgc32.modules.service.scan_can_device":
        errors.append(("CanDeviceNotFoundError", "If no CAN device answers the scan request."))
    return errors


def _function_example(name: str, obj: object) -> list[str]:
    """Build a short example after the generated parameter and error tables."""

    signature = inspect.signature(obj)
    arguments = [
        _example_argument(parameter)
        for parameter in signature.parameters.values()
        if parameter.name not in {"self", "cls"}
        and parameter.default is inspect.Parameter.empty
        and parameter.kind not in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
    ]
    local_name = name.rsplit(".", 1)[-1]
    call = f"{local_name}({', '.join(arguments)})"
    result = _logical_annotation(signature.return_annotation)
    if name.startswith("sbgc32.modules.") or name.startswith("sbgc32.SimpleBGC."):
        expression = f"result = gimbal.{call}.result()"
    elif ".Formatter." in name:
        expression = f"text = gimbal.format.{call}"
    elif name.startswith("sbgc32.types."):
        expression = f"result = types.{call}"
    else:
        expression = f"result = {call}"
    return ["", "Example:", "", ".. code-block:: python", "", f"   {expression}", f"   # result: {result}"]


def describe_public_function(
    app: object,
    what: str,
    name: str,
    obj: object,
    options: object,
    lines: list[str],
) -> None:
    """Add parameter, result, error and example sections to each function."""

    if what not in {"function", "method"}:
        return
    signature = inspect.signature(obj)
    for parameter in signature.parameters.values():
        if parameter.name in {"self", "cls"}:
            continue
        lines.extend(
            (
                "",
                f":param {parameter.name}: {_parameter_description(parameter)}",
                f":type {parameter.name}: {_annotation(parameter.annotation)}",
            )
        )
    result = _logical_annotation(signature.return_annotation)
    lines.extend(("", f":returns: Logical command result: ``{result}``.", f":rtype: {result}"))
    for error_name, description in _function_errors(name, obj):
        lines.extend(("", f":raises {error_name}: {description}"))
    lines.extend(_function_example(name, obj))


def _value_meaning(class_name: str, member: Enum) -> str:
    """Give every enum member a readable meaning in the Values table."""

    specific = _VALUE_MEANINGS.get(class_name, {}).get(member.name)
    if specific:
        return specific
    label = _VALUE_LABELS.get(member.name, member.name.replace("_", " ").lower())
    context = _ENUM_CONTEXTS.get(class_name, f"Configures {class_name.replace('_', ' ')}")
    return f"{context}: {label}."


def describe_public_type(
    app: object,
    what: str,
    name: str,
    obj: object,
    options: object,
    lines: list[str],
) -> None:
    """Add useful prose and enum member names to generated type references."""

    if what != "class" or not name.startswith("sbgc32.types.") or not isinstance(obj, type):
        return
    if issubclass(obj, Enum):
        # ``Enum`` iteration omits zero-valued ``IntFlag`` members, while the
        # public API must document every name declared by the protocol.
        members = tuple(obj.__members__.values())
        if members:
            lines.extend(("", "**Values:**", "", ".. list-table::", "   :header-rows: 1", ""))
            lines.extend(("   * - Value", "     - Meaning"))
            for member in members:
                lines.extend(
                    (
                        f"   * - ``{member.name}`` = ``{member.value}``",
                        f"     - {_value_meaning(obj.__name__, member)}",
                    )
                )
    elif not lines:
        lines.append("Value object used to pass structured data to, or receive it from, the controller.")


def setup(app: object) -> None:
    app.connect("autodoc-process-signature", simplify_api_signature)
    app.connect("autodoc-process-docstring", describe_public_function)
    app.connect("autodoc-process-docstring", describe_public_type)
