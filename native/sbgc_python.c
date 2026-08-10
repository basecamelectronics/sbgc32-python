#include "sbgc_python.h"

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#ifdef _WIN32
    #pragma pack(push, 8)
    #define WIN32_LEAN_AND_MEAN
    #include <windows.h>
    #pragma pack(pop)
#endif
#include "sbgc32.h"

#if (SBGC_REALTIME_MODULE)
_Static_assert(
    sizeof(sbgc_py_realtime_data_t) == sizeof(sbgcRealTimeData_t),
    "sbgc_py_realtime_data_t must match sbgcRealTimeData_t"
);
#endif

/* Yield to the USB-UART driver while Serial API waits for the next packet byte.
   Without this, the synchronous Serial API loop can consume a full CPU core and
   intermittently miss responses from USB serial adapters. */
void SerialAPI_CommandWaitingHandler(sbgcGeneral_t *gSBGC)
{
    (void)gSBGC;
#ifdef _WIN32
    Sleep(1);
#endif
}

struct sbgc_py_device {
    void *context;
    sbgc_py_tx_callback_t transmit;
    sbgc_py_rx_callback_t receive_byte;
    sbgc_py_available_callback_t available_bytes;
    sbgc_py_time_callback_t get_time_ms;
    sbgcGeneral_t serial_api;
    void (*close_context)(void *context);
    void (*recover_context)(void *context);
    uint8_t last_tx[64];
    uint16_t last_tx_size;
    uint8_t last_rx[256];
    uint16_t last_rx_size;
    int connected;
};

/* The initial bridge runs one synchronous Serial API call at a time. */
static sbgc_py_device_t *current_device;

static sbgcTicks_t sbgc_py_get_time_ms (void)
{
    /* Serial API timeout calculations require elapsed wall-clock time, not CPU time. */
#ifdef _WIN32
    return (sbgcTicks_t)GetTickCount64();
#else
    return (sbgcTicks_t)0;
#endif
}

#ifdef _WIN32
typedef struct {
    HANDLE handle;
} sbgc_py_com_t;

static uint8_t sbgc_py_com_transmit(void *context, const uint8_t *data, uint16_t size)
{
    sbgc_py_com_t *com = (sbgc_py_com_t *)context;
    DWORD written = 0;

    if (com == NULL || com->handle == INVALID_HANDLE_VALUE ||
        !WriteFile(com->handle, data, size, &written, NULL) || written != size)
        return 1;

    return 0;
}

static uint8_t sbgc_py_com_receive_byte(void *context, uint8_t *data)
{
    sbgc_py_com_t *com = (sbgc_py_com_t *)context;
    DWORD received = 0;

    if (com == NULL || com->handle == INVALID_HANDLE_VALUE ||
        !ReadFile(com->handle, data, 1, &received, NULL) || received != 1)
        return 1;

    return 0;
}

static uint16_t sbgc_py_com_available_bytes(void *context)
{
    sbgc_py_com_t *com = (sbgc_py_com_t *)context;

    COMSTAT status;
    DWORD errors;

    if (com == NULL || com->handle == INVALID_HANDLE_VALUE ||
        !ClearCommError(com->handle, &errors, &status))
        return 0;

    return (uint16_t)(status.cbInQue > UINT16_MAX ? UINT16_MAX : status.cbInQue);
}

static uint32_t sbgc_py_com_time_callback(void *context)
{
    (void)context;
    return (uint32_t)sbgc_py_get_time_ms();
}

static void sbgc_py_com_close(void *context)
{
    sbgc_py_com_t *com = (sbgc_py_com_t *)context;

    if (com == NULL)
        return;
    if (com->handle != INVALID_HANDLE_VALUE)
        CloseHandle(com->handle);
    free(com);
}

static void sbgc_py_com_recover(void *context)
{
    sbgc_py_com_t *com = (sbgc_py_com_t *)context;

    if (com != NULL && com->handle != INVALID_HANDLE_VALUE)
        PurgeComm(com->handle, PURGE_RXABORT | PURGE_RXCLEAR | PURGE_TXABORT | PURGE_TXCLEAR);
}
#endif

