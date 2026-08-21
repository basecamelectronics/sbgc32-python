#include "sbgc_py_internal.h"

#include <string.h>

sbgc_py_status_t sbgc_py_get_angles (sbgc_py_device_t *device, sbgc_py_angles_t *angles)
{
#if (SBGC_REALTIME_MODULE)
    sbgcGetAngles_t native_angles = { 0 };
    sbgcCommandStatus_t status;
    ui8 axis;

    if (device == NULL || angles == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    status = SBGC32_GetAngles(&device->serial_api, &native_angles);

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
    sbgcCommandStatus_t status;
    ui8 axis;

    if (device == NULL || angles == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    status = SBGC32_GetAnglesExt(&device->serial_api, &native_angles_ext);

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
    sbgcCommandStatus_t status;

    if (device == NULL || realtime_data == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    status = extended
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
    sbgcCommandStatus_t status;

    if (device == NULL || result == NULL || payload_size < 2)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    memset(result, 0, (size_t)payload_size + 4);
    memcpy(result, &flags, sizeof(flags));

    status = SBGC32_RequestRealTimeDataCustom(&device->serial_api, result, payload_size);

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
