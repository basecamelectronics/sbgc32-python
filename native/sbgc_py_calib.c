#include "sbgc_py_internal.h"

#include <string.h>

static sbgc_py_status_t sbgc_py_validate_calib_device (sbgc_py_device_t* device)
{
    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    return SBGC_PY_OK;
}


static sbgc_py_status_t sbgc_py_calib_status (sbgc_py_device_t *device, sbgcCommandStatus_t status)
{
    return status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK
                    ? SBGC_PY_OK 
                    : SBGC_PY_COMMUNICATION_ERROR;
}


static sbgc_py_status_t sbgc_py_calib_confirm
(
    sbgc_py_device_t *device, sbgcCommandStatus_t status, sbgcConfirm_t *confirm,
    sbgc_py_confirmation_t *confirmation
)
{
    sbgc_py_status_t result = sbgc_py_calib_status(device, status);

    if (result == SBGC_PY_OK && confirmation != NULL)
        sbgc_py_copy_confirmation(confirmation, confirm);

    return result;
}


sbgc_py_status_t sbgc_py_calib_acc (sbgc_py_device_t *device)
{
#if (SBGC_CALIB_MODULE)
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    return result == SBGC_PY_OK ? sbgc_py_calib_status(device, SBGC32_CalibAcc(&device->serial_api)) : result;
#else
    (void)device; 
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_gyro (sbgc_py_device_t *device)
{
#if (SBGC_CALIB_MODULE)
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    return result == SBGC_PY_OK ? sbgc_py_calib_status(device, SBGC32_CalibGyro(&device->serial_api)) : result;
#else
    (void)device; 
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_mag (sbgc_py_device_t *device)
{
#if (SBGC_CALIB_MODULE)
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    return result == SBGC_PY_OK ? sbgc_py_calib_status(device, SBGC32_CalibMag(&device->serial_api)) : result;
#else
    (void)device; 
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_request_calib_info (sbgc_py_device_t *device, sbgcCalibInfo_t *calib_info, ui8 imu_type)
{
#if (SBGC_CALIB_MODULE)
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    if (result != SBGC_PY_OK) return result;

    if (calib_info == NULL || imu_type < sbgcIMU_TYPE_MAIN || imu_type > sbgcIMU_TYPE_FRAME) 
        return SBGC_PY_INVALID_ARGUMENT;

    return sbgc_py_calib_status(device, SBGC32_RequestCalibInfo(&device->serial_api, calib_info, (sbgcIMU_Type_t)imu_type));
#else
    (void)device; 
    (void)calib_info;
    (void)imu_type; 
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_acc_ext (sbgc_py_device_t *device, sbgcIMU_ExtCalib_t *data, ui8 need_confirmation, sbgc_py_confirmation_t *confirmation)
{
#if (SBGC_CALIB_MODULE && SBGC_NEED_CONFIRM_CMD)
    sbgcConfirm_t confirm = { 0 }; sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    if (result != SBGC_PY_OK || data == NULL) 
        return result != SBGC_PY_OK ? result : SBGC_PY_INVALID_ARGUMENT;

    return sbgc_py_calib_confirm(device, SBGC32_CalibAccExt(&device->serial_api, data, need_confirmation ? &confirm : NULL), &confirm, confirmation);
#elif (SBGC_CALIB_MODULE)
    (void)device;
    (void)data; 
    (void)need_confirmation; 
    (void)confirmation; 
    return SBGC_PY_CONFIRMATION_DISABLED;
#else
    (void)device;
    (void)data; 
    (void)need_confirmation; 
    (void)confirmation; 
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_gyro_ext (sbgc_py_device_t *device, sbgcIMU_ExtCalib_t *data, ui8 need_confirmation, sbgc_py_confirmation_t *confirmation)
{
#if (SBGC_CALIB_MODULE && SBGC_NEED_CONFIRM_CMD)
    sbgcConfirm_t confirm = { 0 }; sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    if (result != SBGC_PY_OK || data == NULL) 
        return result != SBGC_PY_OK ? result : SBGC_PY_INVALID_ARGUMENT;

    return sbgc_py_calib_confirm(device, SBGC32_CalibGyroExt(&device->serial_api, data, need_confirmation ? &confirm : NULL), &confirm, confirmation);
#elif (SBGC_CALIB_MODULE)
    (void)device; 
    (void)data; 
    (void)need_confirmation; 
    (void)confirmation; 
    return SBGC_PY_CONFIRMATION_DISABLED;
#else
    (void)device;
    (void)data;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_mag_ext (sbgc_py_device_t *device, sbgcIMU_ExtCalib_t *data, ui8 need_confirmation, sbgc_py_confirmation_t *confirmation)
{
#if (SBGC_CALIB_MODULE && SBGC_NEED_CONFIRM_CMD)
    sbgcConfirm_t confirm = { 0 }; sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    if (result != SBGC_PY_OK || data == NULL) 
        return result != SBGC_PY_OK ? result : SBGC_PY_INVALID_ARGUMENT;

    return sbgc_py_calib_confirm(device, SBGC32_CalibMagExt(&device->serial_api, data, need_confirmation ? &confirm : NULL), &confirm, confirmation);
#elif (SBGC_CALIB_MODULE)
    (void)device; 
    (void)data; 
    (void)need_confirmation; 
    (void)confirmation; 
    return SBGC_PY_CONFIRMATION_DISABLED;
#else
    (void)device;
    (void)data;
    (void)need_confirmation;
    (void)confirmation; 
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_encoders_offset (sbgc_py_device_t *device, sbgcCalibParameter_t motor)
{
#if (SBGC_CALIB_MODULE)
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    return result == SBGC_PY_OK ? sbgc_py_calib_status(device, SBGC32_CalibEncodersOffset(&device->serial_api, motor)) : result;
#else
    (void)device; 
    (void)motor;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_encoders_fld_offset (sbgc_py_device_t *device)
{
#if (SBGC_CALIB_MODULE)
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    return result == SBGC_PY_OK ? sbgc_py_calib_status(device, SBGC32_CalibEncodersFldOffset(&device->serial_api)) : result;
#else
    (void)device; 
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_encoders_fld_offset_ext (sbgc_py_device_t *device, const sbgcCalibEncodersOffset_t *data)
{
#if (SBGC_CALIB_MODULE)
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    if (result != SBGC_PY_OK || data == NULL) 
        return result != SBGC_PY_OK ? result : SBGC_PY_INVALID_ARGUMENT;

    return sbgc_py_calib_status(device, SBGC32_CalibEncodersFldOffsetExt(&device->serial_api, data));
#else
    (void)device; 
    (void)data; 
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_poles (sbgc_py_device_t *device)
{
#if (SBGC_CALIB_MODULE)
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    return result == SBGC_PY_OK ? sbgc_py_calib_status(device, SBGC32_CalibPoles(&device->serial_api)) : result;
#else
    (void)device; 
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_offset (sbgc_py_device_t *device)
{
#if (SBGC_CALIB_MODULE)
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    return result == SBGC_PY_OK ? sbgc_py_calib_status(device, SBGC32_CalibOffset(&device->serial_api)) : result;
#else
    (void)device; 
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_bat (sbgc_py_device_t *device, ui16 voltage, ui8 need_confirmation, sbgc_py_confirmation_t *confirmation)
{
#if (SBGC_CALIB_MODULE && SBGC_NEED_CONFIRM_CMD)
    sbgcConfirm_t confirm = { 0 }; 
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    if (result != SBGC_PY_OK)
        return result;

    return sbgc_py_calib_confirm(device, SBGC32_CalibBat(&device->serial_api, voltage, need_confirmation ? &confirm : NULL), &confirm, confirmation);
#elif (SBGC_CALIB_MODULE)
    (void)device; 
    (void)voltage;
    (void)need_confirmation;
    (void)confirmation; 
    return SBGC_PY_CONFIRMATION_DISABLED;
#else
    (void)device;
    (void)voltage;
    (void)need_confirmation;
    (void)confirmation; 
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_orient_corr (sbgc_py_device_t *device, ui8 need_confirmation, sbgc_py_confirmation_t *confirmation)
{
#if (SBGC_CALIB_MODULE && SBGC_NEED_CONFIRM_CMD)
    sbgcConfirm_t confirm = { 0 }; 
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    if (result != SBGC_PY_OK) 
        return result;
    return sbgc_py_calib_confirm(device, SBGC32_CalibOrientCorr(&device->serial_api, need_confirmation ? &confirm : NULL), &confirm, confirmation);
#elif (SBGC_CALIB_MODULE)
    (void)device; 
    (void)need_confirmation;
    (void)confirmation; 
    return SBGC_PY_CONFIRMATION_DISABLED;
#else
    (void)device;
    (void)need_confirmation;
    (void)confirmation; 
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_acc_ext_ref (sbgc_py_device_t *device, const i16 acc_ref[3], ui8 need_confirmation, sbgc_py_confirmation_t *confirmation)
{
#if (SBGC_CALIB_MODULE && SBGC_NEED_CONFIRM_CMD)
    sbgcConfirm_t confirm = { 0 }; 
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    if (result != SBGC_PY_OK || acc_ref == NULL) 
        return result != SBGC_PY_OK ? result : SBGC_PY_INVALID_ARGUMENT;

    return sbgc_py_calib_confirm(device, SBGC32_CalibAccExtRef(&device->serial_api, acc_ref, need_confirmation ? &confirm : NULL), &confirm, confirmation);
#elif (SBGC_CALIB_MODULE)
    (void)device; 
    (void)acc_ref; 
    (void)need_confirmation; 
    (void)confirmation;
    return SBGC_PY_CONFIRMATION_DISABLED;
#else
    (void)device;
    (void)acc_ref;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_calib_cogging (sbgc_py_device_t* device, const ui8* data, ui8 size, ui8 need_confirmation, sbgc_py_confirmation_t* confirmation)
{
#if (SBGC_CALIB_MODULE && SBGC_NEED_CONFIRM_CMD)
    sbgcCalibCogging_t cogging = { 0 };
    sbgcConfirm_t confirm = { 0 };
    sbgc_py_status_t result = sbgc_py_validate_calib_device(device);

    if (result != SBGC_PY_OK || data == NULL || size != sizeof(cogging))
        return result != SBGC_PY_OK ? result : SBGC_PY_INVALID_ARGUMENT;

    memcpy(&cogging, data, sizeof(cogging));

    return sbgc_py_calib_confirm(device, SBGC32_CalibCogging(&device->serial_api, &cogging, need_confirmation ? &confirm : NULL), &confirm, confirmation);
#elif (SBGC_CALIB_MODULE)
    (void)device;
    (void)data;
    (void)size;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_CONFIRMATION_DISABLED;
#else
    (void)device;
    (void)data;
    (void)size;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}
