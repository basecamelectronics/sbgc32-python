#include "sbgc_py_internal.h"

#include <stdlib.h>


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


void SerialAPI_CommandWaitingHandler (sbgcGeneral_t *gSBGC)
{
    (void)gSBGC;
}


sbgc_py_device_t *current_device;


int sbgc_py_transport_pop_debug_packet(
    void *context, uint16_t *time_ms, uint8_t *port_and_direction,
    uint8_t *command_id, uint8_t *payload, uint8_t *payload_size
)
{
    (void)context;
    (void)time_ms;
    (void)port_and_direction;
    (void)command_id;
    (void)payload;
    (void)payload_size;
    return 0;
}


void sbgc_py_transport_set_debug_capture_suppressed(void *context, int suppressed)
{
    (void)context;
    (void)suppressed;
}


static sbgcTicks_t sbgc_py_get_time_ms (void)
{
    if (current_device == NULL || current_device->get_time_ms == NULL)
        return 0;

    return (sbgcTicks_t)current_device->get_time_ms(current_device->context);
}


static ui8 sbgc_py_transmit (void *driver, ui8 *data, ui16 size)
{
    sbgc_py_device_t *device = (sbgc_py_device_t *)driver;

    if (device == NULL || !device->connected || device->transmit(device->context, data, size) != 0)
        return SBGC_DRV_TX_BUFF_OVERFLOW_FLAG;

    return SBGC_DRV_TX_OK_FLAG;
}


static ui8 sbgc_py_receive_byte (void *driver, ui8 *data)
{
    sbgc_py_device_t *device = (sbgc_py_device_t *)driver;

    if (device == NULL || !device->connected || device->receive_byte(device->context, data) != 0)
        return SBGC_DRV_RX_BUFF_EMPTY_FLAG;

    return SBGC_DRV_RX_BUSY_FLAG;
}


static ui16 sbgc_py_available_bytes (void *driver)
{
    sbgc_py_device_t *device = (sbgc_py_device_t *)driver;

    if (device == NULL || !device->connected)
        return SBGC_RX_BUFFER_OVERFLOW_FLAG;

    return device->available_bytes(device->context);
}


static sbgcCommandStatus_t sbgc_py_setup_device (sbgc_py_device_t *device)
{
    sbgcCommandStatus_t status;

    SerialAPI_LinkDriver(
        &device->serial_api,
        sbgc_py_transmit,
        sbgc_py_receive_byte,
        sbgc_py_available_bytes,
        NULL,
        sbgc_py_get_time_ms
    );
    device->serial_api._ll->drv = device;

    status = SBGC32_SetupLibrary(&device->serial_api);
    if (status == sbgcCOMMAND_OK)
        device->serial_api._ll->parserState = STATE_IDLE;

    return status;
}


SBGC_PY_API sbgc_py_device_t *sbgc_py_open
(
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
        available_bytes == NULL || get_time_ms == NULL || current_device != NULL)
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
    if (status != sbgcCOMMAND_OK)
    {
        SerialAPI_ResetLibrary(&device->serial_api);
        current_device = NULL;
        free(device);
        return NULL;
    }

    return device;
}


SBGC_PY_API sbgc_py_status_t sbgc_py_recover (sbgc_py_device_t *device)
{
    sbgcCommandStatus_t status;

    if (device == NULL)
        return SBGC_PY_INVALID_ARGUMENT;
    if (!device->connected)
        return SBGC_PY_NOT_CONNECTED;
    if (current_device != device)
        return SBGC_PY_ERROR;

    SerialAPI_ResetLibrary(&device->serial_api);
    status = sbgc_py_setup_device(device);

    return status == sbgcCOMMAND_OK ? SBGC_PY_OK : SBGC_PY_COMMUNICATION_ERROR;
}


SBGC_PY_API void sbgc_py_close (sbgc_py_device_t *device)
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

    free(device);
}
