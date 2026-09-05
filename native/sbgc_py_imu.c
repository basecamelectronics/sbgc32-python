#include "sbgc_py_internal.h"

#include <string.h>


static sbgc_py_status_t sbgc_py_validate_imu_device (sbgc_py_device_t *device)
{
    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    return SBGC_PY_OK;
}


static sbgc_py_status_t sbgc_py_require_ext_imu (sbgc_py_device_t *device)
{
    sbgcBoardInfo_t board_info = { 0 };

    sbgcCommandStatus_t status = SBGC32_ReadBoardInfo(&device->serial_api, &board_info, 0);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return board_info.boardFeatures & BF_EXT_IMU ? SBGC_PY_OK : SBGC_PY_IMU_NOT_SUPPORTED;
}


sbgc_py_status_t sbgc_py_request_ext_imu_debug (sbgc_py_device_t *device, ui8 *result, ui8 size)
{
#if (SBGC_IMU_MODULE)
    sbgcExtIMU_DebugInfo_t debug_info = { 0 };
    sbgc_py_status_t device_status = sbgc_py_validate_imu_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (result == NULL || size != sizeof(debug_info))
        return SBGC_PY_INVALID_ARGUMENT;

    device_status = sbgc_py_require_ext_imu(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    sbgcCommandStatus_t status = SBGC32_RequestExtIMU_DebugInfo(&device->serial_api, &debug_info);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    memcpy(result, &debug_info, sizeof(debug_info));

    return SBGC_PY_OK;
#else
    (void)device;
    (void)result;
    (void)size;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_send_ext_imu_command
(
    sbgc_py_device_t *device, ui8 *command_id, ui8 *payload,
    ui8 payload_size, ui8 command_type
)
{
#if (SBGC_IMU_MODULE)
    sbgcExtIMU_Command_t command;
    sbgc_py_status_t device_status = sbgc_py_validate_imu_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (command_id == NULL || payload == NULL || command_type > EXT_IMU_CMD_TYPE_TX_RX)
        return SBGC_PY_INVALID_ARGUMENT;

    device_status = sbgc_py_require_ext_imu(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    command.commandID = (sbgcExtIMU_CommandID_t)*command_id;
    command.payloadSize = payload_size;
    command.payload = payload;

    sbgcCommandStatus_t status = SBGC32_SendCmdToExtIMU(&device->serial_api, &command, (sbgcExtIMU_CommandType_t)command_type);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    *command_id = (ui8)command.commandID;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)command_id;
    (void)payload;
    (void)payload_size;
    (void)command_type;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_send_ext_sens_command
(
    sbgc_py_device_t *device, ui8 *command_id, ui8 *payload,
    ui8 payload_size, ui8 flags, ui8 command_type
)
{
#if (SBGC_IMU_MODULE)
    sbgcExtIMU_Command_t command;
    sbgc_py_status_t device_status = sbgc_py_validate_imu_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (command_id == NULL || payload == NULL || flags & ~EXT_SENS_CMD_HIGH_PRIOR || command_type > EXT_IMU_CMD_TYPE_TX_RX)
        return SBGC_PY_INVALID_ARGUMENT;

    device_status = sbgc_py_require_ext_imu(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    command.commandID = (sbgcExtIMU_CommandID_t)*command_id;
    command.payloadSize = payload_size;
    command.payload = payload;

    sbgcCommandStatus_t status = SBGC32_SendCmdToExtSens(&device->serial_api, &command, (sbgcExtSensCommandFlag_t)flags, (sbgcExtIMU_CommandType_t)command_type);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    *command_id = (ui8)command.commandID;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)command_id;
    (void)payload;
    (void)payload_size;
    (void)flags;
    (void)command_type;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_correction_gyro (sbgc_py_device_t *device, ui8 imu_type, const i16 *zero_correction, i16 zero_heading_correction)
{
#if (SBGC_IMU_MODULE)
    sbgcGyroCorrection_t correction = { 0 };
    sbgc_py_status_t device_status = sbgc_py_validate_imu_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (zero_correction == NULL || imu_type > 1)
        return SBGC_PY_INVALID_ARGUMENT;

    correction.IMU_Type = imu_type;
    memcpy(correction.gyroZeroCorr, zero_correction, sizeof(correction.gyroZeroCorr));
    correction.gyroZeroHeadingCorr = zero_heading_correction;

    sbgcCommandStatus_t status = SBGC32_CorrectionGyro(&device->serial_api, &correction);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)imu_type;
    (void)zero_correction;
    (void)zero_heading_correction;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_call_ahrs_helper (sbgc_py_device_t *device, ui8 *helper, ui8 size, ui16 mode)
{
#if (SBGC_IMU_MODULE)
    sbgcAHRS_Helper_t ahrs_helper = { 0 };
    sbgc_py_status_t device_status = sbgc_py_validate_imu_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (helper == NULL || size != sizeof(ahrs_helper))
        return SBGC_PY_INVALID_ARGUMENT;

    memcpy(&ahrs_helper, helper, sizeof(ahrs_helper));

    sbgcCommandStatus_t status = SBGC32_CallAHRS_Helper(&device->serial_api, &ahrs_helper, mode);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    memcpy(helper, &ahrs_helper, sizeof(ahrs_helper));

    return SBGC_PY_OK;
#else
    (void)device;
    (void)helper;
    (void)size;
    (void)mode;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_provide_helper_data (sbgc_py_device_t *device, const ui8 *helper_data, ui8 size)
{
#if (SBGC_IMU_MODULE)
    sbgcHelperData_t data = { 0 };
    sbgc_py_status_t device_status = sbgc_py_validate_imu_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (helper_data == NULL || size != sizeof(data))
        return SBGC_PY_INVALID_ARGUMENT;

    memcpy(&data, helper_data, sizeof(data));

    sbgcCommandStatus_t status = SBGC32_ProvideHelperData(&device->serial_api, &data);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)helper_data;
    (void)size;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_provide_helper_data_ext (sbgc_py_device_t *device, const ui8 *helper_data, ui8 size)
{
#if (SBGC_IMU_MODULE)
    sbgcHelperDataExt_t data = { 0 };
    sbgc_py_status_t device_status = sbgc_py_validate_imu_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;

    if (helper_data == NULL || size != sizeof(data))
        return SBGC_PY_INVALID_ARGUMENT;

    memcpy(&data, helper_data, sizeof(data));

    sbgcCommandStatus_t status = SBGC32_ProvideHelperDataExt(&device->serial_api, &data);

    if (status != sbgcCOMMAND_OK || device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)helper_data;
    (void)size;
    return SBGC_PY_MODULE_DISABLED;
#endif
}
