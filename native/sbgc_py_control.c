#include "sbgc_py_internal.h"

#include <string.h>

sbgc_py_status_t sbgc_py_control (
    sbgc_py_device_t *device,
    const ui8 modes[3],
    const i16 speeds[3],
    const i16 angles[3],
    ui8 need_confirmation,
    sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_CONTROL_MODULE)


    sbgcControl_t native_control = { 0 };
    sbgcCommandStatus_t status;
    ui8 axis;

    if (device == NULL || modes == NULL || speeds == NULL || angles == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    for (axis = 0; axis < 3; ++axis)
    {
        native_control.mode[axis] = modes[axis];
        native_control.AxisC[axis].speed = speeds[axis];
        native_control.AxisC[axis].angle = angles[axis];
    }

    status = SBGC32_Control(&device->serial_api, &native_control);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    if (!need_confirmation)
        return SBGC_PY_OK;

#if (SBGC_NEED_CONFIRM_CMD)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        ui8 attempt;

        if (confirmation == NULL)
            return SBGC_PY_INVALID_ARGUMENT;

        for (attempt = 0; attempt < SBGC_PY_CONTROL_CONFIRM_ATTEMPTS; ++attempt)
        {
            memset(&native_confirmation, 0, sizeof(native_confirmation));
            status = SBGC32_CheckConfirmation(&device->serial_api, &native_confirmation, CMD_CONTROL);
            if (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
                break;

            (void)SBGC32_DeleteCommand(&device->serial_api, CMD_CONFIRM);
        }
        if (attempt == SBGC_PY_CONTROL_CONFIRM_ATTEMPTS)
            return SBGC_PY_COMMUNICATION_ERROR;

        confirmation->command_id = native_confirmation.commandID;
        confirmation->status = (ui8)native_confirmation.status;
        confirmation->command_data = native_confirmation.cmdData;
        confirmation->error_code = native_confirmation.errorCode;
        memcpy(confirmation->error_data, native_confirmation.errorData, sizeof(confirmation->error_data));
    }

    return SBGC_PY_OK;
#else
    (void)confirmation;
    return SBGC_PY_CONFIRMATION_DISABLED;
#endif

#else
    (void)device;
    (void)modes;
    (void)speeds;
    (void)angles;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}

sbgc_py_status_t sbgc_py_control_config 
(
    sbgc_py_device_t *device, const sbgc_py_control_config_t *config,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_CONTROL_MODULE)

    sbgcControlConfig_t native_config = { 0 };
    sbgcCommandStatus_t status;
    ui8 axis;

    if (device == NULL || config == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;
    if (need_confirmation && confirmation == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    native_config.timeoutMS = config->timeout_ms;
    native_config.ch1_Priority = config->channel_priorities[0];
    native_config.ch2_Priority = config->channel_priorities[1];
    native_config.ch3_Priority = config->channel_priorities[2];
    native_config.ch4_Priority = config->channel_priorities[3];
    native_config.thisChPriority = config->channel_priorities[4];

    for (axis = 0; axis < 3; ++axis)
    {
        native_config.AxisCCtrl[axis].angleLPF = config->axis[axis].angle_lpf;
        native_config.AxisCCtrl[axis].speedLPF = config->axis[axis].speed_lpf;
        native_config.AxisCCtrl[axis].RC_LPF = config->axis[axis].rc_lpf;
        native_config.AxisCCtrl[axis].accLimit = config->axis[axis].acceleration_limit;
        native_config.AxisCCtrl[axis].jerkSlope = config->axis[axis].jerk_slope;
    }

    native_config.RC_ExpoRate = config->rc_expo_rate;
    native_config.flags = config->flags;
    native_config.EulerOrder = config->euler_order;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };

        status = SBGC32_ControlConfig(
            &device->serial_api, &native_config, &native_confirmation
        );
        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        confirmation->command_id = native_confirmation.commandID;
        confirmation->status = (ui8)native_confirmation.status;
        confirmation->command_data = native_confirmation.cmdData;
        confirmation->error_code = native_confirmation.errorCode;

        memcpy(confirmation->error_data, native_confirmation.errorData, sizeof(confirmation->error_data));

        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    status = SBGC32_ControlConfig(&device->serial_api, &native_config, SBGC_NO_CONFIRM);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)config;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}

SBGC_PY_API sbgc_py_status_t sbgc_py_set_api_virtual_channels (sbgc_py_device_t* device, const i16* API_virt_ch, ui8 ch_quan)
{
#if (SBGC_CONTROL_MODULE)

    sbgcCommandStatus_t status;

    if (device == NULL || API_virt_ch == NULL || !(ch_quan >= 1 && ch_quan <= SBGC_VIRTUAL_CHANNELS_NUM))
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    status = SBGC32_SetAPI_VirtChControl(&device->serial_api, API_virt_ch, ch_quan);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;

#else
    (void)device;
    (void)API_virt_ch;
    (void)ch_quan;
    return SBGC_PY_MODULE_DISABLED;
#endif
}