#include "sbgc_py_internal.h"

#include <string.h>

sbgc_py_status_t sbgc_py_get_adj_vars (
    sbgc_py_device_t *device,
    const uint8_t *ids,
    uint8_t count,
    sbgc_py_adjustable_variable_t *result
)
{
#if (SBGC_ADJVAR_MODULE)
    sbgcAdjVarGeneral_t native_vars[SBGC_ADJ_VARS_MAX_NUM_PACKET] = { 0 };
    sbgcCommandStatus_t status;
    uint8_t index;

    if (device == NULL || ids == NULL || result == NULL ||
        count == 0 || count > SBGC_ADJ_VARS_MAX_NUM_PACKET)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    for (index = 0; index < count; ++index)
        native_vars[index].ID = (sbgcAdjVarID_t)ids[index];

    device->last_tx_size = 0;
    device->last_rx_size = 0;
    status = SBGC32_GetAdjVarValues(&device->serial_api, native_vars, count);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
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
sbgc_py_status_t sbgc_py_set_adj_vars (
    sbgc_py_device_t *device,
    const sbgc_py_adjustable_variable_t *variables,
    uint8_t count,
    uint8_t need_confirmation,
    sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_ADJVAR_MODULE)
    sbgcAdjVarGeneral_t native_vars[SBGC_ADJ_VARS_MAX_NUM_PACKET] = { 0 };
    sbgcCommandStatus_t status;
    uint8_t index;

    if (device == NULL || variables == NULL ||
        count == 0 || count > SBGC_ADJ_VARS_MAX_NUM_PACKET)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;
    if (need_confirmation && confirmation == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    for (index = 0; index < count; ++index)
    {
        native_vars[index].ID = (sbgcAdjVarID_t)variables[index].id;
        native_vars[index].value = variables[index].value;
        native_vars[index].syncFlag = AV_NOT_SYNCHRONIZED;
    }

    device->last_tx_size = 0;
    device->last_rx_size = 0;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = SBGC32_SetAdjVarValues(&device->serial_api, native_vars, count, &native_confirmation);

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

    status = SBGC32_SetAdjVarValues(&device->serial_api, native_vars, count, SBGC_NO_CONFIRM);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
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


sbgc_py_status_t sbgc_py_save_adj_vars (
    sbgc_py_device_t *device,
    const uint8_t *ids,
    uint8_t count,
    uint8_t need_confirmation,
    sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_ADJVAR_MODULE)
    sbgcAdjVarGeneral_t native_vars[SBGC_ADJ_VARS_MAX_QUANTITY] = { 0 };
    sbgcCommandStatus_t status;
    uint8_t index;

    if (device == NULL || count > SBGC_ADJ_VARS_MAX_QUANTITY || (count != 0 && ids == NULL))
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;
    if (need_confirmation && confirmation == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    for (index = 0; index < count; ++index)
    {
        native_vars[index].ID = (sbgcAdjVarID_t)ids[index];
        native_vars[index].saveFlag = AV_NOT_SAVED;
    }

    device->last_tx_size = 0;
    device->last_rx_size = 0;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = count == 0
            ? SBGC32_SaveAllActiveAdjVarsToEEPROM(&device->serial_api, &native_confirmation)
            : SBGC32_SaveAdjVarsToEEPROM(&device->serial_api, native_vars, count, &native_confirmation);

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

    status = count == 0
        ? SBGC32_SaveAllActiveAdjVarsToEEPROM(&device->serial_api, SBGC_NO_CONFIRM)
        : SBGC32_SaveAdjVarsToEEPROM(&device->serial_api, native_vars, count, SBGC_NO_CONFIRM);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
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
