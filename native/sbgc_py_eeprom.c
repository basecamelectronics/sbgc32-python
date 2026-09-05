#include "sbgc_py_internal.h"

#include <string.h>


static sbgc_py_status_t sbgc_py_validate_eeprom_device (sbgc_py_device_t *device)
{
    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;

    if (current_device != device)
        return SBGC_PY_ERROR;

    return SBGC_PY_OK;
}


static sbgc_py_status_t sbgc_py_eeprom_status (sbgcCommandStatus_t status, sbgc_py_device_t *device)
{
    return status == sbgcCOMMAND_OK && device->serial_api._lastSerialCommandStatus == serialAPI_TX_RX_OK
        ? SBGC_PY_OK : SBGC_PY_COMMUNICATION_ERROR;
}


sbgc_py_status_t sbgc_py_read_i2c_reg
(
    sbgc_py_device_t *device, ui8 device_addr, ui8 register_addr,
    ui8 size, ui8 *result
)
{
#if (SBGC_EEPROM_MODULE)
    sbgcI2C_RegBuff_t request = { 0 };
    sbgc_py_status_t device_status = sbgc_py_validate_eeprom_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (result == NULL || size == 0 || size > SBGC_EEPROM_MAX_BUFF_DATA_LEN)
        return SBGC_PY_INVALID_ARGUMENT;

    request.deviceAddr = device_addr;
    request.regAddr = register_addr;
    request.dataLen = size;

    sbgcCommandStatus_t status = SBGC32_ReadRegBuffI2C(&device->serial_api, &request);
    if (sbgc_py_eeprom_status(status, device) != SBGC_PY_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    memcpy(result, request.data, size);
    return SBGC_PY_OK;
#else
    (void)device;
    (void)device_addr;
    (void)register_addr;
    (void)size;
    (void)result;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_write_i2c_reg
(
    sbgc_py_device_t *device, ui8 device_addr, ui8 register_addr,
    const ui8 *data, ui8 size, ui8 need_confirmation,
    sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_EEPROM_MODULE)
    sbgcI2C_RegBuff_t request = { 0 };
    sbgc_py_status_t device_status = sbgc_py_validate_eeprom_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (data == NULL || size == 0 || size > SBGC_EEPROM_MAX_BUFF_DATA_LEN ||
        (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

    request.deviceAddr = device_addr;
    request.regAddr = register_addr;
    request.dataLen = size;
    memcpy(request.data, data, size);

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        sbgcCommandStatus_t status = SBGC32_WriteRegBuffI2C(&device->serial_api, &request, &native_confirmation);
        if (sbgc_py_eeprom_status(status, device) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    return sbgc_py_eeprom_status(SBGC32_WriteRegBuffI2C(&device->serial_api, &request, SBGC_NO_CONFIRM), device);
#else
    (void)device;
    (void)device_addr;
    (void)register_addr;
    (void)data;
    (void)size;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_eeprom
(
    sbgc_py_device_t *device, ui32 address, ui16 size, ui8 *result
)
{
#if (SBGC_EEPROM_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_eeprom_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (result == NULL || address > SBGC_EEPROM_MAX_REQ_ADDR || address % SBGC_EEPROM_ALIGN_DATA_LEN ||
        size < SBGC_EEPROM_ALIGN_DATA_LEN || size > SBGC_MAX_SER_BUFF_SIZE - SBGC_EEPROM_ALIGN_DATA_LEN ||
        address + size > SBGC_EEPROM_MAX_REQ_ADDR + 1)
        return SBGC_PY_INVALID_ARGUMENT;

    return sbgc_py_eeprom_status(
        SBGC32_ReadEEPROM(&device->serial_api, address, (i8 *)result, size), device
    );
#else
    (void)device;
    (void)address;
    (void)size;
    (void)result;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_write_eeprom
(
    sbgc_py_device_t *device, ui32 address, const ui8 *data, ui16 size,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_EEPROM_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_eeprom_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (data == NULL || address > SBGC_EEPROM_MAX_REQ_ADDR || address % SBGC_EEPROM_ALIGN_DATA_LEN ||
        size < SBGC_EEPROM_ALIGN_DATA_LEN || size > SBGC_MAX_SER_BUFF_SIZE - SBGC_EEPROM_ALIGN_DATA_LEN ||
        address + size > SBGC_EEPROM_MAX_REQ_ADDR + 1 || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        sbgcCommandStatus_t status = SBGC32_WriteEEPROM(
            &device->serial_api, address, (const i8 *)data, size, &native_confirmation
        );
        if (sbgc_py_eeprom_status(status, device) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    return sbgc_py_eeprom_status(
        SBGC32_WriteEEPROM(&device->serial_api, address, (const i8 *)data, size, SBGC_NO_CONFIRM), device
    );
#else
    (void)device;
    (void)address;
    (void)data;
    (void)size;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_external_data (sbgc_py_device_t *device, ui8 *result)
{
#if (SBGC_EEPROM_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_eeprom_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (result == NULL)
        return SBGC_PY_INVALID_ARGUMENT;

    return sbgc_py_eeprom_status(SBGC32_ReadExternalData(&device->serial_api, (i8 *)result), device);
#else
    (void)device;
    (void)result;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_write_external_data
(
    sbgc_py_device_t *device, const ui8 *data, ui8 need_confirmation,
    sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_EEPROM_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_eeprom_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (data == NULL || (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        sbgcCommandStatus_t status = SBGC32_WriteExternalData(&device->serial_api, (const i8 *)data, &native_confirmation);
        if (sbgc_py_eeprom_status(status, device) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    return sbgc_py_eeprom_status(SBGC32_WriteExternalData(&device->serial_api, (const i8 *)data, SBGC_NO_CONFIRM), device);
#else
    (void)device;
    (void)data;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_file
(
    sbgc_py_device_t *device, ui16 file_id, ui16 page_offset, ui16 max_size,
    ui8 *data, ui16 *file_size, ui16 *result_page_offset, ui8 *error_code
)
{
#if (SBGC_EEPROM_MODULE)
    sbgcWriteReadFile_t file = { 0 };
    sbgc_py_status_t device_status = sbgc_py_validate_eeprom_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (data == NULL || file_size == NULL || result_page_offset == NULL || error_code == NULL ||
        max_size == 0 || max_size > SBGC_EEPROM_MAX_BUFF_DATA_LEN)
        return SBGC_PY_INVALID_ARGUMENT;

    file.fileID = file_id;
    file.pageOffset = page_offset;
    file.maxSize = max_size;

    sbgcCommandStatus_t status = SBGC32_ReadFile(&device->serial_api, &file);
    if (sbgc_py_eeprom_status(status, device) != SBGC_PY_OK)
        return SBGC_PY_COMMUNICATION_ERROR;
    if (file.fileSize > max_size || file.fileSize > SBGC_EEPROM_MAX_BUFF_DATA_LEN)
        return SBGC_PY_COMMUNICATION_ERROR;

    memcpy(data, file.data, file.fileSize);
    *file_size = file.fileSize;
    *result_page_offset = file.pageOffset;
    *error_code = file.errCode;
    return SBGC_PY_OK;
#else
    (void)device;
    (void)file_id;
    (void)page_offset;
    (void)max_size;
    (void)data;
    (void)file_size;
    (void)result_page_offset;
    (void)error_code;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_write_file
(
    sbgc_py_device_t *device, ui16 file_id, ui16 page_offset,
    const ui8 *data, ui16 size, ui8 need_confirmation,
    sbgc_py_confirmation_t *confirmation
)
{
#if (SBGC_EEPROM_MODULE)
    sbgcWriteReadFile_t file = { 0 };
    sbgc_py_status_t device_status = sbgc_py_validate_eeprom_device(device);

    if (device_status != SBGC_PY_OK)
        return device_status;
    if (data == NULL || size == 0 || size > SBGC_EEPROM_MAX_BUFF_DATA_LEN ||
        (need_confirmation && confirmation == NULL))
        return SBGC_PY_INVALID_ARGUMENT;

    file.fileID = file_id;
    file.fileSize = size;
    file.pageOffset = page_offset;
    memcpy(file.data, data, size);

#if (SBGC_NEED_CONFIRM_CMD)
    if (need_confirmation)
    {
        sbgcConfirm_t native_confirmation = { 0 };
        sbgcCommandStatus_t status = SBGC32_WriteFile(&device->serial_api, &file, &native_confirmation);
        if (sbgc_py_eeprom_status(status, device) != SBGC_PY_OK)
            return SBGC_PY_COMMUNICATION_ERROR;
        sbgc_py_copy_confirmation(confirmation, &native_confirmation);
        return SBGC_PY_OK;
    }
#else
    if (need_confirmation)
        return SBGC_PY_CONFIRMATION_DISABLED;
#endif

    return sbgc_py_eeprom_status(SBGC32_WriteFile(&device->serial_api, &file, SBGC_NO_CONFIRM), device);
#else
    (void)device;
    (void)file_id;
    (void)page_offset;
    (void)data;
    (void)size;
    (void)need_confirmation;
    (void)confirmation;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_clear_file_system (sbgc_py_device_t *device)
{
#if (SBGC_EEPROM_MODULE)
    sbgc_py_status_t device_status = sbgc_py_validate_eeprom_device(device);
    if (device_status != SBGC_PY_OK)
        return device_status;
    return sbgc_py_eeprom_status(SBGC32_ClearFileSystem(&device->serial_api), device);
#else
    (void)device;
    return SBGC_PY_MODULE_DISABLED;
#endif
}
