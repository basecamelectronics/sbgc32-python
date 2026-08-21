#include "sbgc_py_internal.h"

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#ifdef _WIN32
    #pragma pack(push, 8)
    #define WIN32_LEAN_AND_MEAN
    #include <windows.h>
    #pragma pack(pop)
#endif


#if (SBGC_REALTIME_MODULE)
_Static_assert(
    sizeof(sbgc_py_realtime_data_t) == sizeof(sbgcRealTimeData_t),
    "sbgc_py_realtime_data_t must match sbgcRealTimeData_t"
);
#endif

#if (SBGC_CONTROL_MODULE)
_Static_assert(
    sizeof(sbgc_py_control_axis_config_t) == sizeof(sbgcAxisCCtrl_t),
    "sbgc_py_control_axis_config_t must match sbgcAxisCCtrl_t"
);
_Static_assert(
    sizeof(sbgc_py_control_config_t) == sizeof(sbgcControlConfig_t),
    "sbgc_py_control_config_t must match sbgcControlConfig_t"
);
#endif

#ifdef _WIN32
static void sbgc_native_com_wait_for_data (void);
#endif

void SerialAPI_CommandWaitingHandler (sbgcGeneral_t *gSBGC)
{
#ifdef _WIN32
    if (current_device != NULL)
    {
        sbgc_native_com_wait_for_data();
        if (gSBGC != NULL && gSBGC->_ll->drvAvailableBytes(gSBGC->_ll->drv) != 0)
            gSBGC->_ll->rx(gSBGC);
    }
#else
    (void)gSBGC;
#endif
}


sbgc_py_device_t *current_device;

/* This native build links SerialAPI directly to the Win32 COM callbacks. */
static sbgc_py_device_t *sbgc_native_open_device (void *context);

static sbgcTicks_t sbgc_py_get_time_ms (void)
{
#ifdef _WIN32
    return (sbgcTicks_t)GetTickCount64();
#else
    return (sbgcTicks_t)0;
#endif
}

/* Native work with serial COM on C */
#ifdef _WIN32
typedef struct
{
    HANDLE handle;
    HANDLE stop_event;
    HANDLE rx_ready_event;
    HANDLE reader_thread;
    CRITICAL_SECTION rx_lock;
    uint8_t rx_buffer[4096];
    uint16_t rx_start;
    uint16_t rx_size;
    int rx_overflow;
    int lock_initialized;
}   sbgc_py_com_t;

static sbgc_py_com_t *current_com;


static void sbgc_native_com_wait_for_data (void)
{
    if (current_com != NULL && current_com->rx_ready_event != NULL)
        WaitForSingleObject(current_com->rx_ready_event, INFINITE);
}


static void sbgc_native_com_append (sbgc_py_com_t *com, const uint8_t *data, DWORD size)
{
    uint16_t index, item;
    EnterCriticalSection(&com->rx_lock);

    if (size > (sizeof(com->rx_buffer) - com->rx_size))
    {
        com->rx_overflow = 1;
    }

    else
    {
        index = (uint16_t)((com->rx_start + com->rx_size) % sizeof(com->rx_buffer));

        for (item = 0; item < size; item++)
        {
            com->rx_buffer[index] = data[item];
            index = (uint16_t)((index + 1) % sizeof(com->rx_buffer));
        }

        com->rx_size = (uint16_t)(com->rx_size + size);
        SetEvent(com->rx_ready_event);
    }

    LeaveCriticalSection(&com->rx_lock);
}


static DWORD WINAPI sbgc_native_com_reader (LPVOID parameter)
{
    sbgc_py_com_t *com = (sbgc_py_com_t *)parameter;

    OVERLAPPED  wait_overlapped = { 0 },
                read_overlapped = { 0 };

    HANDLE waits [2];

    wait_overlapped.hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
    read_overlapped.hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);

    if (wait_overlapped.hEvent == NULL || read_overlapped.hEvent == NULL)
        goto done;

    waits[0] = com->stop_event; // Signal of ending flow
    waits[1] = wait_overlapped.hEvent; // Dsts arrival event

    while (WaitForSingleObject(com->stop_event, 0) != WAIT_OBJECT_0)
    {
        DWORD   events = 0,
                errors = 0,
                received = 0,
                count = 0;
        COMSTAT status;
        uint8_t temporary [256];

        ResetEvent(wait_overlapped.hEvent);

        /* Blocks the flow until data becomes available - event EV_RXCHAR */
        if (!WaitCommEvent(com->handle, &events, &wait_overlapped))
        {
            DWORD error = GetLastError();
            if (error != ERROR_IO_PENDING)
            {
                break;
            }

            if (WaitForMultipleObjects(2, waits, FALSE, INFINITE) == WAIT_OBJECT_0)
            {
                CancelIoEx(com->handle, &wait_overlapped);
                break;
            }

            if (!GetOverlappedResult(com->handle, &wait_overlapped, &received, FALSE))
            {
                continue;
            }
        }

        if (WaitForSingleObject(com->stop_event, 0) == WAIT_OBJECT_0)
            break;

        if (!ClearCommError(com->handle, &errors, &status))
        {
            break;
        }

        /* Checking the amount of data in the buffer */
        count = status.cbInQue < sizeof(temporary) ? status.cbInQue : sizeof(temporary);
        if (count == 0)
            continue;

        /* Reading 256 byte in temporary */
        ResetEvent(read_overlapped.hEvent);
        if (!ReadFile(com->handle, temporary, count, &received, &read_overlapped))
        {
            if (GetLastError() != ERROR_IO_PENDING || !GetOverlappedResult(com->handle, &read_overlapped, &received, TRUE))
            {
                break;
            }
        }

        if (received != 0)
        {
            sbgc_native_com_append(com, temporary, received);
        }
    }

