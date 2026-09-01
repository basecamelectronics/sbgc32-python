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


static sbgc_py_status_t sbgc_py_require_can_port (sbgc_py_device_t *device)
{
    sbgcBoardInfo_t board_info = { 0 };
    sbgcCommandStatus_t status = SBGC32_ReadBoardInfo(&device->serial_api, &board_info, 0);

    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return (board_info.boardFeatures & BF_CAN_PORT)
            ? SBGC_PY_OK
            : SBGC_PY_CAN_NOT_SUPPORTED;
}


static sbgc_py_status_t sbgc_py_require_state_vars (sbgc_py_device_t *device)
{
    sbgcBoardInfo_t board_info = { 0 };
    sbgcCommandStatus_t status = SBGC32_ReadBoardInfo(&device->serial_api, &board_info, 0);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    if (board_info.boardVer < 36 || board_info.firmwareVer < 2687 || !(board_info.boardFeaturesExt & BFE_STATE_VARS))
        return SBGC_PY_STATE_VARS_NOT_SUPPORTED;

    return SBGC_PY_OK;
}


sbgc_py_status_t sbgc_py_get_last_error (sbgc_py_device_t *device, int *error)
{
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (error == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    *error = (int)SerialAPI_GetSerialStatus(&device->serial_api);
    return SBGC_PY_OK;
}


sbgc_py_status_t sbgc_py_get_board_info (sbgc_py_device_t *device, sbgc_py_board_info_t *board_info)
{
#if (SBGC_SERVICE_MODULE)

    if (device == NULL || board_info == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_ReadBoardInfo(&device->serial_api, board_info, 0);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK ||
        board_info->boardVer == 0 || board_info->firmwareVer == 0)
        return SBGC_PY_COMMUNICATION_ERROR;

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

    if (device == NULL || board_info == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_ReadBoardInfo3(&device->serial_api, &native_board_info);

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

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_Reset(&device->serial_api, flags, delay_ms);

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

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_ExpectCommand(&device->serial_api, CMD_RESET, NULL, 0);

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

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_SetMotorsON(&device->serial_api, SBGC_NO_CONFIRM);

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

    if (device == NULL || mode > MOTOR_MODE_SAFE_STOP)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_SetMotorsOFF(&device->serial_api, (sbgcMotorsMode_t)mode, SBGC_NO_CONFIRM);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)mode;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_play_beeper 
(
    sbgc_py_device_t *device, uint16_t mode, uint8_t note_length,
    uint8_t decay_factor, const uint16_t *notes_hz, uint8_t notes_count
)
{
#if (SBGC_SERVICE_MODULE)

    sbgcBeeperSettings_t settings = { 0 };

    if (device == NULL || notes_count > SBGC_MAX_NOTES_QUANTITY 
        || (notes_count != 0 && notes_hz == NULL) || (mode != BEEP_MODE_CUSTOM_MELODY && notes_count != 0))
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    settings.mode = mode;
    settings.noteLength = note_length;
    settings.decayFactor = decay_factor;
    settings.notesFreqHz = (ui16 *)notes_hz;
    settings.notesQuan = notes_count;

    sbgcCommandStatus_t status = SBGC32_PlayBeeper(&device->serial_api, &settings);

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


sbgc_py_status_t sbgc_py_execute_menu 
(
    sbgc_py_device_t *device, uint8_t menu_command,
    uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;

    if (device == NULL || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;
    

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = SBGC32_ExecuteMenu(&device->serial_api, (sbgcMenuCommand_t)menu_command, &native_confirmation);

        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        confirmation->command_id = native_confirmation.commandID;
        confirmation->status = (uint8_t)native_confirmation.status;
        confirmation->command_data = native_confirmation.cmdData;
        confirmation->error_code = native_confirmation.errorCode;

        memcpy(confirmation->error_data, native_confirmation.errorData, sizeof(confirmation->error_data));

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    status = SBGC32_ExecuteMenu(&device->serial_api, (sbgcMenuCommand_t)menu_command, SBGC_NO_CONFIRM);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
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


SBGC_PY_API sbgc_py_status_t sbgc_py_execute_menu_ext
(
    sbgc_py_device_t *device, ui8 menu_command, ui8 flags,
    sbgc_py_confirmation_t *start_confirmation,
    sbgc_py_confirmation_t *finish_confirmation
)
{
#if (SBGC_SERVICE_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);
    sbgcConfirm_t first = { 0 };
    sbgcConfirm_t finish = { 0 };
    sbgcCommandStatus_t status;

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (menu_command > MENU_CMD_SERVO_MODE_TOGGLE)
        return SBGC_PY_INVALID_ARGUMENT;

    if (flags & ~(MC_FLAG_CONFIRM | MC_FLAG_CONFIRM_ON_FINISH))
        return SBGC_PY_INVALID_ARGUMENT;

    if ((flags & MC_FLAG_CONFIRM) && start_confirmation == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if ((flags & MC_FLAG_CONFIRM_ON_FINISH) && finish_confirmation == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

#if (SBGC_NEED_CONFIRM_CMD)
    status = SBGC32_ExecuteMenuExt(
        &device->serial_api,
        (sbgcMenuCommand_t)menu_command,
        (sbgcMenuCmdFlag_t)flags,
        flags ? &first : SBGC_NO_CONFIRM
    );

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    if (flags & MC_FLAG_CONFIRM)
        sbgc_py_copy_confirmation(start_confirmation, &first);

    if ((flags & MC_FLAG_CONFIRM_ON_FINISH) && !(flags & MC_FLAG_CONFIRM))
        sbgc_py_copy_confirmation(finish_confirmation, &first);

    if ((flags & MC_FLAG_CONFIRM) && (flags & MC_FLAG_CONFIRM_ON_FINISH))
    {
        status = SBGC32_CheckConfirmation(&device->serial_api, &finish, CMD_EXECUTE_MENU);

        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(finish_confirmation, &finish);
    }

    return SBGC_PY_OK;
#else
    if (flags != MC_FLAG_NO)
        return SBGC_PY_CONFIRMATION_DISABLED;

    status = SBGC32_ExecuteMenu(
        &device->serial_api,
        (sbgcMenuCommand_t)menu_command,
        SBGC_NO_CONFIRM
    );

    return (status == sbgcCOMMAND_OK &&
            device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK
        : SBGC_PY_COMMUNICATION_ERROR;
#endif
#else
    (void)device;
    (void)menu_command;
    (void)flags;
    (void)start_confirmation;
    (void)finish_confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_set_trigger_pin
(
    sbgc_py_device_t *device, ui8 pin_id, ui8 state,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);
    sbgcCommandStatus_t status;

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (state > sbgcPIN_STATE_FLOATING ||
        (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = SBGC32_SetTriggerPin(
            &device->serial_api,
            (sbgcTriggerPinID_t)pin_id,
            (sbgcPinState_t)state,
            &native_confirmation
        );

        if (status != sbgcCOMMAND_OK ||
            device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    status = SBGC32_SetTriggerPin(
        &device->serial_api,
        (sbgcTriggerPinID_t)pin_id,
        (sbgcPinState_t)state,
        SBGC_NO_CONFIRM
    );

    return (status == sbgcCOMMAND_OK &&
            device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK
        : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device;
    (void)pin_id;
    (void)state;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_set_servo_out
(
    sbgc_py_device_t *device, const i16 *values, ui8 count
)
{
#if (SBGC_SERVICE_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);
    sbgcCommandStatus_t status;

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (values == NULL || count != SBGC_SERVO_OUTS_NUM)
        return SBGC_PY_INVALID_ARGUMENT;

    status = SBGC32_SetServoOut(&device->serial_api, values);

    return (status == sbgcCOMMAND_OK &&
            device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK
        : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device;
    (void)values;
    (void)count;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_set_servo_out_ext
(
    sbgc_py_device_t *device, ui32 pins, const i16 *values, ui8 count
)
{
#if (SBGC_SERVICE_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);
    sbgcCommandStatus_t status;
    ui8 required_count = 0;

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (pins == 0 || (pins & ~0x3FFFFUL) != 0 || values == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    for (ui8 bit = 0; bit < 18; bit++)
        if (pins & (1UL << bit))
            required_count++;

    if (count != required_count)
        return SBGC_PY_INVALID_ARGUMENT;

    status = SBGC32_SetServoOutExt(&device->serial_api, pins, (i16 *)values);

    return (status == sbgcCOMMAND_OK &&
            device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK
        : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device;
    (void)pins;
    (void)values;
    (void)count;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_run_script (sbgc_py_device_t *device, uint8_t mode, uint8_t slot)
{
#if (SBGC_SERVICE_MODULE)

    if (device == NULL || mode > ScrtM_START_WITH_DEBUG || slot >= 10)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_RunScript(&device->serial_api, (sbgcScriptMode_t)mode, (sbgcScriptSlotNum_t)slot);

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

    if (device == NULL || script_debug_info == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_ReadScriptDebugInfo(&device->serial_api, script_debug_info);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)script_debug_info;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_tune_auto_pid 
(
    sbgc_py_device_t *device, const sbgc_py_auto_pid_t *config,
    uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)

    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (config == NULL || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = SBGC32_TuneAutoPID(&device->serial_api, config, &native_confirmation);

        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    status = SBGC32_TuneAutoPID(&device->serial_api, config, SBGC_NO_CONFIRM);

    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
            ? SBGC_PY_OK 
            : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; 
    (void)config; 
    (void)need_confirmation; 
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_break_auto_pid 
(
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
            ? SBGC_PY_OK 
            : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; 
    (void)need_confirmation; 
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_tune_auto_pid2 
(
    sbgc_py_device_t *device, const sbgc_py_auto_pid2_t *config,
    uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (config == NULL || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        status = SBGC32_TuneAutoPID2(&device->serial_api, config, &native_confirmation);

        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_TuneAutoPID2(&device->serial_api, config, SBGC_NO_CONFIRM);

    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
            ? SBGC_PY_OK 
            : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; 
    (void)config; 
    (void)need_confirmation; 
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_profile_pid_values
(
    sbgc_py_device_t *device, ui8 profile_id, sbgc_py_pid_values_t *values
)
{
#if (SBGC_PROFILES_MODULE)

    sbgcMainParams3_t params = { 0 };
    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (values == NULL || (profile_id > sbgcPROFILE_5 && profile_id != sbgcCURRENT_PROFILE))
        return SBGC_PY_INVALID_ARGUMENT;

    status = SBGC32_ReadParams3(&device->serial_api, &params, (sbgcProfile_t)profile_id);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    values->profile_id = params.profileID;
    for (ui8 axis = 0; axis < 3; axis++)
    {
        values->p[axis] = params.AxisCMP3[axis].p;
        values->i[axis] = params.AxisCMP3[axis].i;
        values->d[axis] = params.AxisCMP3[axis].d;
    }

    return SBGC_PY_OK;
#else
    (void)device;
    (void)profile_id;
    (void)values;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_auto_pid_state (sbgc_py_device_t *device, sbgc_py_auto_pid_state_t *state)
{
#if (SBGC_SERVICE_MODULE)
    
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (state == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    sbgcCommandStatus_t status = SBGC32_ReadAutoPID_StateCmd(&device->serial_api, state);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device; (void)state;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_synchronize_motors 
(
    sbgc_py_device_t *device, const sbgc_py_sync_motors_t *config,
    uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)

    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (config == NULL || config->axis > SYNC_MOTOR_AXIS_YAW || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = SBGC32_SynchronizeMotors(&device->serial_api, (sbgcSyncMotors_t *)config, &native_confirmation);
        
        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_SynchronizeMotors(&device->serial_api, (sbgcSyncMotors_t *)config, SBGC_NO_CONFIRM);

    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
            ? SBGC_PY_OK 
            : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; 
    (void)config; 
    (void)need_confirmation; 
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


static sbgc_py_status_t sbgc_py_external_motor_state_result(sbgc_py_device_t* device, sbgcCommandStatus_t status)
{
    if (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        return SBGC_PY_OK;

    switch (device->serial_api._lastSerialCommandStatus)
    {
        case serialAPI_RX_EMPTY_BUFF_ERROR:
        case serialAPI_RX_BUFFER_REALTIME_ERROR:
        case serialAPI_RX_NOT_FOUND_ERROR:
            return SBGC_PY_EXTERNAL_MOTOR_NO_RESPONSE;

        default:
            return SBGC_PY_COMMUNICATION_ERROR;
    }
}


sbgc_py_status_t sbgc_py_request_motor_state 
(
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

    device_status = sbgc_py_require_can_port(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    memset(result, 0, size);
    memcpy(result, &data_set, sizeof(data_set));

    status = SBGC32_RequestMotorState(&device->serial_api, (sbgcExtMotorID_t)motor_id, result, size);

    return sbgc_py_external_motor_state_result(device, status);
#else
    (void)device; 
    (void)motor_id; 
    (void)data_set;
    (void)result; 
    (void)size;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_motor_state (sbgc_py_device_t *device, uint8_t *result, uint16_t size)
{
#if (SBGC_SERVICE_MODULE)

    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (result == NULL || size == 0)
        return SBGC_PY_INVALID_ARGUMENT;

    device_status = sbgc_py_require_can_port(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    sbgcCommandStatus_t status = SBGC32_ReadMotorState(&device->serial_api, result, size);

    return sbgc_py_external_motor_state_result(device, status);
#else
    (void)device; 
    (void)result; 
    (void)size;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_set_boot_mode
(
    sbgc_py_device_t *device, uint8_t extended,
    uint8_t need_confirmation, uint16_t delay_ms
)
{
#if (SBGC_SERVICE_MODULE)

    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (extended > 1 || need_confirmation > 1 || need_confirmation ||
        (!extended && delay_ms != 0))
        return SBGC_PY_INVALID_ARGUMENT;

    if (!extended)
    {
        sbgcCommandStatus_t status = SBGC32_SetBootMode(&device->serial_api);

        return (status == sbgcCOMMAND_OK &&
                device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
                ? SBGC_PY_OK
                : SBGC_PY_COMMUNICATION_ERROR;
    }

    sbgcCommandStatus_t status = SBGC32_SetBootModeExt(
            &device->serial_api, sbgcFALSE, delay_ms);

    return (status == sbgcCOMMAND_OK &&
            device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
            ? SBGC_PY_OK
            : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; 
    (void)extended; 
    (void)need_confirmation; 
    (void)delay_ms;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_write_state_vars 
(
    sbgc_py_device_t *device, const sbgc_py_state_vars_t *state,
    uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_SERVICE_MODULE)

    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (state == NULL || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

    device_status = sbgc_py_require_state_vars(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = SBGC32_WriteStateVars(&device->serial_api, state, &native_confirmation);

        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_WriteStateVars(&device->serial_api, state, SBGC_NO_CONFIRM);

    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
            ? SBGC_PY_OK 
            : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; 
    (void)state; 
    (void)need_confirmation; 
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_state_vars (sbgc_py_device_t *device, sbgc_py_state_vars_t *state)
{
#if (SBGC_SERVICE_MODULE)

    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (state == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    device_status = sbgc_py_require_state_vars(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    sbgcCommandStatus_t status = SBGC32_ReadStateVars(&device->serial_api, state);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device; 
    (void)state;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_set_debug_port 
(
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
            ? SBGC_PY_OK 
            : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; 
    (void)action; 
    (void)filter; 
    (void)need_confirmation; 
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_debug_port 
(
    sbgc_py_device_t *device, uint16_t *time_ms, uint8_t *port_and_direction,
    uint8_t *command_id, uint8_t *payload, uint8_t *payload_size,
    uint16_t payload_capacity
)
{
#if (SBGC_SERVICE_MODULE)

    sbgcDebugPortData_t native_data;
    uint8_t buffered_payload_size;

    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (time_ms == NULL || port_and_direction == NULL || command_id == NULL ||
        payload == NULL || payload_size == NULL ||
        payload_capacity < SBGC_MAX_PAYLOAD_SIZE)
        return SBGC_PY_INVALID_ARGUMENT;

    /*
     * Debug records are unsolicited.  A record may have arrived while another
     * blocking SerialAPI command was waiting for its own response; in that
     * case SerialAPI ignores the different command ID.  The native COM
     * transport preserves a copy before that filtering happens.
     */
    if (sbgc_py_transport_pop_debug_packet(device->context, time_ms, port_and_direction, command_id, payload, &buffered_payload_size))
    {
        *payload_size = buffered_payload_size;
        return SBGC_PY_OK;
    }

    native_data.payload = payload;

    sbgcCommandStatus_t status = SBGC32_ReadDebugPort(&device->serial_api, &native_data);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    /* The native transport copied this same frame while SerialAPI parsed it. */
    if (sbgc_py_transport_pop_debug_packet(device->context, time_ms, port_and_direction, command_id, payload, &buffered_payload_size))
    {
        *payload_size = buffered_payload_size;
        return SBGC_PY_OK;
    }

    *time_ms = native_data.timeMs;
    *port_and_direction = native_data.portAndDir;
    *command_id = native_data.cmdID;
    *payload_size = SBGC_MAX_PAYLOAD_SIZE;

    return SBGC_PY_OK;
#else
    (void)device; 
    (void)time_ms; 
    (void)port_and_direction; 
    (void)command_id; 
    (void)payload; 
    (void)payload_size;
    (void)payload_capacity;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_request_module_list
(
    sbgc_py_device_t* device, sbgcCAN_ModuleInfo_t* CAN_module_info, ui8 device_num_max
)
{
#if (SBGC_SERVICE_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (CAN_module_info == NULL || device_num_max == 0)
        return SBGC_PY_INVALID_ARGUMENT;

    sbgc_py_status_t can_status = sbgc_py_require_can_port(device);
    if (can_status != SBGC_PY_OK)
        return can_status;

    sbgcCommandStatus_t status = SBGC32_RequestModuleList(&device->serial_api, CAN_module_info, device_num_max);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)CAN_module_info;
    (void)device_num_max;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_CAN_device_scan(sbgc_py_device_t *device, sbgcCAN_DeviceScan_t *CAN_device_scan)
{
#if (SBGC_SERVICE_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (CAN_device_scan == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    sbgc_py_status_t can_status = sbgc_py_require_can_port(device);
    if (can_status != SBGC_PY_OK)
        return can_status;

    sbgcCommandStatus_t status = SBGC32_CAN_DeviceScan(&device->serial_api, CAN_device_scan);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)CAN_device_scan;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_sign_message 
(
    sbgc_py_device_t *device, ui8 sign_type,
    const ui8 tx_message [SBGC_MAX_MESSAGE_LENGTH], ui8 rx_message [SBGC_MAX_MESSAGE_LENGTH]
)
{
#if (SBGC_SERVICE_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (tx_message == NULL || rx_message == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    sbgcCommandStatus_t status = SBGC32_SignMessage(&device->serial_api, sign_type, (const char *)tx_message, (char *)rx_message);

    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
                    ? SBGC_PY_OK
                    : SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device;
    (void)sign_type;
    (void)tx_message;
    (void)rx_message;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_read_transparent_command (sbgc_py_device_t *device, sbgcTransparentCommand_t *cmd)
{
#if (SBGC_SERVICE_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (cmd == NULL || (cmd->payloadSize != 0 && cmd->payload == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

    device_status = sbgc_py_require_can_port(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    sbgcCommandStatus_t status = SBGC32_ReadTransparentCommand(&device->serial_api, cmd);

    return sbgc_py_external_motor_state_result(device, status);
#else
    (void)device;
    (void)cmd;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_send_transparent_command (sbgc_py_device_t* device, const sbgcTransparentCommand_t* cmd)
{
#if (SBGC_SERVICE_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_service_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (cmd == NULL || (cmd->payloadSize != 0 && cmd->payload == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

    device_status = sbgc_py_require_can_port(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    sbgcCommandStatus_t status = SBGC32_SendTransparentCommand(&device->serial_api, cmd);

    return sbgc_py_external_motor_state_result(device, status);
#else
    (void)device;
    (void)cmd;
    return SBGC_PY_MODULE_DISABLED;
#endif
}
