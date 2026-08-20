#include "sbgc_py_internal.h"

#include <string.h>

uint16_t sbgc_py_copy_last_tx (sbgc_py_device_t *device, uint8_t *buffer, uint16_t capacity)
{
    uint16_t size;

    if (device == NULL || buffer == NULL)
        return 0;
    size = device->last_tx_size > capacity ? capacity : device->last_tx_size;
    memcpy(buffer, device->last_tx, size);
    return size;
}


uint16_t sbgc_py_copy_last_rx (sbgc_py_device_t *device, uint8_t *buffer, uint16_t capacity)
{
    uint16_t size;

    if (device == NULL || buffer == NULL)
        return 0;
    size = device->last_rx_size > capacity ? capacity : device->last_rx_size;
    memcpy(buffer, device->last_rx, size);
    return size;
}