done:
    if (wait_overlapped.hEvent != NULL) CloseHandle(wait_overlapped.hEvent);
    if (read_overlapped.hEvent != NULL) CloseHandle(read_overlapped.hEvent);
    return 0;
}


static int sbgc_native_com_start_reader (sbgc_py_com_t *com)
{
    com->stop_event = CreateEvent(NULL, TRUE, FALSE, NULL);
    com->rx_ready_event = CreateEvent(NULL, TRUE, FALSE, NULL);

    if (com->stop_event == NULL || com->rx_ready_event == NULL)
        return 0;

    com->reader_thread = CreateThread(NULL, 0, sbgc_native_com_reader, com, 0, NULL);

    return com->reader_thread != NULL;
}


static uint8_t sbgc_native_com_transmit (void *context, const uint8_t *data, uint16_t size)
{
    sbgc_py_com_t *com = (sbgc_py_com_t *)context;
    OVERLAPPED write_overlapped = { 0 };
    DWORD written = 0;
    int result = 1;

    if (com == NULL || data == NULL || com->handle == INVALID_HANDLE_VALUE)
        return 1;

    write_overlapped.hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
    if (write_overlapped.hEvent == NULL)
        return 1;

    if (WriteFile(com->handle, data, size, &written, &write_overlapped) || GetLastError() == ERROR_IO_PENDING)

        if (GetOverlappedResult(com->handle, &write_overlapped, &written, TRUE))
            result = (written == size ? 0 : 1);

    CloseHandle(write_overlapped.hEvent);

    return (uint8_t)result;
}


static uint8_t sbgc_native_com_receive_byte (void *context, uint8_t *data)
{
    sbgc_py_com_t *com = (sbgc_py_com_t *)context;

    if (com == NULL || data == NULL || com->handle == INVALID_HANDLE_VALUE)
        return 1;

    EnterCriticalSection(&com->rx_lock);

    if (com->rx_size == 0)
    {
        ResetEvent(com->rx_ready_event);
        LeaveCriticalSection(&com->rx_lock);
        return 1;
    }

    *data = com->rx_buffer[com->rx_start];
    com->rx_start = (uint16_t)((com->rx_start + 1) % sizeof(com->rx_buffer));
    com->rx_size--;

    if (com->rx_size == 0)
        ResetEvent(com->rx_ready_event);

    LeaveCriticalSection(&com->rx_lock);

    return 0;
}


static uint16_t sbgc_native_com_available_bytes (void *context)
{
    sbgc_py_com_t *com = (sbgc_py_com_t *)context;

    if (com == NULL || com->handle == INVALID_HANDLE_VALUE)
        return 0;

    EnterCriticalSection(&com->rx_lock);

    uint16_t size = com->rx_overflow ? SBGC_RX_BUFFER_OVERFLOW_FLAG : com->rx_size;
    LeaveCriticalSection(&com->rx_lock);

    return size;
}


static void sbgc_native_com_close (void *context)
{
    sbgc_py_com_t *com = (sbgc_py_com_t *)context;

    if (com == NULL)
        return;

    if (com->stop_event != NULL)
        SetEvent(com->stop_event);

    if (current_com == com)
        current_com = NULL;

    if (com->handle != INVALID_HANDLE_VALUE)
        CancelIoEx(com->handle, NULL);

    if (com->reader_thread != NULL)
    {
        WaitForSingleObject(com->reader_thread, INFINITE);
        CloseHandle(com->reader_thread);
    }

    if (com->stop_event != NULL) CloseHandle(com->stop_event);
    if (com->rx_ready_event != NULL) CloseHandle(com->rx_ready_event);
    if (com->handle != INVALID_HANDLE_VALUE) CloseHandle(com->handle);
    if (com->lock_initialized) DeleteCriticalSection(&com->rx_lock);

    free(com);
}


static void sbgc_native_com_recover (void *context)
{
    sbgc_py_com_t *com = (sbgc_py_com_t *)context;

    if (com != NULL && com->handle != INVALID_HANDLE_VALUE)
    {
        PurgeComm(com->handle, PURGE_RXABORT | PURGE_RXCLEAR | PURGE_TXABORT | PURGE_TXCLEAR);
        EnterCriticalSection(&com->rx_lock);

        com->rx_start = 0; com->rx_size = 0; com->rx_overflow = 0;

        ResetEvent(com->rx_ready_event);
        LeaveCriticalSection(&com->rx_lock);
    }
}
#endif


