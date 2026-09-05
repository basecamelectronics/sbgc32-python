from __future__ import annotations

from collections.abc import Sequence
from time import sleep

from . import _adjvars, _calib, _control, _eeprom, _imu, _profiles, _realtime, _service
from ._serial_api_library import NativeError
from .backends import create_backend
from .commands import Command, MenuCommands
from .types import (
    AdjustableVariable,
    AdjustableVariableFloat,
    AdjustableVariableInfo,
    AdjustableVariablesConfig,
    AdjustableVariablesState,
    AhrsHelper,
    Angles,
    AnglesExt,
    AutoPid2Config,
    AutoPidConfig,
    AutoPidState,
    BeeperMode,
    BoardInfo,
    BoardInfo3,
    CalibInfo,
    CanDeviceScan,
    CanModuleInfo,
    CommandConfirmation,
    ControlAxis,
    ControlConfig,
    ControlExt,
    ControlQuat,
    ControlQuatConfig,
    ControlQuatStatus,
    ControlQuatStatusFlag,
    DataStreamConfig,
    DebugPortPacket,
    DebugVarInfo,
    EepromFile,
    EepromFileId,
    ExternalImuCommandType,
    ExternalImuDebugInfo,
    ExternalMotorAction,
    ExternalMotorControl,
    ExternalMotorsControlConfig,
    ExternalSensorCommandFlag,
    GyroCorrection,
    HelperData,
    HelperDataExt,
    ImuType,
    MenuExecutionResult,
    MotorsOffMode,
    PidValues,
    ProfileId,
    ProfileParameters,
    ProfileSet,
    ProfileSetAction,
    ProfileWritingAction,
    RealtimeData3,
    RealtimeData4,
    RealtimeDataCustom,
    RealtimeDataCustomFlag,
    ScriptDebugInfo,
    SelectImuAction,
    ServoOutput,
    StateVars,
    SyncMotorsConfig,
    TriggerPin,
    TriggerPinState,
)


