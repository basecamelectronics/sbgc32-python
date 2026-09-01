#include "sbgc_py_internal.h"

#include <string.h>

static sbgc_py_status_t sbgc_py_validate_adjvars_device (sbgc_py_device_t *device)
{
    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    return SBGC_PY_OK;
}


static sbgc_py_status_t sbgc_py_adjvars_status (sbgc_py_device_t *device, sbgcCommandStatus_t status)
{
    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
                    ? SBGC_PY_OK
                    : SBGC_PY_COMMUNICATION_ERROR;
}


sbgc_py_status_t sbgc_py_get_adj_vars 
(
    sbgc_py_device_t *device, const uint8_t *ids,
    uint8_t count, sbgc_py_adjustable_variable_t *result
)
{
#if (SBGC_ADJVAR_MODULE)

    sbgcAdjVarGeneral_t native_vars[SBGC_ADJ_VARS_MAX_NUM_PACKET] = { 0 };

    uint8_t index;

    if (device == NULL || ids == NULL || result == NULL || count == 0 || count > SBGC_ADJ_VARS_MAX_NUM_PACKET)
        return SBGC_PY_INVALID_ARGUMENT;

    sbgc_py_status_t device_status = sbgc_py_validate_adjvars_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    for (index = 0; index < count; ++index)
        native_vars[index].ID = (sbgcAdjVarID_t)ids[index];

    sbgcCommandStatus_t status = SBGC32_GetAdjVarValues(&device->serial_api, native_vars, count);

    if (sbgc_py_adjvars_status(device, status) != SBGC_PY_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    for (index = 0; index < count; ++index)
    {
        result[index].id = (uint8_t)native_vars[index].ID;
        result[index].value = native_vars[index].value;
    }

    return SBGC_PY_OK;
#else
    (void)device;
    (void)ids;
    (void)count;
    (void)result;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_set_adj_vars 
(
    sbgc_py_device_t *device, const sbgc_py_adjustable_variable_t *variables,
    uint8_t count, uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_ADJVAR_MODULE)

    sbgcCommandStatus_t status;
    sbgcAdjVarGeneral_t native_vars[SBGC_ADJ_VARS_MAX_NUM_PACKET] = { 0 };

    uint8_t index;

    if (device == NULL || variables == NULL || count == 0 || count > SBGC_ADJ_VARS_MAX_NUM_PACKET)
        return SBGC_PY_INVALID_ARGUMENT;

    sbgc_py_status_t device_status = sbgc_py_validate_adjvars_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (need_confirmation && confirmation == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    for (index = 0; index < count; ++index)
    {
        native_vars[index].ID = (sbgcAdjVarID_t)variables[index].id;
        native_vars[index].value = variables[index].value;
        native_vars[index].syncFlag = AV_NOT_SYNCHRONIZED;
    }

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = SBGC32_SetAdjVarValues(&device->serial_api, native_vars, count, &native_confirmation);

        if (sbgc_py_adjvars_status(device, status) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    status = SBGC32_SetAdjVarValues(&device->serial_api, native_vars, count, SBGC_NO_CONFIRM);

    if (sbgc_py_adjvars_status(device, status) != SBGC_PY_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)variables;
    (void)count;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_save_adj_vars 
(
    sbgc_py_device_t *device, const uint8_t *ids, uint8_t count,
    uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_ADJVAR_MODULE)
    
    sbgcAdjVarGeneral_t native_vars[SBGC_ADJ_VARS_MAX_QUANTITY] = { 0 };

    sbgcCommandStatus_t status;

    uint8_t index;

    if (count > SBGC_ADJ_VARS_MAX_QUANTITY || (count != 0 && ids == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

    sbgc_py_status_t device_status = sbgc_py_validate_adjvars_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (need_confirmation && confirmation == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    for (index = 0; index < count; ++index)
    {
        native_vars[index].ID = (sbgcAdjVarID_t)ids[index];
        native_vars[index].saveFlag = AV_NOT_SAVED;
    }

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = count == 0
                        ? SBGC32_SaveAllActiveAdjVarsToEEPROM(&device->serial_api, &native_confirmation)
                        : SBGC32_SaveAdjVarsToEEPROM(&device->serial_api, native_vars, count, &native_confirmation);

        if (sbgc_py_adjvars_status(device, status) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    status = count == 0
                    ? SBGC32_SaveAllActiveAdjVarsToEEPROM(&device->serial_api, SBGC_NO_CONFIRM)
                    : SBGC32_SaveAdjVarsToEEPROM(&device->serial_api, native_vars, count, SBGC_NO_CONFIRM);

    if (sbgc_py_adjvars_status(device, status) != SBGC_PY_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)ids;
    (void)count;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_get_adj_vars_float
(
    sbgc_py_device_t *device, const uint8_t *ids, uint8_t count,
    sbgc_py_adjustable_variable_float_t *result
)
{
#if (SBGC_ADJVAR_MODULE)

    sbgcAdjVarGeneral_t native_vars[SBGC_ADJ_VARS_MAX_NUM_PACKET] = { 0 };

    uint8_t index;

    sbgc_py_status_t device_status;

    if (ids == NULL || result == NULL || count == 0 || count > SBGC_ADJ_VARS_MAX_NUM_PACKET)
        return SBGC_PY_INVALID_ARGUMENT;

    device_status = sbgc_py_validate_adjvars_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    for (index = 0; index < count; ++index)
        native_vars[index].ID = (sbgcAdjVarID_t)ids[index];

    sbgcCommandStatus_t status = SBGC32_GetAdjVarValuesFloat(&device->serial_api, native_vars, count);
    if (sbgc_py_adjvars_status(device, status) != SBGC_PY_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    for (index = 0; index < count; ++index)
    {
        result[index].id = (uint8_t)native_vars[index].ID;
        result[index].value = native_vars[index].value_f;
    }

    return SBGC_PY_OK;
#else
    (void)device; (void)ids; (void)count; (void)result;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_set_adj_vars_float
(
    sbgc_py_device_t *device, const sbgc_py_adjustable_variable_float_t *variables,
    uint8_t count, uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_ADJVAR_MODULE)
    sbgcAdjVarGeneral_t native_vars [SBGC_ADJ_VARS_MAX_NUM_PACKET] = { 0 };

    sbgcCommandStatus_t status;
    sbgc_py_status_t device_status;

    uint8_t index;

    if (variables == NULL || count == 0 || count > SBGC_ADJ_VARS_MAX_NUM_PACKET || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

    device_status = sbgc_py_validate_adjvars_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    for (index = 0; index < count; ++index)
    {
        native_vars[index].ID = (sbgcAdjVarID_t)variables[index].id;
        native_vars[index].value_f = variables[index].value;
        native_vars[index].syncFlag = AV_NOT_SYNCHRONIZED;
    }

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = SBGC32_SetAdjVarValuesFloat(&device->serial_api, native_vars, count, &native_confirmation);

        if (sbgc_py_adjvars_status(device, status) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_SetAdjVarValuesFloat(&device->serial_api, native_vars, count, SBGC_NO_CONFIRM);

    return sbgc_py_adjvars_status(device, status);
#else
    (void)device; 
    (void)variables; 
    (void)count; 
    (void)need_confirmation; 
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_adj_vars_config (sbgc_py_device_t *device, sbgc_py_adjvars_config_t *config)
{
#if (SBGC_ADJVAR_MODULE)
    sbgc_py_status_t device_status;
    
    if (config == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    device_status = sbgc_py_validate_adjvars_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    sbgcCommandStatus_t status = SBGC32_ReadAdjVarsCfg(&device->serial_api, (sbgcAdjVarsCfg_t *)config);

    return sbgc_py_adjvars_status(device, status);
#else
    (void)device; 
    (void)config;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_write_adj_vars_config
(
    sbgc_py_device_t *device, const sbgc_py_adjvars_config_t *config,
    uint8_t need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_ADJVAR_MODULE)

    sbgc_py_status_t device_status;
    sbgcCommandStatus_t status;

    if (config == NULL || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

    device_status = sbgc_py_validate_adjvars_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = SBGC32_WriteAdjVarsCfg(&device->serial_api, (const sbgcAdjVarsCfg_t *)config, &native_confirmation);

        if (sbgc_py_adjvars_status(device, status) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_WriteAdjVarsCfg(&device->serial_api, (const sbgcAdjVarsCfg_t *)config, SBGC_NO_CONFIRM);

    return sbgc_py_adjvars_status(device, status);
#else
    (void)device; 
    (void)config; 
    (void)need_confirmation; 
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_get_adj_vars_state
(
    sbgc_py_device_t *device, const sbgc_py_adjvars_state_request_t *request,
    sbgc_py_adjvars_state_t *result
)
{
#if (SBGC_ADJVAR_MODULE)

    sbgcAdjVarsState_t native_state = { 0 };

    if (request == NULL || result == NULL || request->trigger_slot >= SBGC_ADJ_VAR_TRIGGER_SLOTS_NUM)
        return SBGC_PY_INVALID_ARGUMENT;

    sbgc_py_status_t device_status = sbgc_py_validate_adjvars_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (!(SerialAPI_GetBoardFeatures(&device->serial_api) & BF_STATE_VARS))
        return SBGC_PY_STATE_VARS_NOT_SUPPORTED;

    native_state.triggerSlot = request->trigger_slot;
    native_state.analogSrcID = request->analog_source_id;
    native_state.analogVarID = (sbgcAdjVarID_t)request->analog_variable_id;
    native_state.lutSrcID = request->lut_source_id;
    native_state.lutVarID = (sbgcAdjVarID_t)request->lut_variable_id;
    native_state.triggerSlot__old = request->trigger_slot;
    native_state.analogSlot = (ui8)request->analog_source_id;

    sbgcCommandStatus_t status = SBGC32_RequestAdjVarsState(&device->serial_api, &native_state);

    if (sbgc_py_adjvars_status(device, status) != SBGC_PY_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    if (device->serial_api._api->baseFirmwareVersion < 2625)
    {
        result->trigger_rc_data = native_state.triggerRC_Data__old;
        result->trigger_action = native_state.triggerAction__old;
        result->analog_source_value = native_state.analogRC_Data;
        result->analog_variable_value = (float)native_state.analogValue;
        result->lut_source_value = 0;
        result->lut_variable_value = 0.0f;
    }

    else
    {
        result->trigger_rc_data = native_state.triggerRC_Data;
        result->trigger_action = native_state.triggerAction;
        result->analog_source_value = native_state.analogSrcValue;
        result->analog_variable_value = native_state.analogVarValue;
        result->lut_source_value = native_state.lutSrcValue;
        result->lut_variable_value = native_state.lutVarValue;
    }

    return SBGC_PY_OK;
#else
    (void)device;
    (void)request; 
    (void)result;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_get_adj_vars_info
(
    sbgc_py_device_t *device, uint8_t start_id, sbgc_py_adjvar_info_t *result,
    uint8_t capacity, uint8_t *count
)
{
#if (SBGC_ADJVAR_MODULE)

    sbgcAdjVarGeneral_t native_vars[SBGC_ADJ_VARS_MAX_QUANTITY] = { 0 };

    uint8_t index;

    if (device == NULL || result == NULL || count == NULL || capacity == 0)
        return SBGC_PY_INVALID_ARGUMENT;

    sbgc_py_status_t device_status = sbgc_py_validate_adjvars_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    for (index = 0; index < SBGC_ADJ_VARS_MAX_QUANTITY; ++index)
        native_vars[index].ID = ADJ_VAR_UNDEFINED;

    sbgcCommandStatus_t status = SBGC32_RequestAdjVarsInfo(&device->serial_api, native_vars, (sbgcAdjVarID_t)start_id);

    if (sbgc_py_adjvars_status(device, status) != SBGC_PY_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    *count = 0;
    for (index = 0; index < SBGC_ADJ_VARS_MAX_QUANTITY && index < capacity; ++index)
    {
        if (native_vars[index].ID == ADJ_VAR_UNDEFINED)
            break;

        result[index].id = (ui8)native_vars[index].ID;
        result[index].min_value = native_vars[index].minValue;
        result[index].max_value = native_vars[index].maxValue;
        result[index].value = native_vars[index].value;
        ++(*count);
    }

    return SBGC_PY_OK;
#else
    (void)device;
    (void)start_id; 
    (void)result;
    (void)capacity;
    (void)count;
    return SBGC_PY_MODULE_DISABLED;
#endif
}
