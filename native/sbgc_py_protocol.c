#include "sbgc_py_protocol.h"

// Static functions
static uint16_t sbgc_py_protocol_crc16 (const ui8 *data, size_t length)
{
    ui16 crc_register = 0;

    for (size_t index = 0; index < length; ++index)
    {
        for (ui8 shift_register = 1; shift_register > 0; shift_register <<= 1)
        {
            ui8 data_bit = (data[index] & shift_register) ? 1u : 0u;
            ui8 crc_bit = (uint8_t)(crc_register >> 15);

            crc_register <<= 1;

            if (data_bit != crc_bit)
                crc_register ^= SBGC_PY_PROTOCOL_CRC16_POLYNOM;
        }
    }

    return crc_register;
}


static ui8 sbgc_py_protocol_payload_checksum (const ui8 *payload, ui8 payload_size)
{
    ui8 checksum = 0;

    for (ui8 index = 0; index < payload_size; ++index)
        checksum = (ui8)(checksum + payload[index]);

    return checksum;
}


static int sbgc_py_protocol_is_valid_version (ui8 protocol_version)
{
    return protocol_version == SBGC_PY_PROTOCOL_V1 || protocol_version == SBGC_PY_PROTOCOL_V2;
}


static ui8 sbgc_py_protocol_start_byte (ui8 protocol_version)
{
    return protocol_version == SBGC_PY_PROTOCOL_V2
                            ? SBGC_PY_PROTOCOL_V2_START
                            : SBGC_PY_PROTOCOL_V1_START;
}


static ui8 sbgc_py_protocol_trailer_size (ui8 protocol_version)
{
    return protocol_version == SBGC_PY_PROTOCOL_V2 ? 2u : 1u;
}


// Protocol functions
void sbgc_py_protocol_parser_init (sbgc_py_protocol_parser_t *parser, ui8 protocol_version)
{
    if (parser == NULL)
        return;

    memset(parser, 0, sizeof(*parser));

    parser->protocol_version = protocol_version;
    parser->state = SBGC_PY_PARSER_SEARCH_START;
}


void sbgc_py_protocol_reset_reading (sbgc_py_protocol_parser_t *parser)
{
    if (parser == NULL)
        return;

    parser->state = SBGC_PY_PARSER_SEARCH_START;
    parser->buffered_size = 0;
    parser->expected_size = 0;
}


// Trancform command into bytes
int sbgc_py_protocol_encode
(
    ui8 protocol_version, ui8 command_id, const ui8* payload, ui8 payload_size,
    ui8 *output, size_t output_capacity, size_t* output_size
)
{
    const size_t trailer_size = sbgc_py_protocol_trailer_size(protocol_version);
    const size_t frame_size = 4u + (size_t)payload_size + trailer_size;

    if (output_size == NULL || output == NULL || (payload_size > 0u && payload == NULL))
        return SBGC_PY_PROTOCOL_INVALID_ARGUMENT;

    *output_size = 0;

    if (!sbgc_py_protocol_is_valid_version(protocol_version))
        return SBGC_PY_PROTOCOL_UNSUPPORTED_VERSION;

    if (output_capacity < frame_size)
        return SBGC_PY_PROTOCOL_OUTPUT_TOO_SMALL;

    output[0] = sbgc_py_protocol_start_byte(protocol_version);
    output[1] = command_id;
    output[2] = payload_size;
    output[3] = (uint8_t)(command_id + payload_size);

    if (payload_size > 0u)
        memcpy(&output[4], payload, payload_size);

    if (protocol_version == SBGC_PY_PROTOCOL_V1)
    {
        output[4u + payload_size] = sbgc_py_protocol_payload_checksum(payload, payload_size);
    }

    else
    {
        const uint16_t crc = sbgc_py_protocol_crc16(&output[1], (size_t)(3u + payload_size));
        output[4u + payload_size] = (uint8_t)(crc & 0x00FFu);
        output[5u + payload_size] = (uint8_t)(crc >> 8);
    }

    *output_size = frame_size;
    return SBGC_PY_PROTOCOL_OK;
}


int sbgc_py_protocol_parser_feed
(
    sbgc_py_protocol_parser_t* parser, const ui8* input, size_t input_size,
    size_t* consumed, sbgc_py_wire_frame_t* frame, ui8* frame_ready
)
{
    if (parser == NULL || consumed == NULL || frame == NULL || frame_ready == NULL || (input_size > 0u && input == NULL))
        return SBGC_PY_PROTOCOL_INVALID_ARGUMENT;

    if (!sbgc_py_protocol_is_valid_version(parser->protocol_version))
        return SBGC_PY_PROTOCOL_UNSUPPORTED_VERSION;

    *consumed = 0;
    *frame_ready = 0;

    for (size_t index = 0; index < input_size; index++)
    {
        const ui8 value = input[index];
        *consumed = index + 1u;

        if (parser->state == SBGC_PY_PARSER_SEARCH_START)
        {
            if (value == sbgc_py_protocol_start_byte(parser->protocol_version))
            {
                parser->state = SBGC_PY_PARSER_HEADER;
                parser->buffered_size = 0;
            }

            continue;
        }

        if (parser->state == SBGC_PY_PARSER_HEADER)
        {
            parser->header[parser->buffered_size++] = value;

            if (parser->buffered_size != sizeof(parser->header))
                continue;

            if (parser->header[0] == 0u || (ui8)(parser->header[0] + parser->header[1]) != parser->header[2])
            {
                sbgc_py_protocol_reset_reading(parser);
                continue;
            }

            parser->state = SBGC_PY_PARSER_PAYLOAD;
            parser->buffered_size = 0;
            parser->expected_size = (uint16_t)(parser->header[1] + sbgc_py_protocol_trailer_size(parser->protocol_version));

            continue;
        }

        if (parser->buffered_size < parser->header[1])
            parser->payload[parser->buffered_size] = value;

        else
            parser->trailer[parser->buffered_size - parser->header[1]] = value;

        parser->buffered_size++;

        if (parser->buffered_size != parser->expected_size)
            continue;

        int checksum_ok;

        if (parser->protocol_version == SBGC_PY_PROTOCOL_V1)
        {
            checksum_ok = parser->trailer[0] == sbgc_py_protocol_payload_checksum(parser->payload, parser->header[1]);
        }

        else
        {
            ui8 checksum_data [3u + SBGC_PY_PROTOCOL_MAX_PAYLOAD];

            memcpy(checksum_data, parser->header, sizeof(parser->header));
            memcpy(&checksum_data[sizeof(parser->header)], parser->payload, parser->header[1]);

            const ui16 crc = sbgc_py_protocol_crc16(checksum_data, sizeof(parser->header) + parser->header[1]);

            checksum_ok = parser->trailer[0] == (uint8_t)(crc & 0x00FFu) &&
                          parser->trailer[1] == (uint8_t)(crc >> 8);
        }

        if (!checksum_ok)
        {
            sbgc_py_protocol_reset_reading(parser);
            continue;
        }

        memset(frame, 0, sizeof(*frame));
        frame->protocol_version = parser->protocol_version;

        frame->command_id = parser->header[0];
        frame->payload_size = parser->header[1];
        memcpy(frame->payload, parser->payload, frame->payload_size);

        sbgc_py_protocol_reset_reading(parser);
        *frame_ready = 1;

        return SBGC_PY_PROTOCOL_OK;
    }

    return SBGC_PY_PROTOCOL_OK;
}
