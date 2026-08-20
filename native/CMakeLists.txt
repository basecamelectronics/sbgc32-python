cmake_minimum_required(VERSION 3.21)

project(sbgc_python LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

set(SERIAL_API_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../vendor/serialAPI")

add_library(sbgc_python SHARED
    sbgc_py_common.c
    sbgc_py_transport.c
    sbgc_py_control.c
    sbgc_py_adjvars.c
    sbgc_py_realtime.c
    sbgc_py_service.c
    "${SERIAL_API_DIR}/sbgc32.c"
    "${SERIAL_API_DIR}/core/commandBuild.c"
    "${SERIAL_API_DIR}/core/lowLayer.c"
    "${SERIAL_API_DIR}/core/debug/debug.c"
    "${SERIAL_API_DIR}/core/highLayer/highLayer.c"
    "${SERIAL_API_DIR}/core/parser/parser.c"
    "${SERIAL_API_DIR}/modules/gimbalControl/gimbalControl.c"
    "${SERIAL_API_DIR}/modules/adjvar/adjvar.c"
    "${SERIAL_API_DIR}/modules/realtime/realtime.c"
    "${SERIAL_API_DIR}/modules/service/service.c"
)

target_include_directories(sbgc_python PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${SERIAL_API_DIR}"
)

target_compile_definitions(sbgc_python PRIVATE
    SBGC_PYTHON_EXPORTS
    SBGC_EXTERNAL_WAIT_HANDLER
)

if(MSVC)
    # Serial API declares wire-format structures with PACKED__.
    target_compile_options(sbgc_python PRIVATE /Zp1)
endif()

set_target_properties(sbgc_python PROPERTIES
    OUTPUT_NAME "sbgc_python"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
    RUNTIME_OUTPUT_DIRECTORY_RELWITHDEBINFO "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
    RUNTIME_OUTPUT_DIRECTORY_MINSIZEREL "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
)

install(TARGETS sbgc_python
    RUNTIME DESTINATION sbgc32/_native
    LIBRARY DESTINATION sbgc32/_native
    ARCHIVE DESTINATION sbgc32/_native
)
