#include "sbgc_py_internal.h"

#include <string.h>


static sbgc_py_status_t sbgc_py_validate_service_device (sbgc_py_device_t *device)
{
    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;
    return SBGC_PY_OK;
}


sbgc_py_status_t sbgc_py_get_board_info (sbgc_py_device_t *device, sbgc_py_board_info_t *board_info)
{
#if (SBGC_SERVICE_MODULE)
	sbgcBoardInfo_t native_board_info = { 0 };
	sbgcCommandStatus_t status;

    if (device == NULL || board_info == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    status = SBGC32_ReadBoardInfo(&device->serial_api, &native_board_info, 0);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK ||
        native_board_info.boardVer == 0 || native_board_info.firmwareVer == 0)
        return SBGC_PY_COMMUNICATION_ERROR;

    board_info->board_ver = native_board_info.boardVer;
    board_info->firmware_ver = native_board_info.firmwareVer;
    board_info->state_flags = native_board_info.stateFlags;
    board_info->board_features = native_board_info.boardFeatures;
    board_info->connection_flag = native_board_info.connectionFlag;
    board_info->firmware_extra_id = native_board_info.frwExtraID;
    board_info->board_features_ext = native_board_info.boardFeaturesExt;
    board_info->main_imu_sensor_model = native_board_info.mainIMU_SensModel;
    board_info->frame_imu_sensor_model = native_board_info.frameIMU_SensModel;
    board_info->build_number = native_board_info.buildNumber;
    board_info->base_firmware_ver = native_board_info.baseFrwVer;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)board_info;
    return SBGC_PY_MODULE_DISABLED;
#endif
}