static ui8 sbgc_py_transmit (void *driver, ui8 *data, ui16 size)
{
    sbgc_py_device_t *device = (sbgc_py_device_t *)driver;

    if (device == NULL || !device->connected || device->transmit(device->context, data, size) != 0)
        return SBGC_DRV_TX_BUFF_OVERFLOW_FLAG;

    device->last_tx_size = size > sizeof(device->last_tx) ? sizeof(device->last_tx) : size;
    memcpy(device->last_tx, data, device->last_tx_size);

    return SBGC_DRV_TX_OK_FLAG;
}

static ui8 sbgc_py_receive_byte( void *driver, ui8 *data)
{
    sbgc_py_device_t *device = (sbgc_py_device_t *)driver;

    if (device == NULL || !device->connected || device->receive_byte(device->context, data) != 0)
        return SBGC_DRV_RX_BUFF_EMPTY_FLAG;

    if (device->last_rx_size < sizeof(device->last_rx))
        device->last_rx[device->last_rx_size++] = *data;

    return SBGC_DRV_RX_BUSY_FLAG;
}

static ui16 sbgc_py_available_bytes (void *driver)
{
    sbgc_py_device_t *device = (sbgc_py_device_t *)driver;

    if (device == NULL || !device->connected)
        return SBGC_RX_BUFFER_OVERFLOW_FLAG;

    return device->available_bytes(device->context);
}

static sbgcCommandStatus_t sbgc_py_setup_device(sbgc_py_device_t *device)
{
    sbgcCommandStatus_t status;

    SerialAPI_LinkDriver(&device->serial_api, sbgc_py_transmit, sbgc_py_receive_byte,
                         sbgc_py_available_bytes, NULL, sbgc_py_get_time_ms);
    device->serial_api._ll->drv = device;
    status = SBGC32_SetupLibrary(&device->serial_api);
    return status;
}

sbgc_py_device_t *sbgc_py_open(
    void *context,
    sbgc_py_tx_callback_t transmit,
    sbgc_py_rx_callback_t receive_byte,
    sbgc_py_available_callback_t available_bytes,
    sbgc_py_time_callback_t get_time_ms
)
{
    sbgc_py_device_t *device;
    sbgcCommandStatus_t status;

    if (context == NULL || transmit == NULL || receive_byte == NULL ||
        available_bytes == NULL || get_time_ms == NULL)
        return NULL;
    if (current_device != NULL)
        return NULL;

    device = (sbgc_py_device_t *)calloc(1, sizeof(*device));
    if (device == NULL)
        return NULL;

    device->context = context;
    device->transmit = transmit;
    device->receive_byte = receive_byte;
    device->available_bytes = available_bytes;
    device->get_time_ms = get_time_ms;
    device->connected = 1;
    current_device = device;

    status = sbgc_py_setup_device(device);

    if (status != sbgcCOMMAND_OK) {
        SerialAPI_ResetLibrary(&device->serial_api);
        current_device = NULL;
        free(device);
        return NULL;
    }

    return device;
}

sbgc_py_status_t sbgc_py_recover(sbgc_py_device_t *device)
{
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    if (device->recover_context != NULL)
        device->recover_context(device->context);

    SerialAPI_ResetLibrary(&device->serial_api);
    status = sbgc_py_setup_device(device);
    return status == sbgcCOMMAND_OK ? SBGC_PY_OK : SBGC_PY_COMMUNICATION_ERROR;
}

void sbgc_py_close (sbgc_py_device_t *device)
{
    if (device == NULL)
        return;

    if (device->connected) {
        device->connected = 0;
        SerialAPI_ResetLibrary(&device->serial_api);
    }
    if (current_device == device)
        current_device = NULL;

    if (device->close_context != NULL)
        device->close_context(device->context);

    free(device);
}