SBGC_PY_API sbgc_py_device_t *sbgc_py_open_com (const char *port, uint32_t baudrate)
{
#ifdef _WIN32
    char port_path [32];
    sbgc_py_com_t *com;
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

    com->handle = INVALID_HANDLE_VALUE;
    InitializeCriticalSection(&com->rx_lock);
    com->lock_initialized = 1;

    com->handle = CreateFile(port_path, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING,
                             FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OVERLAPPED, NULL);
                             
    if (com->handle == INVALID_HANDLE_VALUE)
    {
        sbgc_native_com_close(com);
        return NULL;
    }

    /* Configuring settings */
    DCB settings = { 0 };
    settings.DCBlength = sizeof(settings);

    if (!GetCommState(com->handle, &settings))
    {
        sbgc_native_com_close(com);
        return NULL;
    }

    settings.BaudRate = baudrate;
    settings.ByteSize = 8;
    settings.Parity = NOPARITY;
    settings.StopBits = ONESTOPBIT;
    settings.fBinary = TRUE;
    settings.fParity = FALSE;

    if (!SetCommState(com->handle, &settings))
    {
        sbgc_native_com_close(com);
        return NULL;
    }

    if (!SetCommTimeouts(com->handle, &timeouts))
    {
        sbgc_native_com_close(com);
        return NULL;
    }

    if (!SetCommMask(com->handle, EV_RXCHAR | EV_ERR))
    {
        sbgc_native_com_close(com);
        return NULL;
    }

    SetupComm(com->handle, 4096, 4096);
    PurgeComm(com->handle, PURGE_RXABORT | PURGE_RXCLEAR | PURGE_TXABORT | PURGE_TXCLEAR);

    if (!sbgc_native_com_start_reader(com))
    {
        sbgc_native_com_close(com);
        return NULL;
    }

    current_com = com;

    device = sbgc_native_open_device(com);

    if (device == NULL)
    {
        current_com = NULL;
        sbgc_native_com_close(com);
        return NULL;
    }

    device->close_context = sbgc_native_com_close;
    device->recover_context = sbgc_native_com_recover;

    return device;
#else
    (void)port;
    (void)baudrate;
    return NULL;
#endif
}


static ui8 sbgc_native_transmit (void *driver, ui8 *data, ui16 size)
{
    sbgc_py_device_t *device = (sbgc_py_device_t *)driver;

    if (device == NULL || !device->connected || sbgc_native_com_transmit(device->context, data, size) != 0)
        return SBGC_DRV_TX_BUFF_OVERFLOW_FLAG;

    return SBGC_DRV_TX_OK_FLAG;
}


static ui8 sbgc_native_receive_byte (void *driver, ui8 *data)
{
    sbgc_py_device_t *device = (sbgc_py_device_t *)driver;

    if (device == NULL || !device->connected || sbgc_native_com_receive_byte(device->context, data) != 0)
        return SBGC_DRV_RX_BUFF_EMPTY_FLAG;

    return SBGC_DRV_RX_BUSY_FLAG;
}


static ui16 sbgc_native_available_bytes (void *driver)
{
    sbgc_py_device_t *device = (sbgc_py_device_t *)driver;
    if (device == NULL || !device->connected)
        return SBGC_RX_BUFFER_OVERFLOW_FLAG;

    return sbgc_native_com_available_bytes(device->context);
}


static sbgcCommandStatus_t sbgc_py_setup_device (sbgc_py_device_t *device)
{
    sbgcCommandStatus_t status;

    SerialAPI_LinkDriver(&device->serial_api, sbgc_native_transmit, sbgc_native_receive_byte,
                         sbgc_native_available_bytes, NULL, sbgc_py_get_time_ms);

    device->serial_api._ll->drv = device;

    status = SBGC32_SetupLibrary(&device->serial_api);
    if (status == sbgcCOMMAND_OK)
        device->serial_api._ll->parserState = STATE_IDLE;

    return status;
}



static sbgc_py_device_t *sbgc_native_open_device (void *context)
{
    sbgc_py_device_t *device;
    sbgcCommandStatus_t status;

    if (context == NULL)
        return NULL;

    if (current_device != NULL)
        return NULL;

    device = (sbgc_py_device_t *)calloc(1, sizeof(*device));
    if (device == NULL)
        return NULL;

    device->context = context;
    device->connected = 1;
    current_device = device;

    status = sbgc_py_setup_device(device);

    if (status != sbgcCOMMAND_OK)
    {
        SerialAPI_ResetLibrary(&device->serial_api);
        current_device = NULL;
        free(device);
        return NULL;
    }

    return device;
}


sbgc_py_status_t sbgc_py_recover (sbgc_py_device_t *device)
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

    if (device->connected)
    {
        device->connected = 0;
        SerialAPI_ResetLibrary(&device->serial_api);
    }

    if (current_device == device)
        current_device = NULL;

    if (device->close_context != NULL)
        device->close_context(device->context);

    free(device);
}
