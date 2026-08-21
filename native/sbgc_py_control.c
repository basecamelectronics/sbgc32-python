#include "sbgc_py_internal.h"

#include <string.h>

/* Do not retransmit a physical movement while waiting for confirmation. */
#define SBGC_PY_CONTROL_CONFIRM_ATTEMPTS 3

sbgc_py_status_t sbgc_py_control (
    sbgc_py_device_t *device,
    const uint8_t modes[3],
    const int16_t speeds[3],
    const int16_t angles[3],
    uint8_t need_confirmation,
    sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_CONTROL_MODULE)
    sbgcControl_t native_control = { 0 };
    sbgcCommandStatus_t status;
    uint8_t axis;

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
        uint8_t attempt;

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
        confirmation->status = (uint8_t)native_confirmation.status;
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

sbgc_py_status_t sbgc_py_control_config (
    sbgc_py_device_t *device,
    const sbgc_py_control_config_t *config,
    uint8_t need_confirmation,
    sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_CONTROL_MODULE)
    sbgcControlConfig_t native_config = { 0 };
    sbgcCommandStatus_t status;
    uint8_t axis;

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
