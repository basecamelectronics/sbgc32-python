#include "sbgc_py_internal.h"

#include <string.h>


static sbgc_py_status_t sbgc_py_validate_profiles_device (sbgc_py_device_t *device)
{
    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    return SBGC_PY_OK;
}


static sbgc_py_status_t sbgc_py_profiles_status (sbgcCommandStatus_t status, sbgc_py_device_t *device)
{
    return status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK
                    ? SBGC_PY_OK 
                    : SBGC_PY_COMMUNICATION_ERROR;
}


static ui16 sbgc_py_params_size (ui8 block)
{
    switch (block)
    {
        case 0: return sizeof(sbgcMainParams3_t);
        case 1: return sizeof(sbgcMainParamsExt_t);
        case 2: return sizeof(sbgcMainParamsExt2_t);
        case 3: return sizeof(sbgcMainParamsExt3_t);

        default: return 0;
    }
}


sbgc_py_status_t sbgc_py_read_profile_names (sbgc_py_device_t *device, ui8 *names, ui16 size)
{
#if (SBGC_PROFILES_MODULE)
    sbgcProfileNames_t result = { 0 };
    sbgc_py_status_t device_status = sbgc_py_validate_profiles_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (names == NULL || size != sizeof(result))
        return SBGC_PY_INVALID_ARGUMENT;

    if (sbgc_py_profiles_status(SBGC32_ReadProfileNames(&device->serial_api, &result), device) != SBGC_PY_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    memcpy(names, &result, sizeof(result));

    return SBGC_PY_OK;
#else
    (void)device;
    (void)names;
    (void)size;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_write_profile_names
(
    sbgc_py_device_t *device, const ui8 *names, ui16 size,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_PROFILES_MODULE)
    sbgcProfileNames_t values = { 0 };
    sbgc_py_status_t device_status = sbgc_py_validate_profiles_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (names == NULL || size != sizeof(values) || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

    memcpy(&values, names, sizeof(values));

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        if (sbgc_py_profiles_status(SBGC32_WriteProfileNames(&device->serial_api, &values, &native_confirmation), device) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    return sbgc_py_profiles_status(SBGC32_WriteProfileNames(&device->serial_api, &values, SBGC_NO_CONFIRM), device);
#else
    (void)device;
    (void)names;
    (void)size;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_manage_profile_set
(
    sbgc_py_device_t *device, ui8 slot, ui8 action,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_PROFILES_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_profiles_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (slot < sbgcPROFILE_SET_1 || slot > sbgcPROFILE_SET_BACKUP || action < PSA_PROFILE_SET_ACTION_SAVE || action > PSA_PROFILE_SET_ACTION_LOAD ||
        (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        if (sbgc_py_profiles_status(SBGC32_ManageProfileSet(&device->serial_api, (sbgcProfileSet_t)slot, (sbgcProfileSetAction_t)action, &native_confirmation), device) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    return sbgc_py_profiles_status(SBGC32_ManageProfileSet(&device->serial_api, (sbgcProfileSet_t)slot, (sbgcProfileSetAction_t)action, SBGC_NO_CONFIRM), device);
#else
    (void)device;
    (void)slot;
    (void)action;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_write_params_set
(
    sbgc_py_device_t *device, ui8 action,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_PROFILES_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_profiles_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (action > PWF_START_WRITING || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        if (sbgc_py_profiles_status(SBGC32_WriteParamsSet(&device->serial_api, (sbgcProfileWritingFlag_t)action, &native_confirmation), device) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    return sbgc_py_profiles_status(SBGC32_WriteParamsSet(&device->serial_api, (sbgcProfileWritingFlag_t)action, SBGC_NO_CONFIRM), device);
#else
    (void)device;
    (void)action;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_profile_params (sbgc_py_device_t *device, ui8 block, ui8 profile_id, ui8 *result, ui16 size)
{
#if (SBGC_PROFILES_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_profiles_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (result == NULL || size != sbgc_py_params_size(block) || (profile_id > sbgcPROFILE_5 && profile_id != sbgcCURRENT_PROFILE))
        return SBGC_PY_INVALID_ARGUMENT;

    switch (block)
    {
        case 0:
        {
            sbgcMainParams3_t values = { 0 };
            if (sbgc_py_profiles_status(SBGC32_ReadParams3(&device->serial_api, &values, (sbgcProfile_t)profile_id), device) != SBGC_PY_OK)
                return SBGC_PY_COMMUNICATION_ERROR;

            memcpy(result, &values, sizeof(values));

            return SBGC_PY_OK;
        }
        case 1:
        {
            sbgcMainParamsExt_t values = { 0 };
            if (sbgc_py_profiles_status(SBGC32_ReadParamsExt(&device->serial_api, &values, (sbgcProfile_t)profile_id), device) != SBGC_PY_OK)
                return SBGC_PY_COMMUNICATION_ERROR;

            memcpy(result, &values, sizeof(values));

            return SBGC_PY_OK;
        }
        case 2:
        {
            sbgcMainParamsExt2_t values = { 0 };
            if (sbgc_py_profiles_status(SBGC32_ReadParamsExt2(&device->serial_api, &values, (sbgcProfile_t)profile_id), device) != SBGC_PY_OK)
                return SBGC_PY_COMMUNICATION_ERROR;

            memcpy(result, &values, sizeof(values));

            return SBGC_PY_OK;
        }
        case 3:
        {
            sbgcMainParamsExt3_t values = { 0 };
            if (sbgc_py_profiles_status(SBGC32_ReadParamsExt3(&device->serial_api, &values, (sbgcProfile_t)profile_id), device) != SBGC_PY_OK)
                return SBGC_PY_COMMUNICATION_ERROR;

            memcpy(result, &values, sizeof(values));

            return SBGC_PY_OK;
        }

        default:
            return SBGC_PY_INVALID_ARGUMENT;
    }
#else
    (void)device;
    (void)block;
    (void)profile_id;
    (void)result;
    (void)size;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_write_profile_params
(
    sbgc_py_device_t *device, ui8 block, const ui8 *data, ui16 size,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_PROFILES_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_profiles_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (data == NULL || size != sbgc_py_params_size(block) || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        sbgcCommandStatus_t status;

        switch (block)
        {
            case 0: 
            { 
                sbgcMainParams3_t values; 
                memcpy(&values, data, sizeof(values)); 

                status = SBGC32_WriteParams3(&device->serial_api, &values, &native_confirmation); 
                
                break; 
            }
            case 1: 
            { 
                sbgcMainParamsExt_t values; 
                memcpy(&values, data, sizeof(values)); 

                status = SBGC32_WriteParamsExt(&device->serial_api, &values, &native_confirmation); 

                break; 
            }
            case 2: 
            { 
                sbgcMainParamsExt2_t values; 
                memcpy(&values, data, sizeof(values));
                
                status = SBGC32_WriteParamsExt2(&device->serial_api, &values, &native_confirmation);
                
                break; 
            }
            case 3: 
            { 
                sbgcMainParamsExt3_t values; 
                memcpy(&values, data, sizeof(values)); 
                
                status = SBGC32_WriteParamsExt3(&device->serial_api, &values, &native_confirmation); 
                
                break; 
            }

            default: return SBGC_PY_INVALID_ARGUMENT;
        }

        if (sbgc_py_profiles_status(status, device) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    switch (block)
    {
        case 0: 
        { 
            sbgcMainParams3_t values; 
            memcpy(&values, data, sizeof(values)); 
            
            return sbgc_py_profiles_status(SBGC32_WriteParams3(&device->serial_api, &values, SBGC_NO_CONFIRM), device); 
        }
        case 1: 
        { 
            sbgcMainParamsExt_t values; 
            memcpy(&values, data, sizeof(values)); 
        
            return sbgc_py_profiles_status(SBGC32_WriteParamsExt(&device->serial_api, &values, SBGC_NO_CONFIRM), device); 
        }
        case 2: 
        {
            sbgcMainParamsExt2_t values; 
            memcpy(&values, data, sizeof(values)); 
            
            return sbgc_py_profiles_status(SBGC32_WriteParamsExt2(&device->serial_api, &values, SBGC_NO_CONFIRM), device); 
        }
        case 3: 
        { 
            sbgcMainParamsExt3_t values; 
            memcpy(&values, data, sizeof(values)); 
            
            return sbgc_py_profiles_status(SBGC32_WriteParamsExt3(&device->serial_api, &values, SBGC_NO_CONFIRM), device); 
        }

        default: return SBGC_PY_INVALID_ARGUMENT;
    }
#else
    (void)device;
    (void)block;
    (void)data;
    (void)size;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_use_profile_defaults (sbgc_py_device_t *device, ui8 profile_id)
{
#if (SBGC_PROFILES_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_profiles_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (profile_id > sbgcPROFILE_5 && profile_id != sbgcCURRENT_PROFILE)
        return SBGC_PY_INVALID_ARGUMENT;

    return sbgc_py_profiles_status(SBGC32_UseDefaults(&device->serial_api, (sbgcProfile_t)profile_id), device);
#else
    (void)device;
    (void)profile_id;
    return SBGC_PY_MODULE_DISABLED;
#endif
}