class SimpleBGC:
    """Connection-oriented public interface for a SimpleBGC controller.

    Create an instance for one serial connection, use its command methods, and
    close it explicitly or through a ``with`` statement.
    """

    def __init__(
        self,
        port: str,
        baud_rate: int = 115200,
        startup_delay: float = 1.0,
        backend: str = "pyserial",
    ) -> None:
        """Open a Serial API connection to a SimpleBGC controller.

        Args:
            port: System serial-port name, for example ``"COM4"``.
            baud_rate: Serial-port speed in bits per second.
            startup_delay: Delay after opening the port, in seconds.
            backend: Transport implementation, ``"pyserial"`` or
                ``"native_win"`` where available.

        Raises:
            ValueError: If ``startup_delay`` is negative or the backend is
                unsupported.
            OSError: If the serial port cannot be opened.
        """

        if startup_delay < 0:
            raise ValueError("startup_delay must be non-negative")
        self._backend = create_backend(backend)
        self._native = self._backend.library
        self._device = self._backend.open(port, baud_rate)
        sleep(startup_delay)
        self._closed = False
        self._debug_script_slot: int | None = None

    # CONTROL MODULE
    def set_api_virtual_channels(self, values: object) -> None:
        """Set standard virtual RC channels.

        Args:
            values: One to 32 values in ``-500..500``; use ``None`` to leave
                a channel unchanged.

        Raises:
            ValueError: If the channel count or a value is invalid.
        """
        _control.set_api_virtual_channels(self, values)

    def control(
        self,
        axes: tuple[ControlAxis, ControlAxis, ControlAxis],
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Send roll, pitch, and yaw control commands.

        Args:
            axes: Three :class:`ControlAxis` records in roll, pitch, yaw order.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.

        Raises:
            TypeError: If the axis records have an invalid type.
            ValueError: If the axis values are outside the protocol range.
        """
        return _control.control(self, axes, need_confirmation=need_confirmation)

    def configure_control(
        self,
        config: ControlConfig | None = None,
        *,
        confirm_control: bool | None = None,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Configure how the controller processes ``CMD_CONTROL``.

        Args:
            config: Command configuration. ``None`` uses the default structure.
            confirm_control: Enable or disable controller confirmations, or leave
                the existing setting unchanged with ``None``.
            need_confirmation: Request a confirmation for this write.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.

        Raises:
            TypeError: If ``config`` or an option has an invalid type.
            ValueError: If a configuration value is outside its protocol range.
        """
        return _control.configure_control(
            self,
            config,
            confirm_control=confirm_control,
            need_confirmation=need_confirmation,
        )

    def control_config(
        self,
        config: ControlConfig | None = None,
        *,
        confirm_control: bool | None = None,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Alias for :meth:`configure_control`.

        Args:
            config: Control-command configuration.
            confirm_control: Controller confirmation setting.
            need_confirmation: Request a confirmation for this write.

        Returns:
            The result of :meth:`configure_control`.
        """
        return self.configure_control(
            config,
            confirm_control=confirm_control,
            need_confirmation=need_confirmation,
        )

    def control_ext(self, control: ControlExt) -> None:
        """Send extended raw control values.

        Args:
            control: Extended control structure and its data-set mask.

        Raises:
            TypeError: If ``control`` is not a :class:`ControlExt`.
            ValueError: If its data-set or axis values are invalid.
        """
        _control.control_ext(self, control)

    def control_quat(
        self, control: ControlQuat, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Send quaternion attitude and speed control.

        Args:
            control: Quaternion control structure.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _control.control_quat(self, control, need_confirmation=need_confirmation)

    def configure_control_quat(
        self, config: ControlQuatConfig, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Configure quaternion-control limits and filters.

        Args:
            config: Quaternion-control configuration.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _control.configure_control_quat(self, config, need_confirmation=need_confirmation)

    def ext_motors_action(
        self,
        motors: int,
        action: ExternalMotorAction | int,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Apply an action to selected external motors.

        Args:
            motors: External-motor bit mask.
            action: Requested :class:`ExternalMotorAction`.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _control.ext_motors_action(self, motors, action, need_confirmation=need_confirmation)

    def control_ext_motors(
        self,
        control: ExternalMotorControl,
        motors: int,
        data_set: int = 0,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Send a raw setpoint to selected external motors.

        Args:
            control: External-motor setpoint structure.
            motors: External-motor bit mask.
            data_set: Firmware data-set mask.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _control.control_ext_motors(
            self, control, motors, data_set, need_confirmation=need_confirmation
        )

    def configure_ext_motors(
        self, config: ExternalMotorsControlConfig, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Configure selected external motors.

        Args:
            config: External-motor configuration.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _control.configure_ext_motors(self, config, need_confirmation=need_confirmation)

    def set_api_virtual_channels_hr(self, values: object) -> None:
        """Set high-resolution virtual RC channels.

        Args:
            values: One to 32 values in ``-16384..16384``; ``None`` leaves a
                channel unchanged.

        Raises:
            ValueError: If the channel count or a value is invalid.
        """
        _control.set_api_virtual_channels_hr(self, values)

    # ADJVAR MODULE
    def get_adj_vars(self, ids: object) -> tuple[AdjustableVariable, ...]:
        """Read integer adjustable variables.

        Args:
            ids: One to 40 distinct variable identifiers.

        Returns:
            Variable records in request order.

        Raises:
            ValueError: If the identifiers are invalid or duplicated.
        """
        return _adjvars.get_adj_vars(self, ids)

    def get_adj_var(self, id: int) -> AdjustableVariable:
        """Read one integer adjustable variable.

        Args:
            id: Adjustable-variable identifier.

        Returns:
            The requested variable record.

        Raises:
            ValueError: If ``id`` is outside ``0..255``.
        """
        return _adjvars.get_adj_var(self, id)

    def set_adj_vars(
        self, variables: object, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Write integer adjustable variables to controller RAM.

        Args:
            variables: One to 40 :class:`AdjustableVariable` records.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.

        Raises:
            ValueError: If variables are invalid, duplicated, or out of range.
        """
        return _adjvars.set_adj_vars(self, variables, need_confirmation=need_confirmation)

    def set_adj_var(
        self, id: int, value: int, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Write one integer adjustable variable to controller RAM.

        Args:
            id: Adjustable-variable identifier.
            value: Signed 32-bit raw value.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.

        Raises:
            ValueError: If the identifier or value is invalid.
        """
        return _adjvars.set_adj_var(self, id, value, need_confirmation=need_confirmation)

    def save_adj_vars(
        self, ids: object, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Persist selected adjustable variables to controller memory.

        Args:
            ids: One to 102 variable identifiers to save.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.

        Raises:
            ValueError: If the identifiers are invalid or duplicated.
        """
        return _adjvars.save_adj_vars(self, ids, need_confirmation=need_confirmation)

    def save_all_adj_vars(self, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """Persist all active unsaved adjustable variables.

        Args:
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _adjvars.save_all_adj_vars(self, need_confirmation=need_confirmation)

    def get_adj_vars_float(self, ids: object) -> tuple[AdjustableVariableFloat, ...]:
        """Read floating-point adjustable variables.

        Args:
            ids: One to 40 distinct variable identifiers.

        Returns:
            Variable records in request order.

        Raises:
            ValueError: If the identifiers are invalid or duplicated.
        """
        return _adjvars.get_adj_vars_float(self, ids)

    def get_adj_var_float(self, id: int) -> AdjustableVariableFloat:
        """Read one floating-point adjustable variable.

        Args:
            id: Adjustable-variable identifier.

        Returns:
            The requested variable record.
        """
        return _adjvars.get_adj_var_float(self, id)

    def set_adj_vars_float(
        self, variables: object, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Write floating-point adjustable variables to controller RAM.

        Args:
            variables: One to 40 :class:`AdjustableVariableFloat` records.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _adjvars.set_adj_vars_float(self, variables, need_confirmation=need_confirmation)

    def set_adj_var_float(
        self, id: int, value: float, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Write one floating-point adjustable variable to controller RAM.

        Args:
            id: Adjustable-variable identifier.
            value: Finite floating-point value.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _adjvars.set_adj_var_float(self, id, value, need_confirmation=need_confirmation)

    def read_adj_vars_config(self) -> AdjustableVariablesConfig:
        """Read adjustable-variable trigger and analog-slot configuration.

        Returns:
            The complete :class:`AdjustableVariablesConfig` structure.
        """
        return _adjvars.read_adj_vars_config(self)

    def write_adj_vars_config(
        self, config: AdjustableVariablesConfig, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Write adjustable-variable trigger and analog-slot configuration.

        Args:
            config: Complete configuration structure.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _adjvars.write_adj_vars_config(self, config, need_confirmation=need_confirmation)

    def get_adj_vars_state(
        self,
        trigger_slot: int,
        analog_source_id: int,
        analog_variable_id: int,
        lut_source_id: int,
        lut_variable_id: int,
    ) -> AdjustableVariablesState:
        """Read adjustable-variable runtime state for selected sources.

        Args:
            trigger_slot: Trigger slot to inspect.
            analog_source_id: Analog source identifier.
            analog_variable_id: Variable mapped from that source.
            lut_source_id: Lookup-table source identifier.
            lut_variable_id: Lookup-table variable identifier.

        Returns:
            Current :class:`AdjustableVariablesState` values.
        """
        return _adjvars.get_adj_vars_state(
            self,
            trigger_slot,
            analog_source_id,
            analog_variable_id,
            lut_source_id,
            lut_variable_id,
        )

    def get_adj_vars_info(self, start_id: int = 0) -> tuple[AdjustableVariableInfo, ...]:
        """Read metadata and ranges for available integer variables.

        Args:
            start_id: First variable identifier to query.

        Returns:
            Firmware-reported variable metadata records.
        """
        return _adjvars.get_adj_vars_info(self, start_id)

    def format_adj_vars(
        self, variables: Sequence[AdjustableVariable | AdjustableVariableFloat]
    ) -> str:
        """Format adjustable-variable values as a text table.

        Args:
            variables: Previously read integer or floating-point records.

        Returns:
            A formatted text table.
        """
        return _adjvars.format_adj_vars(variables)

    def format_adj_vars_info(
        self, variables: Sequence[AdjustableVariableInfo] | None = None
    ) -> str:
        """Format adjustable-variable metadata.

        Args:
            variables: Metadata to format. ``None`` requests fresh metadata.

        Returns:
            A formatted text table.
        """
        return _adjvars.format_adj_vars_info(
            self.get_adj_vars_info() if variables is None else variables
        )

    def format_adj_vars_config(self, config: AdjustableVariablesConfig | None = None) -> str:
        """Format adjustable-variable configuration.

        Args:
            config: Configuration to format. ``None`` reads it first.

        Returns:
            A formatted text table.
        """
        return _adjvars.format_adj_vars_config(
            self.read_adj_vars_config() if config is None else config
        )

    def format_adj_vars_state(self, state: AdjustableVariablesState) -> str:
        """Format adjustable-variable runtime state.

        Args:
            state: Previously read runtime state.

        Returns:
            A formatted text table.
        """
        return _adjvars.format_adj_vars_state(state)

    # EEPROM MODULE
    def read_i2c_register(self, device_address: int, register_address: int, size: int) -> bytes:
        """Read bytes from an I²C device register.

        Args:
            device_address: 8-bit I²C device address.
            register_address: 8-bit register address.
            size: Number of bytes to read, from 1 through 240.

        Returns:
            The raw register bytes.
        """
        return _eeprom.read_i2c_register(self, device_address, register_address, size)

    def write_i2c_register(
        self,
        device_address: int,
        register_address: int,
        data: bytes,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Write bytes to an I²C device register.

        Args:
            device_address: 8-bit I²C device address.
            register_address: 8-bit register address.
            data: One to 240 bytes to write.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _eeprom.write_i2c_register(
            self,
            device_address,
            register_address,
            data,
            need_confirmation=need_confirmation,
        )

    def read_eeprom(self, address: int, size: int = 64) -> bytes:
        """Read one or more aligned EEPROM pages.

        Args:
            address: 64-byte aligned EEPROM address.
            size: Aligned read size from 64 through 192 bytes.

        Returns:
            Raw EEPROM bytes.

        Raises:
            ValueError: If the requested range is not page aligned or valid.
        """
        return _eeprom.read_eeprom(self, address, size)

    def write_eeprom(
        self,
        address: int,
        data: bytes,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Write one or more aligned EEPROM pages.

        Args:
            address: 64-byte aligned EEPROM address.
            data: From 64 through 192 bytes.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _eeprom.write_eeprom(self, address, data, need_confirmation=need_confirmation)

    def read_external_data(self) -> bytes:
        """Read the controller's 128-byte external-data area.

        Returns:
            The raw 128-byte data area.
        """
        return _eeprom.read_external_data(self)

    def write_external_data(
        self, data: bytes, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Write the controller's external-data area.

        Args:
            data: Exactly 128 bytes.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _eeprom.write_external_data(self, data, need_confirmation=need_confirmation)

    def read_file(
        self,
        file_id: EepromFileId | int,
        page_offset: int = 0,
        max_size: int = 240,
    ) -> EepromFile:
        """Read one file-system chunk from the controller.

        Args:
            file_id: Firmware file identifier.
            page_offset: First file page to read.
            max_size: Maximum number of bytes to return, from 1 through 240.

        Returns:
            The returned :class:`EepromFile` chunk and its firmware status.
        """
        return _eeprom.read_file(self, file_id, page_offset, max_size)

    def write_file(
        self,
        file_id: EepromFileId | int,
        data: bytes,
        *,
        page_offset: int = 0,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Write one file-system chunk to the controller.

        Args:
            file_id: Firmware file identifier.
            data: One to 240 bytes to write.
            page_offset: Destination page offset.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _eeprom.write_file(
            self,
            file_id,
            data,
            page_offset=page_offset,
            need_confirmation=need_confirmation,
        )

    def clear_file_system(self, *, confirm: bool = False) -> None:
        """Delete every controller file-system entry.

        Args:
            confirm: Must be explicitly ``True`` to perform this irreversible
                operation.

        Raises:
            ValueError: If ``confirm`` is not ``True``.
        """
        _eeprom.clear_file_system(self, confirm=confirm)

    # PROFILES MODULE
    def read_profile_names(self) -> tuple[str, str, str, str, str]:
        """Read the five controller profile names.

        Returns:
            UTF-8 profile names in profile-number order.
        """
        return _profiles.read_profile_names(self)

    def write_profile_names(
        self,
        names: Sequence[str],
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Write all five controller profile names.

        Args:
            names: Exactly five strings, up to 47 UTF-8 bytes each.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _profiles.write_profile_names(self, names, need_confirmation=need_confirmation)

    def manage_profile_set(
        self,
        slot: ProfileSet | int,
        action: ProfileSetAction | int,
        *,
        need_confirmation: bool = False,
        confirm: bool = False,
    ) -> CommandConfirmation | None:
        """Manage a stored controller profile set.

        Args:
            slot: Profile-set slot.
            action: Requested profile-set action.
            need_confirmation: Request a controller confirmation.
            confirm: Must be ``True`` when clearing a profile-set slot.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _profiles.manage_profile_set(
            self, slot, action, need_confirmation=need_confirmation, confirm=confirm
        )

    def set_profile_writing(
        self,
        action: ProfileWritingAction | int,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Enable or disable controller profile-writing mode.

        Args:
            action: Start or stop :class:`ProfileWritingAction`.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _profiles.set_profile_writing(self, action, need_confirmation=need_confirmation)

    def read_profile_parameter_block(
        self,
        block: int,
        profile_id: ProfileId | int = ProfileId.CURRENT,
    ) -> bytes:
        """Read one raw profile-parameter block.

        Args:
            block: Block number from 0 through 3.
            profile_id: Profile to read; defaults to the active profile.

        Returns:
            Exact-size raw parameter bytes for the selected block.
        """
        return _profiles.read_profile_parameter_block(self, block, profile_id)

    def write_profile_parameter_block(
        self,
        block: int,
        parameters: bytes,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Write one raw profile-parameter block.

        Args:
            block: Block number from 0 through 3.
            parameters: Exact-size raw bytes for that block.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _profiles.write_profile_parameter_block(
            self, block, parameters, need_confirmation=need_confirmation
        )

    def read_params_3(self, profile_id: ProfileId | int = ProfileId.CURRENT) -> bytes:
        """Read the ``PARAMS_3`` block.

        Args:
            profile_id: Profile to read; defaults to the active profile.

        Returns:
            The 134-byte raw block.
        """
        return _profiles.read_params_3(self, profile_id)

    def read_params_ext(self, profile_id: ProfileId | int = ProfileId.CURRENT) -> bytes:
        """Read the ``PARAMS_EXT`` block.

        Args:
            profile_id: Profile to read; defaults to the active profile.

        Returns:
            The 104-byte raw block.
        """
        return _profiles.read_params_ext(self, profile_id)

    def read_params_ext2(self, profile_id: ProfileId | int = ProfileId.CURRENT) -> bytes:
        """Read the ``PARAMS_EXT2`` block.

        Args:
            profile_id: Profile to read; defaults to the active profile.

        Returns:
            The 151-byte raw block.
        """
        return _profiles.read_params_ext2(self, profile_id)

    def read_params_ext3(self, profile_id: ProfileId | int = ProfileId.CURRENT) -> bytes:
        """Read the ``PARAMS_EXT3`` block.

        Args:
            profile_id: Profile to read; defaults to the active profile.

        Returns:
            The 221-byte raw block.
        """
        return _profiles.read_params_ext3(self, profile_id)

    def write_params_3(
        self, parameters: bytes, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Write the ``PARAMS_3`` block.

        Args:
            parameters: Exactly 134 raw bytes.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _profiles.write_params_3(self, parameters, need_confirmation=need_confirmation)

    def write_params_ext(
        self, parameters: bytes, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Write the ``PARAMS_EXT`` block.

        Args:
            parameters: Exactly 104 raw bytes.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _profiles.write_params_ext(self, parameters, need_confirmation=need_confirmation)

    def write_params_ext2(
        self, parameters: bytes, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Write the ``PARAMS_EXT2`` block.

        Args:
            parameters: Exactly 151 raw bytes.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _profiles.write_params_ext2(self, parameters, need_confirmation=need_confirmation)

    def write_params_ext3(
        self, parameters: bytes, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Write the ``PARAMS_EXT3`` block.

        Args:
            parameters: Exactly 221 raw bytes.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _profiles.write_params_ext3(self, parameters, need_confirmation=need_confirmation)

    def read_profile_parameters(
        self, profile_id: ProfileId | int = ProfileId.CURRENT
    ) -> ProfileParameters:
        """Read all four raw parameter blocks for one profile.

        Args:
            profile_id: Profile to read; defaults to the active profile.

        Returns:
            A :class:`ProfileParameters` structure.
        """
        return _profiles.read_profile_parameters(self, profile_id)

    def write_profile_parameters(
        self,
        parameters: ProfileParameters,
        *,
        need_confirmation: bool = False,
    ) -> None:
        """Write all four raw parameter blocks for the active profile.

        Args:
            parameters: Exact-size blocks to write.
            need_confirmation: Request confirmation for each block write.

        Raises:
            TypeError: If ``parameters`` is not :class:`ProfileParameters`.
            ValueError: If a block has an invalid size.
        """
        _profiles.write_profile_parameters(self, parameters, need_confirmation=need_confirmation)

    def use_profile_defaults(
        self, profile_id: ProfileId | int = ProfileId.CURRENT, *, confirm: bool = False
    ) -> None:
        """Restore firmware defaults for a profile.

        Args:
            profile_id: Profile to reset; defaults to the active profile.
            confirm: Must be explicitly ``True``.

        Raises:
            ValueError: If ``confirm`` is not ``True``.
        """
        _profiles.use_profile_defaults(self, profile_id, confirm=confirm)

    def format_profile_names(self, names: tuple[str, str, str, str, str] | None = None) -> str:
        """Format five profile names as a text table.

        Args:
            names: Names to format. ``None`` reads them first.

        Returns:
            A formatted text table.
        """
        return _profiles.format_profile_names(self.read_profile_names() if names is None else names)

    def format_profile_parameters(self, parameters: ProfileParameters | None = None) -> str:
        """Format raw profile-block metadata as a text table.

        Args:
            parameters: Parameter blocks to format. ``None`` reads them first.

        Returns:
            A formatted text table.
        """
        return _profiles.format_profile_parameters(
            self.read_profile_parameters() if parameters is None else parameters
        )

    # IMU MODULE
    def request_ext_imu_debug(self) -> ExternalImuDebugInfo:
        """Read external-IMU diagnostic data.

        Returns:
            Current :class:`ExternalImuDebugInfo` values.
        """
        return _imu.request_ext_imu_debug(self)

    def send_ext_imu_command(
        self,
        command_id: int,
        payload: bytes = b"",
        *,
        command_type: ExternalImuCommandType | int = ExternalImuCommandType.TX,
        response_size: int | None = None,
    ) -> tuple[int, bytes] | None:
        """Send a command to the external IMU.

        Args:
            command_id: 8-bit external-IMU command identifier.
            payload: Up to 254 command bytes.
            command_type: Transmit, receive, or transmit/receive mode.
            response_size: Required receive size for ``RX`` mode.

        Returns:
            ``None`` for transmit-only commands; otherwise response ID and data.

        Raises:
            ValueError: If the mode, payload, or response size is incompatible.
        """
        return _imu.send_ext_imu_command(
            self,
            command_id,
            payload,
            command_type=command_type,
            response_size=response_size,
        )

    def send_ext_sens_command(
        self,
        command_id: int,
        payload: bytes = b"",
        *,
        flags: ExternalSensorCommandFlag | int = ExternalSensorCommandFlag.LOW_PRIORITY,
        command_type: ExternalImuCommandType | int = ExternalImuCommandType.TX,
        response_size: int | None = None,
    ) -> tuple[int, bytes] | None:
        """Send a command to an external sensor.

        Args:
            command_id: 8-bit external-sensor command identifier.
            payload: Up to 254 command bytes.
            flags: External-sensor command flags.
            command_type: Transmit, receive, or transmit/receive mode.
            response_size: Required receive size for ``RX`` mode.

        Returns:
            ``None`` for transmit-only commands; otherwise response ID and data.
        """
        return _imu.send_ext_sens_command(
            self,
            command_id,
            payload,
            flags=flags,
            command_type=command_type,
            response_size=response_size,
        )

    def format_ext_imu_debug(self, info: ExternalImuDebugInfo | None = None) -> str:
        """Format external-IMU diagnostics.

        Args:
            info: Diagnostic data to format. ``None`` requests it first.

        Returns:
            A formatted text table.
        """
        return _imu.format_ext_imu_debug(self.request_ext_imu_debug() if info is None else info)

    def get_ahrs_helper(self, mode: int = 0) -> AhrsHelper:
        """Read AHRS reference vectors.

        Args:
            mode: Packed GET AHRS-helper mode, normally built by
                :func:`pack_ahrs_helper_mode`.

        Returns:
            The controller :class:`AhrsHelper` structure.
        """
        return _imu.get_ahrs_helper(self, mode)

    def set_ahrs_helper(self, helper: AhrsHelper, mode: int = 1) -> None:
        """Write AHRS reference vectors.

        Args:
            helper: Reference vectors to write.
            mode: Packed SET AHRS-helper mode.

        Raises:
            ValueError: If ``mode`` does not select SET operation.
        """
        _imu.set_ahrs_helper(self, helper, mode)

    def correction_gyro(self, correction: GyroCorrection) -> None:
        """Apply a gyro zero correction for one IMU.

        Args:
            correction: IMU type and signed 16-bit correction values.

        Raises:
            TypeError: If ``correction`` is not :class:`GyroCorrection`.
            ValueError: If an IMU or correction value is invalid.
        """
        _imu.correction_gyro(self, correction)

    def provide_helper_data(self, data: HelperData) -> None:
        """Provide standard frame helper data to the controller.

        Args:
            data: Frame acceleration and angle values.

        Raises:
            TypeError: If ``data`` is not :class:`HelperData`.
            ValueError: If a value is outside the signed 16-bit range.
        """
        _imu.provide_helper_data(self, data)

    def provide_helper_data_ext(self, data: HelperDataExt) -> None:
        """Provide extended frame helper data to the controller.

        Args:
            data: Extended acceleration, angle, speed, and heading values.

        Raises:
            TypeError: If ``data`` is not :class:`HelperDataExt`.
            ValueError: If a value or data flag is invalid.
        """
        _imu.provide_helper_data_ext(self, data)

    def format_ahrs_helper(self, helper: AhrsHelper | None = None) -> str:
        """Format AHRS reference vectors.

        Args:
            helper: Vectors to format. ``None`` reads them first.

        Returns:
            A formatted text table.
        """
        return _imu.format_ahrs_helper(self.get_ahrs_helper() if helper is None else helper)

    # CALIBRATION MODULE
    def request_calib_info(self, imu_type: ImuType | int = ImuType.MAIN) -> CalibInfo:
        """Read calibration progress and status for one IMU.

        Args:
            imu_type: Main or frame IMU.

        Returns:
            Current :class:`CalibInfo` data.

        Raises:
            ValueError: If ``imu_type`` is not main or frame.
        """
        return _calib.request_calib_info(self, imu_type)

    def calib_acc(self) -> None:
        """Start accelerometer calibration.

        Returns:
            ``None``. Poll :meth:`request_calib_info` for progress.
        """
        _calib.calib_acc(self)

    def calib_gyro(self) -> None:
        """Start gyroscope calibration.

        Returns:
            ``None``. Poll :meth:`request_calib_info` for progress.
        """
        _calib.calib_gyro(self)

    def calib_mag(self) -> None:
        """Start magnetometer calibration.

        Returns:
            ``None``. Poll :meth:`request_calib_info` for progress.
        """
        _calib.calib_mag(self)

    def calib_poles(self) -> None:
        """Start motor-pole calibration.

        Returns:
            ``None``. The procedure runs on the controller.
        """
        _calib.calib_poles(self)

    def calib_offset(self) -> None:
        """Start motor-offset calibration.

        Returns:
            ``None``. The procedure runs on the controller.
        """
        _calib.calib_offset(self)

    def calib_encoders_offset(self, motor: int = 255) -> None:
        """Start encoder-offset calibration.

        Args:
            motor: Axis ``0``, ``1``, ``2``, or ``255`` for every axis.

        Raises:
            ValueError: If ``motor`` is not a valid axis selector.
        """
        _calib.calib_encoders_offset(self, motor)

    def calib_encoders_fld_offset(self) -> None:
        """Start field-oriented encoder-offset calibration.

        Returns:
            ``None``. The procedure runs on the controller.
        """
        _calib.calib_encoders_fld_offset(self)

    def calib_bat(
        self, voltage: int, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Calibrate the battery-voltage measurement.

        Args:
            voltage: Reference voltage in 0.01 V units.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.

        Raises:
            ValueError: If ``voltage`` is outside ``0..65535``.
        """
        return _calib.calib_bat(self, voltage, need_confirmation=need_confirmation)

    def calib_orient_corr(self, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """Start orientation-correction calibration.

        Args:
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _calib.calib_orient_corr(self, need_confirmation=need_confirmation)

    def calib_acc_ext_ref(
        self, reference: tuple[int, int, int], *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Calibrate accelerometer data against an external reference.

        Args:
            reference: Three signed 16-bit acceleration reference values.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _calib.calib_acc_ext_ref(self, reference, need_confirmation=need_confirmation)

    def calib_cogging(
        self, cogging: object, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Start or remove motor-cogging calibration data.

        Args:
            cogging: Cogging action, selected axes, and per-axis configuration.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _calib.calib_cogging(self, cogging, need_confirmation=need_confirmation)

    def format_calib_info(self, info: CalibInfo | None = None) -> str:
        """Format calibration progress and status.

        Args:
            info: Calibration data to format. ``None`` reads it first.

        Returns:
            A formatted text table.
        """
        return _calib.format_calib_info(self.request_calib_info() if info is None else info)

    # REALTIME MODULE
    def get_angles(self) -> Angles:
        """Read the current IMU, target, and target-speed angles.

        Returns:
            An :class:`Angles` object with named roll, pitch, and yaw values.
        """
        return _realtime.get_angles(self)

    def get_angles_ext(self) -> AnglesExt:
        """Read the extended angle representation.

        Returns:
            An :class:`AnglesExt` object with raw per-axis values and
            converted IMU, target, and frame-camera angle properties.
        """
        return _realtime.get_angles_ext(self)

    def format_angles(self, angles: Angles | None = None) -> str:
        """Format current or supplied angle values.

        Args:
            angles: Angles to format. ``None`` reads them first.

        Returns:
            A formatted text table.
        """
        return _realtime.format_angles(self.get_angles() if angles is None else angles)

    def get_realtime_data(self) -> RealtimeData3:
        """Read ``REALTIME_DATA_3`` using its legacy method name.

        Returns:
            The same :class:`RealtimeData3` result as
            :meth:`get_realtime_data_3`.
        """
        return _realtime.get_realtime_data_3(self)

    def get_realtime_data_3(self) -> RealtimeData3:
        """Read the fixed ``REALTIME_DATA_3`` controller packet.

        Returns:
            A :class:`RealtimeData3` object. Most fields preserve their raw
            protocol representation; ``bat_level`` is expressed in
            centivolts.
        """
        return _realtime.get_realtime_data_3(self)

    def get_realtime_data_4(self) -> RealtimeData4:
        """Read the extended ``REALTIME_DATA_4`` controller packet.

        Returns:
            A :class:`RealtimeData4` object, including every
            :class:`RealtimeData3` field.
        """
        return _realtime.get_realtime_data_4(self)

    def format_realtime_data(self, data: RealtimeData3 | RealtimeData4 | None = None) -> str:
        """Format current or supplied realtime data.

        Args:
            data: ``REALTIME_DATA_3`` or ``REALTIME_DATA_4`` to format.
                ``None`` requests ``REALTIME_DATA_3`` first.

        Returns:
            A formatted text table.
        """
        return _realtime.format_realtime_data(self.get_realtime_data() if data is None else data)

    def get_realtime_data_custom(self, flags: RealtimeDataCustomFlag | int) -> RealtimeDataCustom:
        """Request a realtime packet containing selected fields.

        Args:
            flags: A combination of :class:`RealtimeDataCustomFlag` members.

        Returns:
            A :class:`RealtimeDataCustom` object whose ``fields`` mapping is
            keyed by the selected flags.

        Raises:
            ValueError: If ``flags`` contains unsupported bits or the selected
                protocol payload is larger than 255 bytes.
        """
        return _realtime.get_realtime_data_custom(self, flags)

    def read_rc_inputs(self, sources: object) -> tuple[int | None, ...]:
        """Read RC sources as normalized ``-500`` to ``500`` values.

        Args:
            sources: An iterable containing from one to 42 RC source IDs or
                :class:`RcInputSource` values.

        Returns:
            Values in the same order as ``sources``. An inactive source is
            represented by ``None``.

        Raises:
            TypeError: If ``sources`` is not an iterable.
            ValueError: If the number or values of source IDs are invalid.
        """
        return _realtime.read_rc_inputs(self, sources)

    def start_data_stream(
        self, config: DataStreamConfig, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Start a periodic controller data stream.

        Args:
            config: Command, interval, command-specific configuration, and
                synchronization setting for the stream.
            need_confirmation: Request ``CMD_CONFIRM`` from firmware that
                supports confirmations.

        Returns:
            A command confirmation when requested and supported; otherwise
            ``None``.
        """
        return _realtime.start_data_stream(self, config, need_confirmation=need_confirmation)

    def stop_data_stream(
        self, config: DataStreamConfig, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Stop the stream described by ``config``.

        Args:
            config: The same stream configuration used to start the stream.
            need_confirmation: Request ``CMD_CONFIRM`` from firmware that
                supports confirmations.

        Returns:
            A command confirmation when requested and supported; otherwise
            ``None``.
        """
        return _realtime.stop_data_stream(self, config, need_confirmation=need_confirmation)

    def read_data_stream(
        self,
        config: DataStreamConfig,
        size: int | None = None,
    ) -> bytes:
        """Read one raw payload from a configured data stream.

        Args:
            config: The stream configuration. It determines the payload size
                for known realtime and helper stream commands.
            size: Required payload size for commands whose size is not known
                to the library. Ignored for known commands.

        Returns:
            The unparsed controller payload.

        Raises:
            ValueError: If the configuration or payload size is invalid.
        """
        return _realtime.read_data_stream(self, config, size)

    def request_debug_var_info_3(self) -> tuple[DebugVarInfo, ...]:
        """Request the complete ``DEBUG_VARS_INFO_3`` metadata list.

        Returns:
            Index-ordered :class:`DebugVarInfo` records. Pass this complete
            result unchanged to :meth:`request_debug_var_values_3`.
        """
        return _realtime.request_debug_var_info_3(self)

    def format_debug_var_info_3(self, variables: Sequence[DebugVarInfo]) -> str:
        """Format debug-variable metadata as a compact text table.

        Args:
            variables: Records returned by :meth:`request_debug_var_info_3`.

        Returns:
            A human-readable table with variable indexes, names, types, and
            protocol flags.
        """
        return _realtime.format_debug_var_info_3(variables)

    def print_debug_var_info_3(self, variables: Sequence[DebugVarInfo]) -> None:
        """Print debug-variable metadata as a formatted table.

        Args:
            variables: Records returned by :meth:`request_debug_var_info_3`.
        """
        return _realtime.print_debug_var_info_3(variables)

    def request_debug_var_values_3(
        self,
        variables: Sequence[DebugVarInfo],
        selected_indexes: Sequence[int] | None = None,
    ) -> tuple[DebugVarInfo, ...]:
        """Request current values for debug variables.

        Args:
            variables: The complete, index-ordered metadata result from
                :meth:`request_debug_var_info_3`.
            selected_indexes: Optional variable indexes to request. Unselected
                records are returned unchanged.

        Returns:
            Metadata records populated with ``raw_value`` and decoded ``value``
            for each requested variable.

        Raises:
            ValueError: If ``variables`` is not a complete, index-ordered
                metadata list or a selected index is invalid.
        """
        return _realtime.request_debug_var_values_3(self, variables, selected_indexes)

    def select_imu_3(
        self,
        imu_type: ImuType | int,
        action: SelectImuAction | int = SelectImuAction.SIMPLE_SELECT,
        time_ms: int = 0,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Select an IMU or perform an extended IMU calibration action.

        Args:
            imu_type: The IMU addressed by the command.
            action: Selection or calibration action to perform.
            time_ms: Action-specific duration or timeout in milliseconds.
            need_confirmation: Request ``CMD_CONFIRM`` from firmware that
                supports confirmations.

        Returns:
            A command confirmation when requested and supported; otherwise
            ``None``.

        Raises:
            ValueError: If an enum value or ``time_ms`` is invalid.
        """
        return _realtime.select_imu_3(
            self,
            imu_type,
            action,
            time_ms,
            need_confirmation=need_confirmation,
        )

    def get_control_quat_status(
        self,
        flags: ControlQuatStatusFlag | int,
    ) -> ControlQuatStatus:
        """Read selected quaternion-control status fields (firmware 2.73+).

        Args:
            flags: Combination of :class:`ControlQuatStatusFlag` members to
                include in the controller response.

        Returns:
            A :class:`ControlQuatStatus` object. Fields not requested by
            ``flags`` are ``None``; speed values retain raw protocol units.

        Raises:
            ValueError: If no fields or unsupported status bits are selected.
        """
        return _realtime.get_control_quat_status(self, flags)

    def format_control_quat_status(self, status: ControlQuatStatus) -> str:
        """Format quaternion-control status fields.

        Args:
            status: Status returned by :meth:`get_control_quat_status`.

        Returns:
            A formatted text table.
        """
        return _realtime.format_control_quat_status(status)

    # SERVICE MODULE
    def motors_on(self) -> None:
        """Turn on the gimbal motors.

        Returns:
            ``None``.
        """
        _service.motors_on(self)

    def tune_auto_pid(
        self,
        config: AutoPidConfig,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Start legacy automatic PID tuning (firmware before 2.73).

        Args:
            config: Legacy Auto PID configuration.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _service.tune_auto_pid(self, config, need_confirmation=need_confirmation)

    def break_auto_pid(self, *, need_confirmation: bool = False) -> CommandConfirmation | None:
        """Stop legacy automatic PID tuning.

        Args:
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _service.break_auto_pid(self, need_confirmation=need_confirmation)

    def tune_auto_pid2(
        self,
        config: AutoPid2Config,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Start Auto PID2.

        Args:
            config: Auto PID2 configuration.
            need_confirmation: Request a completion confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _service.tune_auto_pid2(
            self,
            config,
            need_confirmation=need_confirmation,
        )

    def read_auto_pid_state(self) -> AutoPidState:
        """Read the latest legacy Auto PID progress packet.

        Returns:
            The current :class:`AutoPidState`.
        """
        return _service.read_auto_pid_state(self)

    def format_auto_pid_state(self, state: AutoPidState | None = None) -> str:
        """Format legacy Auto PID state using GUI-scale values.

        Args:
            state: State to format. ``None`` reads it first.

        Returns:
            A formatted text table.
        """
        return _service.format_auto_pid_state(
            self.read_auto_pid_state() if state is None else state
        )

    def read_profile_pid_values(self, profile_id: int = 0xFF) -> PidValues:
        """Read stored P/I/D values from a profile.

        Args:
            profile_id: Profile ID; ``0xFF`` selects the active profile.

        Returns:
            Raw :class:`PidValues` for the selected profile.
        """
        return _service.read_profile_pid_values(self, profile_id)

    def format_profile_pid_values(self, values: PidValues | None = None) -> str:
        """Format stored P/I/D values using GUI-scale values.

        Args:
            values: Values to format. ``None`` reads the active profile first.

        Returns:
            A formatted text table.
        """
        return _service.format_profile_pid_values(
            self.read_profile_pid_values() if values is None else values
        )

    def synchronize_motors(
        self,
        config: SyncMotorsConfig,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Synchronize parallel motors.

        Args:
            config: Axis, power, duration, and optional angle.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.

        Warning:
            The command can move the gimbal.
        """
        return _service.synchronize_motors(self, config, need_confirmation=need_confirmation)

    def request_one_external_motor_state(
        self, motor_id: int, data_set: int, result_size: int
    ) -> bytes:
        """Request raw external-motor state data.

        Args:
            motor_id: External motor identifier.
            data_set: Firmware state data-set mask.
            result_size: Expected raw payload size.

        Returns:
            Raw state payload.
        """
        return _service.request_motor_state(self, motor_id, data_set, result_size)

    def read_any_external_motors_state(self, result_size: int) -> bytes:
        """Read a queued raw external-motor state payload.

        Args:
            result_size: Expected raw payload size.

        Returns:
            Raw state payload.
        """
        return _service.read_motor_state(self, result_size)

    def enter_boot_mode(
        self,
        *,
        extended: bool = True,
        need_confirmation: bool = False,
        delay_ms: int = 0,
    ) -> None:
        """Enter the controller bootloader.

        Args:
            extended: Use the extended bootloader command.
            need_confirmation: Request a controller confirmation.
            delay_ms: Delay before entering boot mode.

        Warning:
            No further Serial API calls are valid on this connection.
        """
        _service.enter_boot_mode(
            self,
            extended=extended,
            need_confirmation=need_confirmation,
            delay_ms=delay_ms,
        )

    def read_state_vars(self) -> StateVars:
        """Read persistent maintenance and cumulative state counters.

        Returns:
            Current :class:`StateVars` values.
        """
        return _service.read_state_vars(self)

    def format_state_vars(self, state: StateVars | None = None) -> str:
        """Format persistent maintenance and state counters.

        Args:
            state: Counters to format. ``None`` reads them first.

        Returns:
            A formatted text table.
        """
        return _service.format_state_vars(self.read_state_vars() if state is None else state)

    def write_state_vars(
        self,
        state: StateVars,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Write persistent maintenance and state counters.

        Args:
            state: Complete state structure to persist.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _service.write_state_vars(self, state, need_confirmation=need_confirmation)

    def set_debug_port(
        self,
        action: int,
        filter: int = 0,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Configure debug-port packet mirroring.

        Args:
            action: Start/stop debug-port action.
            filter: Firmware packet filter; zero forwards all packets.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _service.set_debug_port(self, action, filter, need_confirmation=need_confirmation)

    def read_debug_port(self) -> DebugPortPacket:
        """Read one mirrored debug-port packet.

        Returns:
            A :class:`DebugPortPacket` with its exact raw payload length.
        """
        return _service.read_debug_port(self)

    def motors_off(self, mode: MotorsOffMode = MotorsOffMode.SAFE_STOP) -> None:
        """Turn off gimbal motors using the selected stop mode.

        Args:
            mode: Requested :class:`MotorsOffMode`.
        """
        _service.motors_off(self, mode)

    def beep(
        self,
        mode: BeeperMode = BeeperMode.CONFIRM,
        *,
        note_length: int = 0,
        decay_factor: int = 0,
        notes_hz: tuple[int, ...] = (),
    ) -> None:
        """Play a standard beeper signal or a custom motor melody.

        Args:
            mode: Standard signal or custom-melody mode.
            note_length: Custom-melody note length.
            decay_factor: Custom-melody decay factor.
            notes_hz: Custom-melody note frequencies.
        """
        _service.beep(
            self,
            mode,
            note_length=note_length,
            decay_factor=decay_factor,
            notes_hz=notes_hz,
        )

    def play_beeper(
        self,
        mode: BeeperMode = BeeperMode.CONFIRM,
        *,
        note_length: int = 0,
        decay_factor: int = 0,
        notes_hz: tuple[int, ...] = (),
    ) -> None:
        """Alias for :meth:`beep`.

        Args:
            mode: Standard signal or custom-melody mode.
            note_length: Custom-melody note length.
            decay_factor: Custom-melody decay factor.
            notes_hz: Custom-melody note frequencies.
        """
        self.beep(
            mode,
            note_length=note_length,
            decay_factor=decay_factor,
            notes_hz=notes_hz,
        )

    def execute_menu(
        self, menu_command: MenuCommands, *, need_confirmation: bool = False
    ) -> CommandConfirmation | None:
        """Execute a firmware menu command.

        Args:
            menu_command: Supported :class:`MenuCommands` member.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.

        Raises:
            ValueError: If the menu command is not supported by this method.
        """
        return _service.execute_menu(self, menu_command, need_confirmation=need_confirmation)

    def execute_menu_ext(
        self,
        menu_command: MenuCommands | int,
        *,
        confirm_on_start: bool = False,
        confirm_on_finish: bool = False,
    ) -> MenuExecutionResult:
        """Execute a menu command with optional lifecycle confirmations.

        Args:
            menu_command: Supported firmware menu command.
            confirm_on_start: Request confirmation when execution starts.
            confirm_on_finish: Request confirmation when execution finishes.

        Returns:
            Start and finish confirmation results.
        """
        return _service.execute_menu_ext(
            self,
            menu_command,
            confirm_on_start=confirm_on_start,
            confirm_on_finish=confirm_on_finish,
        )

    def set_trigger_pin(
        self,
        pin: TriggerPin | int,
        state: TriggerPinState | int,
        *,
        need_confirmation: bool = False,
    ) -> CommandConfirmation | None:
        """Set a controller trigger-output pin.

        Args:
            pin: Trigger pin to change.
            state: Desired :class:`TriggerPinState`.
            need_confirmation: Request a controller confirmation.

        Returns:
            A confirmation when requested and supported; otherwise ``None``.
        """
        return _service.set_trigger_pin(
            self,
            pin,
            state,
            need_confirmation=need_confirmation,
        )

    def set_servo_out(self, values: tuple[int, int, int, int]) -> None:
        """Set the four basic servo-output values.

        Args:
            values: Four firmware-scale servo values.

        Raises:
            ValueError: If the tuple length or an output value is invalid.
        """
        _service.set_servo_out(self, values)

    def set_servo_out_ext(self, outputs: dict[ServoOutput | int, int]) -> None:
        """Set selected extended servo outputs.

        Args:
            outputs: Mapping of servo-output selectors to firmware-scale values.

        Raises:
            ValueError: If an output selector or value is invalid.
        """
        _service.set_servo_out_ext(self, outputs)

    def run_script(self, slot: int = 1, *, debug: bool = False) -> None:
        """Start a controller script.

        Args:
            slot: Controller script slot.
            debug: Enable debug output readable via :meth:`read_script_debug_info`.

        Raises:
            ValueError: If ``slot`` is invalid.
        """
        _service.run_script(self, slot, debug=debug)

    def stop_script(self, slot: int = 1) -> None:
        """Stop the script in a controller slot.

        Args:
            slot: Controller script slot.

        Raises:
            ValueError: If ``slot`` is invalid.
        """
        _service.stop_script(self, slot)

    def read_script_debug_info(self, timeout: float = 1.0) -> ScriptDebugInfo:
        """Read the next debug record from a running script.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            The next :class:`ScriptDebugInfo` record.

        Raises:
            TimeoutError: If no debug record arrives before ``timeout``.
        """
        return _service.read_script_debug_info(self, timeout)

    def get_board_info(self) -> BoardInfo:
        """Read basic controller board and firmware information.

        Returns:
            A :class:`BoardInfo` structure.
        """
        return _service.get_board_info(self)

    def format_board_info(self, info: BoardInfo | None = None) -> str:
        """Format basic controller board information.

        Args:
            info: Board information to format. ``None`` reads it first.

        Returns:
            A formatted text table.
        """
        return _service.format_board_info(self.get_board_info() if info is None else info)

    def get_board_info_3(self) -> BoardInfo3:
        """Read extended controller board and firmware information.

        Returns:
            A :class:`BoardInfo3` structure.
        """
        return _service.get_board_info_3(self)

    def format_board_info_3(self, info: BoardInfo3 | None = None) -> str:
        """Format extended controller board information.

        Args:
            info: Extended board information to format. ``None`` reads it first.

        Returns:
            A formatted text table.
        """
        return _service.format_board_info_3(self.get_board_info_3() if info is None else info)

    def reset(
        self,
        delay_ms: int = 100,
        *,
        need_confirmation: bool = True,
        restore_state: bool = False,
        confirmation_timeout: float = 2.0,
        startup_delay: float = 5.0,
    ) -> None:
        """Reset the controller and optionally restore the Python connection.

        Args:
            delay_ms: Firmware reset delay in milliseconds.
            need_confirmation: Request a confirmation before resetting.
            restore_state: Reopen and restore the local transport state afterward.
            confirmation_timeout: Maximum confirmation wait in seconds.
            startup_delay: Delay after reopening the transport, in seconds.

        Raises:
            TimeoutError: If a requested confirmation does not arrive in time.
            ValueError: If a delay value is invalid.
        """
        _service.reset(
            self,
            delay_ms,
            need_confirmation=need_confirmation,
            restore_state=restore_state,
            confirmation_timeout=confirmation_timeout,
            startup_delay=startup_delay,
        )

    def request_module_list(
        self,
        max_devices: int = 13,
    ) -> tuple[CanModuleInfo, ...]:
        """Request the CAN module list.

        Args:
            max_devices: Maximum number of module entries to request.

        Returns:
            Discovered :class:`CanModuleInfo` records.
        """
        return _service.request_module_list(self, max_devices)

    def format_can_module_list(self, modules: tuple[CanModuleInfo, ...] | None = None) -> str:
        """Format CAN-module information.

        Args:
            modules: Module records to format. ``None`` requests them first.

        Returns:
            A formatted text table.
        """
        return _service.format_can_module_list(
            self.request_module_list() if modules is None else modules
        )

    def scan_can_device(
        self,
    ) -> CanDeviceScan:
        """Read the current CAN device-scan result.

        Returns:
            The latest :class:`CanDeviceScan` structure.
        """
        return _service.scan_can_device(
            self,
        )

    def sign_message(
        self,
        sign_type: int,
        message: bytes,
    ) -> bytes:
        """Sign a message with the controller cryptographic service.

        Args:
            sign_type: Firmware-defined signing mode.
            message: Raw message bytes to sign.

        Returns:
            Raw firmware signature bytes.
        """
        return _service.sign_message(self, sign_type, message)

    def send_transparent_command(self, target: int, payload: bytes) -> None:
        """Forward raw Serial API data through CAN.

        Args:
            target: Packed transparent-command target.
            payload: Raw Serial API packet payload.
        """
        _service.send_transparent_command(self, target, payload)

    def read_transparent_command(self, max_payload_size: int = 254) -> tuple[int, bytes]:
        """Read a transparent CAN packet.

        Args:
            max_payload_size: Maximum accepted payload length.

        Returns:
            Packed target and raw payload bytes.
        """
        return _service.read_transparent_command(self, max_payload_size)

    # Transport information
    def get_last_serial_status(self) -> int:
        """Return the latest native Serial API status code.

        Returns:
            Firmware/native bridge status code for the most recent operation.
        """
        self._ensure_open()
        return self._native.get_last_serial_status(self._device)

    @staticmethod
    def _required_argument(command: Command, kwargs: dict[str, object], name: str) -> object:
        try:
            value = kwargs.pop(name)
        except KeyError as error:
            raise TypeError(f"{command.name} requires {name}=...") from error
        return value

    @staticmethod
    def _reject_remaining_arguments(command: Command, kwargs: dict[str, object]) -> None:
        if kwargs:
            raise TypeError(
                f"{command.name} does not accept keyword arguments: {', '.join(kwargs)}"
            )

    def close(self) -> None:
        """Close the serial connection and release its resources.

        The method is idempotent and is called automatically by the context
        manager returned from :class:`SimpleBGC`.
        """
        if not self._closed:
            self._backend.close(self._device)
            self._closed = True
            self._debug_script_slot = None

    def _ensure_open(self) -> None:
        if self._closed:
            raise NativeError("The SimpleBGC connection is already closed.")

    def __enter__(self) -> SimpleBGC:
        self._ensure_open()
        return self

    def __exit__(self, exception_type, exception, traceback) -> None:
        self.close()