sbgc_py_device_t *sbgc_py_open_com (const char *port, uint32_t baudrate)
{
#ifdef _WIN32
    char port_path[32];
    sbgc_py_com_t *com;
    DCB settings = { 0 };
    COMMTIMEOUTS timeouts = { 0 };
    sbgc_py_device_t *device;

    if (port == NULL || port[0] == '\0' || baudrate == 0)
        return NULL;

    if (strncmp(port, "\\\\.\\", 4) == 0)
        snprintf(port_path, sizeof(port_path), "%s", port);
    else
        snprintf(port_path, sizeof(port_path), "\\\\.\\%s", port);

    com = (sbgc_py_com_t *)calloc(1, sizeof(*com));
    if (com == NULL)
        return NULL;

    com->handle = CreateFileA(port_path, GENERIC_READ | GENERIC_WRITE, 0, NULL,
                               OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (com->handle == INVALID_HANDLE_VALUE) {
        free(com);
        return NULL;
    }
    settings.DCBlength = sizeof(settings);
    if (!GetCommState(com->handle, &settings)) {
        sbgc_py_com_close(com);
        return NULL;
    }
    settings.BaudRate = baudrate;
    settings.ByteSize = 8;
    settings.Parity = NOPARITY;
    settings.StopBits = ONESTOPBIT;
    settings.fBinary = TRUE;
    settings.fParity = FALSE;

    /* SimpleBGC uses only RX/TX; do not drive optional modem-control lines. */
    settings.fDtrControl = DTR_CONTROL_DISABLE;
    settings.fRtsControl = RTS_CONTROL_DISABLE;
    settings.fOutxCtsFlow = FALSE;
    settings.fOutxDsrFlow = FALSE;
    settings.fDsrSensitivity = FALSE;
    settings.fOutX = FALSE;
    settings.fInX = FALSE;
    settings.fErrorChar = FALSE;
    settings.fNull = FALSE;
    settings.fTXContinueOnXoff = TRUE;
    settings.fAbortOnError = FALSE;

    if (!SetCommState(com->handle, &settings))
    {
        sbgc_py_com_close(com);
        return NULL;
    }

    timeouts.ReadIntervalTimeout = MAXDWORD;
    timeouts.ReadTotalTimeoutMultiplier = 0;
    timeouts.ReadTotalTimeoutConstant = 0;
    timeouts.WriteTotalTimeoutMultiplier = 0;
    timeouts.WriteTotalTimeoutConstant = 1000;
    if (!SetCommTimeouts(com->handle, &timeouts))
    {
        sbgc_py_com_close(com);
        return NULL;
    }

    SetupComm(com->handle, 4096, 4096);
    PurgeComm(com->handle, PURGE_RXABORT | PURGE_RXCLEAR | PURGE_TXABORT | PURGE_TXCLEAR);

    device = sbgc_py_open(com, sbgc_py_com_transmit, sbgc_py_com_receive_byte,
                          sbgc_py_com_available_bytes, sbgc_py_com_time_callback);

    if (device == NULL)
    {
        sbgc_py_com_close(com);
        return NULL;
    }

    device->close_context = sbgc_py_com_close;
    device->recover_context = sbgc_py_com_recover;
    return device;
#else
    (void)port;
    (void)baudrate;
    return NULL;
#endif
}


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

    device->last_tx_size = 0;
    device->last_rx_size = 0;

    status = SBGC32_GetAngles(&device->serial_api, &native_angles);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    for (axis = ROLL; axis <= YAW; axis++) {
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

    device->last_tx_size = 0;
    device->last_rx_size = 0;

    status = SBGC32_GetAnglesExt(&device->serial_api, &native_angles_ext);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    for (axis = ROLL; axis <= YAW; axis++)
    {
        angles->axis_gae[axis].imu_angle = native_angles_ext.AxisGAE[axis].IMU_Angle;
        angles->axis_gae[axis].target_angle = native_angles_ext.AxisGAE[axis].targetAngle;
        angles->axis_gae[axis].frame_cam_angle = native_angles_ext.AxisGAE[axis].frameCamAngle;
        memcpy(angles->axis_gae[axis].reserved, native_angles_ext.AxisGAE[axis].reserved,
               sizeof(angles->axis_gae[axis].reserved));
    }

    return SBGC_PY_OK;
#else
    (void)device;
    (void)angles;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_get_board_info (sbgc_py_device_t *device, sbgc_py_board_info_t *board_info)
{
#if (SBGC_SERVICE_MODULE)
	sbgcBoardInfo_t native_board_info = { 0 };
	sbgcCommandStatus_t status;

    if (device == NULL || board_info == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    device->last_tx_size = 0;
    device->last_rx_size = 0;

    /* Send only CMD_BOARD_INFO. SBGC32_GetBoardData also sends CMD_BOARD_INFO_3,
       which is unavailable on some older controller firmware. */
    status = SBGC32_ReadBoardInfo(&device->serial_api, &native_board_info, 0);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK ||
        native_board_info.boardVer == 0 || native_board_info.firmwareVer == 0)
        return SBGC_PY_COMMUNICATION_ERROR;

    board_info->board_ver = native_board_info.boardVer;
    board_info->firmware_ver = native_board_info.firmwareVer;
    board_info->state_flags = native_board_info.stateFlags;
    board_info->board_features = native_board_info.boardFeatures;
    board_info->connection_flag = native_board_info.connectionFlag;
    board_info->firmware_extra_id = native_board_info.frwExtraID;
    board_info->board_features_ext = native_board_info.boardFeaturesExt;
    board_info->main_imu_sensor_model = native_board_info.mainIMU_SensModel;
    board_info->frame_imu_sensor_model = native_board_info.frameIMU_SensModel;
    board_info->build_number = native_board_info.buildNumber;
    board_info->base_firmware_ver = native_board_info.baseFrwVer;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)board_info;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_get_board_info_3 (sbgc_py_device_t *device, sbgc_py_board_info_3_t *board_info)
{
#if (SBGC_SERVICE_MODULE)
    sbgcBoardInfo3_t native_board_info = {0};
    sbgcCommandStatus_t status;

    if (device == NULL || board_info == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    device->last_tx_size = 0;
    device->last_rx_size = 0;

    status = SBGC32_ReadBoardInfo3(&device->serial_api, &native_board_info);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    memcpy(board_info->device_id, native_board_info.deviceID, 9);
    memcpy(board_info->mcu_id, native_board_info.MCU_ID, 12);
    board_info->eeprom_size = native_board_info.EEPROM_Size;

    board_info->script_slot_1_size = native_board_info.scriptSlot1_Size;
    board_info->script_slot_2_size = native_board_info.scriptSlot2_Size;
    board_info->script_slot_3_size = native_board_info.scriptSlot3_Size;
    board_info->script_slot_4_size = native_board_info.scriptSlot4_Size;
    board_info->script_slot_5_size = native_board_info.scriptSlot5_Size;

    board_info->profile_set_slots = native_board_info.profileSetSlots;
    board_info->profile_set_current = native_board_info.profileSetCur;
    board_info->flash_size = native_board_info.flashSize;
    memcpy(board_info->imu_calib_info, native_board_info.IMU_CalibInfo, 2);

    board_info->script_slot_6_size = native_board_info.scriptSlot6_Size;
    board_info->script_slot_7_size = native_board_info.scriptSlot7_Size;
    board_info->script_slot_8_size = native_board_info.scriptSlot8_Size;
    board_info->script_slot_9_size = native_board_info.scriptSlot9_Size;
    board_info->script_slot_10_size = native_board_info.scriptSlot10_Size;

    board_info->hardware_flags = native_board_info.hwFlags;
    board_info->board_features_ext2 = native_board_info.boardFeaturesExt2;
    board_info->can_driver_main_limit = native_board_info.CAN_DrvMainLimit;
    board_info->can_driver_aux_limit = native_board_info.CAN_DrvAuxLimit;
    board_info->adjustable_variables_total = native_board_info.adjVarsTotalNum;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)board_info;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_reset (sbgc_py_device_t *device, uint8_t flags, uint16_t delay_ms)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    device->last_tx_size = 0;
    device->last_rx_size = 0;
    status = SBGC32_Reset(&device->serial_api, flags, delay_ms);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)flags;
    (void)delay_ms;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_expect_reset (sbgc_py_device_t *device)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    status = SBGC32_ExpectCommand(&device->serial_api, CMD_RESET, NULL, 0);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_motors_on (sbgc_py_device_t *device)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    device->last_tx_size = 0;
    device->last_rx_size = 0;
    status = SBGC32_SetMotorsON(&device->serial_api, SBGC_NO_CONFIRM);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_motors_off (sbgc_py_device_t *device, uint8_t mode)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;
    if (mode > MOTOR_MODE_SAFE_STOP)
        return SBGC_PY_INVALID_ARGUMENT;

    device->last_tx_size = 0;
    device->last_rx_size = 0;
    status = SBGC32_SetMotorsOFF(
        &device->serial_api, (sbgcMotorsMode_t)mode, SBGC_NO_CONFIRM
    );
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)mode;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_run_script (sbgc_py_device_t *device, uint8_t mode, uint8_t slot)
{
#if (SBGC_SERVICE_MODULE)
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;
    /* CMD_RUN_SCRIPT reserves one byte for the slot. Newer firmware supports
       slots 6..10 even though this SerialAPI revision names only slots 1..5. */
    if (mode > ScrtM_START_WITH_DEBUG || slot > 9)
        return SBGC_PY_INVALID_ARGUMENT;

    device->last_tx_size = 0;
    device->last_rx_size = 0;
    status = SBGC32_RunScript(&device->serial_api, (sbgcScriptMode_t)mode, (sbgcScriptSlotNum_t)slot);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    return SBGC_PY_OK;
#else
    (void)device;
    (void)mode;
    (void)slot;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


sbgc_py_status_t sbgc_py_read_script_debug_info (
    sbgc_py_device_t *device, sbgc_py_script_debug_info_t *script_debug_info
)
{
#if (SBGC_SERVICE_MODULE)
    sbgcScriptDebugInfo_t native_script_debug_info = { 0 };
    sbgcCommandStatus_t status;

    if (device == NULL || script_debug_info == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    status = SBGC32_ReadScriptDebugInfo(&device->serial_api, &native_script_debug_info);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
        return SBGC_PY_COMMUNICATION_ERROR;

    script_debug_info->current_command_counter = native_script_debug_info.curComCounter;
    script_debug_info->error_code = native_script_debug_info.errorCode;
    return SBGC_PY_OK;
#else
    (void)device;
    (void)script_debug_info;
    return SBGC_PY_MODULE_DISABLED;
#endif
}


static sbgc_py_status_t sbgc_py_get_realtime_data (
    sbgc_py_device_t *device,
    sbgc_py_realtime_data_t *realtime_data,
    sbgcBoolean_t extended
)
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

    device->last_tx_size = 0;
    device->last_rx_size = 0;
    status = extended ? SBGC32_ReadRealTimeData4(&device->serial_api, &native_realtime_data)
                      : SBGC32_ReadRealTimeData3(&device->serial_api, &native_realtime_data);
    if (status != sbgcCOMMAND_OK ||
        device->serial_api._lastSerialCommandStatus != serialAPI_TX_RX_OK)
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


sbgc_py_status_t sbgc_py_get_realtime_data_3 (
    sbgc_py_device_t *device, sbgc_py_realtime_data_t *realtime_data
)
{
    return sbgc_py_get_realtime_data(device, realtime_data, sbgcOFF);
}


sbgc_py_status_t sbgc_py_get_realtime_data_4 (
    sbgc_py_device_t *device, sbgc_py_realtime_data_t *realtime_data
)
{
    return sbgc_py_get_realtime_data(device, realtime_data, sbgcON);
}


uint16_t sbgc_py_copy_last_tx (sbgc_py_device_t *device, uint8_t *buffer, uint16_t capacity)
{
    uint16_t size;

    if (device == NULL || buffer == NULL)
        return 0;
    size = device->last_tx_size > capacity ? capacity : device->last_tx_size;
    memcpy(buffer, device->last_tx, size);
    return size;
}


uint16_t sbgc_py_copy_last_rx(sbgc_py_device_t *device, uint8_t *buffer, uint16_t capacity)
{
    uint16_t size;

    if (device == NULL || buffer == NULL)
        return 0;
    size = device->last_rx_size > capacity ? capacity : device->last_rx_size;
    memcpy(buffer, device->last_rx, size);
    return size;
}
