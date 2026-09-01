#include "sbgc_py_internal.h"

#include <string.h>


sbgc_py_status_t sbgc_py_get_angles (sbgc_py_device_t *device, sbgc_py_angles_t *angles)
{
#if (SBGC_REALTIME_MODULE)

    sbgcGetAngles_t native_angles = { 0 };
    ui8 axis;

    if (device == NULL || angles == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_GetAngles(&device->serial_api, &native_angles);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    for (axis = ROLL; axis <= YAW; axis++)
    {
        ((float *)&angles->imu)[axis] = sbgcDegreeToAngle(native_angles.AxisGA[axis].IMU_Angle);
        ((float *)&angles->target)[axis] = sbgcDegreeToAngle(native_angles.AxisGA[axis].targetAngle);
        ((float *)&angles->target_speed)[axis] = sbgcValueToSpeed(native_angles.AxisGA[axis].targetSpeed);
    }

    return SBGC_PY_OK;
#else
    (void)device;
    (void)angles;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_get_angles_ext (sbgc_py_device_t *device, sbgc_py_angles_ext_t *angles)
{
#if (SBGC_REALTIME_MODULE)

    sbgcGetAnglesExt_t  native_angles_ext = { 0 };
    ui8 axis;

    if (device == NULL || angles == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_GetAnglesExt(&device->serial_api, &native_angles_ext);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    for (axis = ROLL; axis <= YAW; axis++)
    {
        angles->axis_gae[axis].imu_angle = native_angles_ext.AxisGAE[axis].IMU_Angle;
        angles->axis_gae[axis].target_angle = native_angles_ext.AxisGAE[axis].targetAngle;
        angles->axis_gae[axis].frame_cam_angle = native_angles_ext.AxisGAE[axis].frameCamAngle;

        memcpy(angles->axis_gae[axis].reserved, native_angles_ext.AxisGAE[axis].reserved, sizeof(angles->axis_gae[axis].reserved));
    }

    return SBGC_PY_OK;

#else
    (void)device;
    (void)angles;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


static sbgc_py_status_t sbgc_py_get_realtime_data (sbgc_py_device_t *device, sbgc_py_realtime_data_t *realtime_data, sbgcBoolean_t extended)
{
#if (SBGC_REALTIME_MODULE)

    sbgcRealTimeData_t native_realtime_data = { 0 };

    if (device == NULL || realtime_data == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = extended
        ? SBGC32_ReadRealTimeData4(&device->serial_api, &native_realtime_data)
        : SBGC32_ReadRealTimeData3(&device->serial_api, &native_realtime_data);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    memcpy(realtime_data, &native_realtime_data, sizeof(*realtime_data));

    return SBGC_PY_OK;

#else
    (void)device;
    (void)realtime_data;
    (void)extended;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_get_realtime_data_3 (sbgc_py_device_t *device, sbgc_py_realtime_data_t *realtime_data)
{
    return sbgc_py_get_realtime_data(device, realtime_data, sbgcOFF);
}


sbgc_py_status_t sbgc_py_get_realtime_data_4 (sbgc_py_device_t *device, sbgc_py_realtime_data_t *realtime_data)
{
    return sbgc_py_get_realtime_data(device, realtime_data, sbgcON);
}


sbgc_py_status_t sbgc_py_get_realtime_data_custom (sbgc_py_device_t *device, uint32_t flags, uint8_t *result, uint8_t payload_size)
{
#if (SBGC_REALTIME_MODULE)

    if (device == NULL || result == NULL || payload_size < 2)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    memset(result, 0, (size_t)payload_size + 4);
    memcpy(result, &flags, sizeof(flags));

    sbgcCommandStatus_t status = SBGC32_RequestRealTimeDataCustom(&device->serial_api, result, payload_size);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)flags;
    (void)result;
    (void)payload_size;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_rc_inputs (sbgc_py_device_t* device, const uint8_t* sources, uint8_t count, int16_t* values)
{
#if (SBGC_REALTIME_MODULE)
    sbgcRC_Inputs_t native_imputs[SBGC_ALL_RC_CHANNELS_NUM] = { 0 };

	if (device == NULL || sources == NULL || values == NULL || count == 0 || count > SBGC_ALL_RC_CHANNELS_NUM)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    ui8 i;
    for (i = 0; i < count; i++)
		native_imputs[i].RC_Src = sources[i];

    sbgcCommandStatus_t status = SBGC32_ReadRC_Inputs(&device->serial_api, native_imputs, ICF_DONT_TRY_TO_INIT_INPUT, count);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    for (i = 0; i < count; i++)
        values[i] = native_imputs[i].RC_Val;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)sources;
    (void)count;
    (void)values;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


static sbgc_py_status_t sbgc_py_update_data_stream
(
    sbgc_py_device_t  *device,
    const sbgc_data_stream_interval_t *data_stream_interval,
    ui8 need_confirmation,
    sbgc_py_confirmation_t *confirmation,
    sbgcBoolean_t stop
)
{
#if (SBGC_REALTIME_MODULE)

    sbgcDataStreamInterval_t native_stream = { 0 };
    sbgcConfirm_t native_confirmation = { 0 };

    sbgcConfirm_t *confirm = SBGC_NO_CONFIRM;

    if (device == NULL || data_stream_interval == NULL || data_stream_interval->syncToData > 1
                       || (!stop && data_stream_interval->intervalMs == 0) || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    native_stream = *data_stream_interval;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
        confirm = &native_confirmation;
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    sbgcCommandStatus_t status = stop
        ? SBGC32_StopDataStream(&device->serial_api, &native_stream, confirm)
        : SBGC32_StartDataStream(&device->serial_api, &native_stream, confirm);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    if (need_confirmation)
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

    return SBGC_PY_OK;

#else
    (void)device;
    (void)data_stream_interval;
    (void)need_confirmation;
    (void)confirmation;
    (void)stop;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_start_data_stream
(
    sbgc_py_device_t* device, const sbgc_data_stream_interval_t* data_stream_interval,
    ui8 need_confirmation, sbgc_py_confirmation_t* confirmation
)
{
    return sbgc_py_update_data_stream(device, data_stream_interval, need_confirmation, confirmation, sbgcFALSE);
}


sbgc_py_status_t sbgc_py_stop_data_stream
(
    sbgc_py_device_t* device, const sbgc_data_stream_interval_t* data_stream_interval,
    ui8 need_confirmation, sbgc_py_confirmation_t* confirmation
)
{
    return sbgc_py_update_data_stream(device, data_stream_interval, need_confirmation, confirmation, sbgcTRUE);
}


sbgc_py_status_t sbgc_py_read_data_stream
(
    sbgc_py_device_t *device, ui8 cmd_id, ui8 *data_straem_struct, ui8 size
)
{
#if (SBGC_REALTIME_MODULE)

    if (device == NULL || data_straem_struct == NULL || size <= 0)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_ReadDataStream(&device->serial_api, (sbgcDataStreamCommand_t)cmd_id, data_straem_struct, size);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;

#else
    (void)device;
    (void)cmd_id;
    (void)data_stream_struct;
    (void)size;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_request_debug_var_info_3
(
    sbgc_py_device_t* device, sbgc_debug_var_info_3_t* debug_var_info_3,
    ui8 statuc_index, ui8 var_count
)
{
#if (SBGC_REALTIME_MODULE)

    if (device == NULL || debug_var_info_3 == NULL || var_count == 0)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_RequestDebugVarInfo3(&device->serial_api, debug_var_info_3, statuc_index, var_count);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;

#else
    (void)device;
    (void)debug_var_info_3;
    (void)statuc_index;
    (void)var_count;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_request_debug_var_values_3 (sbgc_py_device_t* device, sbgc_debug_var_values_3_t* debug_var_values_3)
{
#if (SBGC_REALTIME_MODULE)

        if (device == NULL || debug_var_values_3 == NULL || debug_var_values_3->debugVar3_Info == NULL)
            return SBGC_PY_INVALID_ARGUMENT;

        if ((debug_var_values_3->mask == NULL) != (debug_var_values_3->maskQuan == 0)) // check mask
            return SBGC_PY_INVALID_ARGUMENT;

        if (!device->connected)
            return SBGC_PY_NOT_CONNECTED;

        if (current_device != device)
            return SBGC_PY_ERROR;

        sbgcCommandStatus_t status = SBGC32_RequestDebugVarValue3(&device->serial_api, debug_var_values_3);

        if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
            return SBGC_PY_COMMUNICATION_ERROR;

        return SBGC_PY_OK;

#else
        (void)device;
        (void)debug_var_values_3;
        return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_select_imu_3
(
    sbgc_py_device_t* device, ui8 imu_type, ui8 action, ui16 time_ms,
    ui8 need_confirmation, sbgc_py_confirmation_t* confirmation
)
{
#if (SBGC_REALTIME_MODULE)

    sbgcConfirm_t native_confirmation = { 0 };
    sbgcConfirm_t* confirm = SBGC_NO_CONFIRM;

    if (device == NULL || imu_type > sbgcIMU_TYPE_FRAME || action > SIMUA_COPY_CALIB_FROM_MAIN_EEPROM ||
        (action == SIMUA_SIMPLE_SELECT && imu_type == sbgcIMU_TYPE_CURRENTLY_ACTIVE) ||
        (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
        confirm = &native_confirmation;
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    sbgcCommandStatus_t status = SBGC32_SelectIMU_3(
        &device->serial_api,
        (sbgcIMU_Type_t)imu_type,
        (sbgcSelectIMU_Action_t)action,
        time_ms,
        confirm
    );

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    if (need_confirmation)
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);

    return SBGC_PY_OK;

#else
    (void)device;
    (void)imu_type;
    (void)action;
    (void)time_ms;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


SBGC_PY_API sbgc_py_status_t sbgc_py_control_quat_status
(
    sbgc_py_device_t* device, ui32 flags, ui8* result, ui8 result_size
)
{
#if (SBGC_REALTIME_MODULE)

    if (device == NULL || result == NULL || result_size == 0 || (flags & ~0x03FFUL) != 0)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    sbgcCommandStatus_t status = SBGC32_ControlQuatStatus(&device->serial_api, (sbgcControlQuatStatusFlag_t)flags, result, result_size);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;

#else
    (void)device;
    (void)flags;
    (void)result;
    (void)result_size;
    return SBGC_PY_MODULE_DISABLED;
#endif
}
