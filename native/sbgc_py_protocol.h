#ifndef SBGC_PY_PROTOCOL_H
#define SBGC_PY_PROTOCOL_H

#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "adjunct.h"

#if defined(_WIN32)
    #if defined(SBGC_PYTHON_EXPORTS)
        #define SBGC_PY_PROTOCOL_API __declspec(dllexport)
    #else
        #define SBGC_PY_PROTOCOL_API __declspec(dllimport)
    #endif
#else
    #define SBGC_PY_PROTOCOL_API __attribute__((visibility("default")))
#endif


#define SBGC_PY_PROTOCOL_ABI_VERSION    1u
#define SBGC_PY_PROTOCOL_MAX_PAYLOAD    255u

#define SBGC_PY_PROTOCOL_V1_START       0x3EU
#define SBGC_PY_PROTOCOL_V2_START       0x24U

#define SBGC_PY_PROTOCOL_CRC16_POLYNOM  0x8005U

enum
{
    SBGC_PY_PROTOCOL_OK                     = 0,
    SBGC_PY_PROTOCOL_INVALID_ARGUMENT       = -1,
    SBGC_PY_PROTOCOL_UNSUPPORTED_VERSION    = -2,
    SBGC_PY_PROTOCOL_OUTPUT_TOO_SMALL       = -3

};


enum
{
    SBGC_PY_PROTOCOL_V1 = 1,
    SBGC_PY_PROTOCOL_V2 = 2

};


enum
{
    SBGC_PY_PARSER_SEARCH_START = 0,
    SBGC_PY_PARSER_HEADER,
    SBGC_PY_PARSER_PAYLOAD

};


#pragma pack(push, 1)

typedef struct
{
    ui8                         protocol_version,
                                command_id,
                                
                                payload_size,
                                payload [SBGC_PY_PROTOCOL_MAX_PAYLOAD];

}   sbgc_py_wire_frame_t;


typedef struct
{
    ui8                         protocol_version,
                                state,

                                header [3],
                                trailer [2],

                                payload [SBGC_PY_PROTOCOL_MAX_PAYLOAD];

    ui16                        buffered_size,
                                expected_size;

}   sbgc_py_protocol_parser_t;

#pragma pack(pop)


SBGC_PY_PROTOCOL_API void sbgc_py_protocol_parser_init (sbgc_py_protocol_parser_t *parser, ui8 protocol_version);

SBGC_PY_PROTOCOL_API void sbgc_py_protocol_reset_reading (sbgc_py_protocol_parser_t *parser);

SBGC_PY_PROTOCOL_API int sbgc_py_protocol_encode
(
    ui8 protocol_version, ui8 command_id, const ui8*payload, ui8 payload_size,
    ui8 *output, size_t output_capacity, size_t *output_size
);

SBGC_PY_PROTOCOL_API int sbgc_py_protocol_parser_feed
(
    sbgc_py_protocol_parser_t *parser, const ui8 *input, size_t input_size,
    size_t *consumed, sbgc_py_wire_frame_t *frame, ui8 *frame_ready
);

#endif
