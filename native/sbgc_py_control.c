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


static sbgc_py_status_t sbgc_py_validate_control_device (sbgc_py_device_t *device)
{
    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;
    return SBGC_PY_OK;
}


static sbgc_py_status_t sbgc_py_control_status (sbgc_py_device_t *device, sbgcCommandStatus_t status)
{
    return (status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK)
        ? SBGC_PY_OK
        : SBGC_PY_COMMUNICATION_ERROR;
}


static sbgc_py_status_t sbgc_py_require_control_can (sbgc_py_device_t *device)
{
    return (SerialAPI_GetBoardFeatures(&device->serial_api) & BF_CAN_PORT)
        ? SBGC_PY_OK
        : SBGC_PY_CAN_NOT_SUPPORTED;
}


static sbgc_py_status_t sbgc_py_read_control_confirmation
(
    sbgc_py_device_t *device, ui8 command, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_NEED_CONFIRM_CMD)
    sbgcConfirm_t native_confirmation = { 0 };
    sbgcCommandStatus_t status;
    ui8 attempt;

    if (confirmation == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    for (attempt = 0; attempt < SBGC_PY_CONTROL_CONFIRM_ATTEMPTS; ++attempt)
    {
        memset(&native_confirmation, 0, sizeof(native_confirmation));
        status = SBGC32_CheckConfirmation(&device->serial_api, &native_confirmation, command);
        if (sbgc_py_control_status(device, status) == SBGC_PY_OK)
        {
            sbgc_py_copy_confirmation(confirmation, &native_confirmation);
            return SBGC_PY_OK;
        }
        (void)SBGC32_DeleteCommand(&device->serial_api, CMD_CONFIRM);
    }
    return SBGC_PY_COMMUNICATION_ERROR;
#else
    (void)device; (void)command; (void)confirmation;
    return SBGC_PY_CONFIRMATION_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_control_ext (sbgc_py_device_t *device, const sbgc_py_control_ext_t *control)
{
#if (SBGC_CONTROL_MODULE)
    sbgcControlExt_t native_control = { 0 };
    sbgc_py_status_t device_status;
    sbgcCommandStatus_t status;
    ui8 axis;

    if (device == NULL || control == NULL || control->data_set == 0)
        return SBGC_PY_INVALID_ARGUMENT;
    device_status = sbgc_py_validate_control_device(device);
    if (device_status != SBGC_PY_OK)
        return device_status;
    native_control.dataSet = control->data_set;
    for (axis = 0; axis < 3; ++axis)
    {
        native_control.AxisCE[axis].mode = control->axes[axis].mode;
        native_control.AxisCE[axis].modeFlags = control->axes[axis].flags;
        native_control.AxisCE[axis].speed = control->axes[axis].speed;
        native_control.AxisCE[axis].angle = control->axes[axis].angle;
    }
    status = SBGC32_ControlExt(&device->serial_api, &native_control);
    return sbgc_py_control_status(device, status);
#else
    (void)device; (void)control;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_control_quat
(
    sbgc_py_device_t *device, const sbgc_py_control_quat_t *control,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_CONTROL_MODULE)
    sbgcControlQuat_t native_control = { 0 };
    sbgc_py_status_t device_status;
    sbgcCommandStatus_t status;

    if (device == NULL || control == NULL || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;
    device_status = sbgc_py_validate_control_device(device);
    if (device_status != SBGC_PY_OK)
        return device_status;
    native_control.mode = control->mode;
    native_control.flags = control->flags | (need_confirmation ? CtrlQ_FLAG_NEED_CONFIRM : 0);
    memcpy(native_control.attitude, control->attitude, sizeof(native_control.attitude));
    memcpy(native_control.speed, control->speed, sizeof(native_control.speed));
    status = SBGC32_ControlQuat(&device->serial_api, &native_control);
    if (sbgc_py_control_status(device, status) != SBGC_PY_OK)
        return SBGC_PY_COMMUNICATION_ERROR;
    return need_confirmation
        ? sbgc_py_read_control_confirmation(device, CMD_CONTROL_QUAT, confirmation)
        : SBGC_PY_OK;
#else
    (void)device; (void)control; (void)need_confirmation; (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_control_quat_config
(
    sbgc_py_device_t *device, const sbgc_py_control_quat_config_t *config,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_CONTROL_MODULE)
    sbgcControlQuatConfig_t native_config = { 0 };
    sbgc_py_status_t device_status;
    sbgcCommandStatus_t status;

    if (device == NULL || config == NULL || config->data_set == 0 || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;
    device_status = sbgc_py_validate_control_device(device);
    if (device_status != SBGC_PY_OK)
        return device_status;
    native_config.dataSet = config->data_set;
    memcpy(native_config.maxSpeed, config->max_speed, sizeof(native_config.maxSpeed));
    memcpy(native_config.accLimit, config->acceleration_limit, sizeof(native_config.accLimit));
    memcpy(native_config.jerkSlope, config->jerk_slope, sizeof(native_config.jerkSlope));
    native_config.flags = config->flags;
    native_config.attitudeLPF_Freq = config->attitude_lpf_frequency;
    native_config.speedLPF_Freq = config->speed_lpf_frequency;
#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        status = SBGC32_ControlQuatConfig(&device->serial_api, &native_config, &native_confirmation);
        if (sbgc_py_control_status(device, status) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_ControlQuatConfig(&device->serial_api, &native_config, SBGC_NO_CONFIRM);
    return sbgc_py_control_status(device, status);
#else
    (void)device; (void)config; (void)need_confirmation; (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_ext_motors_action
(
    sbgc_py_device_t *device, ui8 motors, ui8 action,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_CONTROL_MODULE)
    sbgc_py_status_t device_status;
    sbgcCommandStatus_t status;
    sbgcExtMotorID_t ids;

    if (device == NULL || motors == 0 || (motors & 0x80) || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;
    device_status = sbgc_py_validate_control_device(device);
    if (device_status != SBGC_PY_OK)
        return device_status;
    device_status = sbgc_py_require_control_can(device);
    if (device_status != SBGC_PY_OK)
        return device_status;
    ids = (sbgcExtMotorID_t)(motors | (need_confirmation ? EXT_MOTOR_NEED_CONFIRM : 0));
#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        status = SBGC32_ExtMotorsAction(&device->serial_api, ids, (sbgcExtMotorAction_t)action, &native_confirmation);
        if (sbgc_py_control_status(device, status) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_ExtMotorsAction(&device->serial_api, ids, (sbgcExtMotorAction_t)action, SBGC_NO_CONFIRM);
    return sbgc_py_control_status(device, status);
#else
    (void)device; (void)motors; (void)action; (void)need_confirmation; (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_ext_motors_control
(
    sbgc_py_device_t *device, const sbgc_py_ext_motor_control_t *control,
    ui8 motors, ui8 data_set, ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_CONTROL_MODULE)
    sbgcControlExtMotors_t native_control = { 0 };
    sbgc_py_status_t device_status;
    sbgcCommandStatus_t status;
    sbgcExtMotorID_t ids;

    if (device == NULL || control == NULL || motors == 0 || (motors & 0x80) || (data_set & ~0x07) ||
        (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;
    device_status = sbgc_py_validate_control_device(device);
    if (device_status != SBGC_PY_OK)
        return device_status;
    device_status = sbgc_py_require_control_can(device);
    if (device_status != SBGC_PY_OK)
        return device_status;
    native_control.setpoint = control->setpoint;
    native_control.param1 = control->param1;
    ids = (sbgcExtMotorID_t)(motors | (need_confirmation ? EXT_MOTOR_NEED_CONFIRM : 0));
#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        status = SBGC32_ControlExtMotors(&device->serial_api, &native_control, ids, (sbgcExtMotorParam_t)data_set, &native_confirmation);
        if (sbgc_py_control_status(device, status) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_ControlExtMotors(&device->serial_api, &native_control, ids, (sbgcExtMotorParam_t)data_set, SBGC_NO_CONFIRM);
    return sbgc_py_control_status(device, status);
#else
    (void)device; (void)control; (void)motors; (void)data_set; (void)need_confirmation; (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_ext_motors_control_config
(
    sbgc_py_device_t *device, const sbgc_py_ext_motors_control_config_t *config,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_CONTROL_MODULE)
    sbgcExtMotorsControlConfig_t native_config = { 0 };
    sbgc_py_status_t device_status;
    sbgcCommandStatus_t status;

    if (device == NULL || config == NULL || config->motors == 0 || (config->motors & 0x80) || config->data_set == 0 ||
        (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;
    device_status = sbgc_py_validate_control_device(device);
    if (device_status != SBGC_PY_OK)
        return device_status;
    device_status = sbgc_py_require_control_can(device);
    if (device_status != SBGC_PY_OK)
        return device_status;
    native_config.forMotors = config->motors | (need_confirmation ? EXT_MOTOR_NEED_CONFIRM : 0);
    native_config.dataSet = config->data_set;
    native_config.mode = config->mode;
    native_config.maxSpeed = config->max_speed;
    native_config.maxAcceleration = config->max_acceleration;
    native_config.jerkSlope = config->jerk_slope;
    native_config.maxTorque = config->max_torque;
#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        status = SBGC32_ExtMotorsControlConfig(&device->serial_api, &native_config, &native_confirmation);
        if (sbgc_py_control_status(device, status) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif
    status = SBGC32_ExtMotorsControlConfig(&device->serial_api, &native_config, SBGC_NO_CONFIRM);
    return sbgc_py_control_status(device, status);
#else
    (void)device; (void)config; (void)need_confirmation; (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_set_api_virtual_channels_hr
(
    sbgc_py_device_t *device, const i16 *channels, ui8 count
)
{
#if (SBGC_CONTROL_MODULE)
    sbgc_py_status_t device_status;
    sbgcCommandStatus_t status;

    if (device == NULL || channels == NULL || count == 0 || count > SBGC_VIRTUAL_CHANNELS_NUM)
        return SBGC_PY_INVALID_ARGUMENT;
    device_status = sbgc_py_validate_control_device(device);
    if (device_status != SBGC_PY_OK)
        return device_status;
    status = SBGC32_SetAPI_VirtChHR_Control(&device->serial_api, channels, count);
    return sbgc_py_control_status(device, status);
#else
    (void)device; (void)channels; (void)count;
    return SBGC_PY_MODULE_DISABLED;
#endif
}