sbgc_py_status_t sbgc_py_get_board_info_3 (sbgc_py_device_t *device, sbgc_py_board_info_3_t *board_info)
{
#if (SBGC_SERVICE_MODULE)
    sbgcBoardInfo3_t native_board_info = {0};
    sbgcCommandStatus_t status;

    if (device == NULL || board_info == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    status = SBGC32_ReadBoardInfo3(&device->serial_api, &native_board_info);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    memcpy(board_info->device_id, native_board_info.deviceID, 9);
    memcpy(board_info->mcu_id, native_board_info.MCU_ID, 12);

    board_info->eeprom_size = native_board_info.EEPROM_Size;

    board_info->script_slot_1_size = native_board_info.scriptSlot1_Size;
    board_info->script_slot_2_size = native_board_info.scriptSlot2_Size;
    board_info->script_slot_3_size = native_board_info.scriptSlot3_Size;
    board_info->script_slot_4_size = native_board_info.scriptSlot4_Size;
    board_info->script_slot_5_size = native_board_info.scriptSlot5_Size;

    board_info->profile_set_slots = native_board_info.profileSetSlots;
    board_info->profile_set_current = native_board_info.profileSetCur;
    board_info->flash_size = native_board_info.flashSize;

    memcpy(board_info->imu_calib_info, native_board_info.IMU_CalibInfo, 2);

    board_info->script_slot_6_size = native_board_info.scriptSlot6_Size;
    board_info->script_slot_7_size = native_board_info.scriptSlot7_Size;
    board_info->script_slot_8_size = native_board_info.scriptSlot8_Size;
    board_info->script_slot_9_size = native_board_info.scriptSlot9_Size;
    board_info->script_slot_10_size = native_board_info.scriptSlot10_Size;

    board_info->hardware_flags = native_board_info.hwFlags;
    board_info->board_features_ext2 = native_board_info.boardFeaturesExt2;
    board_info->can_driver_main_limit = native_board_info.CAN_DrvMainLimit;
    board_info->can_driver_aux_limit = native_board_info.CAN_DrvAuxLimit;
    board_info->adjustable_variables_total = native_board_info.adjVarsTotalNum;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)board_info;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_reset (sbgc_py_device_t *device, uint8_t flags, uint16_t delay_ms)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    status = SBGC32_Reset(&device->serial_api, flags, delay_ms);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)flags;
    (void)delay_ms;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_expect_reset (sbgc_py_device_t *device)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    status = SBGC32_ExpectCommand(&device->serial_api, CMD_RESET, NULL, 0);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_motors_on (sbgc_py_device_t *device)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    status = SBGC32_SetMotorsON(&device->serial_api, SBGC_NO_CONFIRM);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_motors_off (sbgc_py_device_t *device, uint8_t mode)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;
    if (mode > MOTOR_MODE_SAFE_STOP)
        return SBGC_PY_INVALID_ARGUMENT;

    status = SBGC32_SetMotorsOFF(&device->serial_api, (sbgcMotorsMode_t)mode, SBGC_NO_CONFIRM);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)mode;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_play_beeper (
    sbgc_py_device_t *device,
    uint16_t mode,
    uint8_t note_length,
    uint8_t decay_factor,
    const uint16_t *notes_hz,
    uint8_t notes_count
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcBeeperSettings_t settings = { 0 };
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;
    if (notes_count > SBGC_MAX_NOTES_QUANTITY ||
        (notes_count != 0 && notes_hz == NULL))
        return SBGC_PY_INVALID_ARGUMENT;
    if (mode != BEEP_MODE_CUSTOM_MELODY && notes_count != 0)
        return SBGC_PY_INVALID_ARGUMENT;

    settings.mode = mode;
    settings.noteLength = note_length;
    settings.decayFactor = decay_factor;
    settings.notesFreqHz = (ui16 *)notes_hz;
    settings.notesQuan = notes_count;

    status = SBGC32_PlayBeeper(&device->serial_api, &settings);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)mode;
    (void)note_length;
    (void)decay_factor;
    (void)notes_hz;
    (void)notes_count;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_execute_menu (
    sbgc_py_device_t *device,
    uint8_t menu_command,
    uint8_t need_confirmation,
    sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;
    if (need_confirmation && confirmation == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = SBGC32_ExecuteMenu(
            &device->serial_api, (sbgcMenuCommand_t)menu_command,
            &native_confirmation
        );
        if (status != sbgcCOMMAND_OK ||
            device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        confirmation->command_id = native_confirmation.commandID;
        confirmation->status = (uint8_t)native_confirmation.status;
        confirmation->command_data = native_confirmation.cmdData;
        confirmation->error_code = native_confirmation.errorCode;
        memcpy(confirmation->error_data, native_confirmation.errorData,
               sizeof(confirmation->error_data));
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    status = SBGC32_ExecuteMenu(
        &device->serial_api, (sbgcMenuCommand_t)menu_command, SBGC_NO_CONFIRM
    );
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;
    return SBGC_PY_OK;
#else
    (void)device;
    (void)menu_command;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}



sbgc_py_status_t sbgc_py_run_script (sbgc_py_device_t *device, uint8_t mode, uint8_t slot)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    if (mode > ScrtM_START_WITH_DEBUG || slot > 10)
        return SBGC_PY_INVALID_ARGUMENT;

    status = SBGC32_RunScript(&device->serial_api, (sbgcScriptMode_t)mode, (sbgcScriptSlotNum_t)slot);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)mode;
    (void)slot;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_script_debug_info (sbgc_py_device_t *device, sbgc_py_script_debug_info_t *script_debug_info)
{
#if (SBGC_SERVICE_MODULE)
    sbgcScriptDebugInfo_t native_script_debug_info = { 0 };
    sbgcCommandStatus_t status;

    if (device == NULL || script_debug_info == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    status = SBGC32_ReadScriptDebugInfo(&device->serial_api, &native_script_debug_info);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    script_debug_info->current_command_counter = native_script_debug_info.curComCounter;
    script_debug_info->error_code = native_script_debug_info.errorCode;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)script_debug_info;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_tune_auto_pid (
    sbgc_py_device_t *device, const sbgc_py_auto_pid_t *config,
    uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcAutoPID_t native_config;
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (config == NULL || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;
    _Static_assert(sizeof(native_config) == sizeof(*config), "AutoPID ABI mismatch");
    memcpy(&native_config, config, sizeof(native_config));

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        status = SBGC32_TuneAutoPID(&device->serial_api, &native_config, &native_confirmation);
        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    status = SBGC32_TuneAutoPID(&device->serial_api, &native_config, SBGC_NO_CONFIRM);
    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; (void)config; (void)need_confirmation; (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_break_auto_pid (
    sbgc_py_device_t *device, uint8_t need_confirmation,
    sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (need_confirmation && confirmation == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        status = SBGC32_BreakAutoPID_Tuning(&device->serial_api, &native_confirmation);
        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_BreakAutoPID_Tuning(&device->serial_api, SBGC_NO_CONFIRM);
    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; (void)need_confirmation; (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_tune_auto_pid2 (
    sbgc_py_device_t *device, const sbgc_py_auto_pid2_t *config,
    uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcAutoPID2_t native_config;
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (config == NULL || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;
    _Static_assert(sizeof(native_config) == sizeof(*config), "AutoPID2 ABI mismatch");
    memcpy(&native_config, config, sizeof(native_config));
#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        status = SBGC32_TuneAutoPID2(&device->serial_api, &native_config, &native_confirmation);
        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_TuneAutoPID2(&device->serial_api, &native_config, SBGC_NO_CONFIRM);
    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; (void)config; (void)need_confirmation; (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_auto_pid_state (
    sbgc_py_device_t *device, sbgc_py_auto_pid_state_t *state
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcAutoPID_State_t native_state = { 0 };
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (state == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    _Static_assert(sizeof(native_state) == sizeof(*state), "AutoPID state ABI mismatch");
    status = SBGC32_ReadAutoPID_StateCmd(&device->serial_api, &native_state);
    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;
    memcpy(state, &native_state, sizeof(*state));
    return SBGC_PY_OK;
#else
    (void)device; (void)state;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_synchronize_motors (
    sbgc_py_device_t *device, const sbgc_py_sync_motors_t *config,
    uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcSyncMotors_t native_config;
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (config == NULL || config->axis > SYNC_MOTOR_AXIS_YAW ||
        (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;
    _Static_assert(sizeof(native_config) == sizeof(*config), "Sync motors ABI mismatch");
    memcpy(&native_config, config, sizeof(native_config));
#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        status = SBGC32_SynchronizeMotors(&device->serial_api, &native_config, &native_confirmation);
        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_SynchronizeMotors(&device->serial_api, &native_config, SBGC_NO_CONFIRM);
    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; (void)config; (void)need_confirmation; (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_request_motor_state (
    sbgc_py_device_t *device, uint8_t motor_id, uint32_t data_set,
    uint8_t *result, uint16_t size
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (result == NULL || size < sizeof(data_set))
        return SBGC_PY_INVALID_ARGUMENT;
    memset(result, 0, size);
    memcpy(result, &data_set, sizeof(data_set));
    status = SBGC32_RequestMotorState(
        &device->serial_api, (sbgcExtMotorID_t)motor_id, result, size
    );
    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; (void)motor_id; (void)data_set; (void)result; (void)size;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_motor_state (sbgc_py_device_t *device, uint8_t *result, uint16_t size)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (result == NULL || size == 0)
        return SBGC_PY_INVALID_ARGUMENT;
    status = SBGC32_ReadMotorState(&device->serial_api, result, size);
    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; (void)result; (void)size;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_set_boot_mode (
    sbgc_py_device_t *device, uint8_t extended, uint8_t need_confirmation,
    uint16_t delay_ms
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (extended > 1 || need_confirmation > 1)
        return SBGC_PY_INVALID_ARGUMENT;
    status = extended
        ? SBGC32_SetBootModeExt(&device->serial_api, (sbgcBoolean_t)need_confirmation, delay_ms)
        : SBGC32_SetBootMode(&device->serial_api);
    return status == sbgcCOMMAND_OK ? SBGC_PY_OK : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; (void)extended; (void)need_confirmation; (void)delay_ms;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_write_state_vars (
    sbgc_py_device_t *device, const sbgc_py_state_vars_t *state,
    uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcStateVars_t native_state;
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (state == NULL || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;
    _Static_assert(sizeof(native_state) == sizeof(*state), "State vars ABI mismatch");
    memcpy(&native_state, state, sizeof(native_state));
#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        status = SBGC32_WriteStateVars(&device->serial_api, &native_state, &native_confirmation);
        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_WriteStateVars(&device->serial_api, &native_state, SBGC_NO_CONFIRM);
    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; (void)state; (void)need_confirmation; (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_state_vars (
    sbgc_py_device_t *device, sbgc_py_state_vars_t *state
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcStateVars_t native_state = { 0 };
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (state == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    _Static_assert(sizeof(native_state) == sizeof(*state), "State vars ABI mismatch");
    status = SBGC32_ReadStateVars(&device->serial_api, &native_state);
    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;
    memcpy(state, &native_state, sizeof(*state));
    return SBGC_PY_OK;
#else
    (void)device; (void)state;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_set_debug_port (
    sbgc_py_device_t *device, uint8_t action, uint32_t filter,
    uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (action > DPA_START_USING_DEBUG_PORT || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;
#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        status = SBGC32_SetDebugPort(&device->serial_api, (sbgcDebugPortAction_t)action, filter, &native_confirmation);
        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_SetDebugPort(&device->serial_api, (sbgcDebugPortAction_t)action, filter, SBGC_NO_CONFIRM);
    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; (void)action; (void)filter; (void)need_confirmation; (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_debug_port (
    sbgc_py_device_t *device, uint16_t *time_ms, uint8_t *port_and_direction,
    uint8_t *command_id, uint8_t *payload, uint16_t payload_capacity
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcDebugPortData_t native_data;
    sbgcCommandStatus_t status;
    uint8_t buffered_payload_size;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (time_ms == NULL || port_and_direction == NULL || command_id == NULL ||
        payload == NULL || payload_capacity < SBGC_MAX_PAYLOAD_SIZE)
        return SBGC_PY_INVALID_ARGUMENT;

    /*
     * Debug records are unsolicited.  A record may have arrived while another
     * blocking SerialAPI command was waiting for its own response; in that
     * case SerialAPI ignores the different command ID.  The native COM
     * transport preserves a copy before that filtering happens.
     */
    if (sbgc_py_transport_pop_debug_packet(
            device->context, time_ms, port_and_direction, command_id, payload,
            &buffered_payload_size))
        return SBGC_PY_OK;

    /* Do not enqueue a second copy while this call itself receives a record. */
    sbgc_py_transport_set_debug_capture_suppressed(device->context, 1);
    native_data.payload = payload;
    status = SBGC32_ReadDebugPort(&device->serial_api, &native_data);
    sbgc_py_transport_set_debug_capture_suppressed(device->context, 0);
    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;
    *time_ms = native_data.timeMs;
    *port_and_direction = native_data.portAndDir;
    *command_id = native_data.cmdID;
    return SBGC_PY_OK;
#else
    (void)device; (void)time_ms; (void)port_and_direction; (void)command_id; (void)payload; (void)payload_capacity;
    return SBGC_PY_MODULE_DISABLED;
#endif
}
