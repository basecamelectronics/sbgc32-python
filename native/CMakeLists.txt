cmake_minimum_required(VERSION 3.21)

project(sbgc_python LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

set(SERIAL_API_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../vendor/serialAPI")

set(SBGC_PY_SERIAL_API_SOURCES
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

function(add_sbgc_python_library target transport_source output_name)
    add_library(${target} SHARED ${transport_source} ${SBGC_PY_SERIAL_API_SOURCES})

    target_include_directories(${target} PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}"
        "${SERIAL_API_DIR}"
    )
    target_compile_definitions(${target} PRIVATE
        SBGC_PYTHON_EXPORTS
        SBGC_EXTERNAL_WAIT_HANDLER
    )
    if(MSVC)
        # Serial API declares wire-format structures with PACKED__.
        target_compile_options(${target} PRIVATE /Zp1)
    endif()

    set_target_properties(${target} PROPERTIES
        OUTPUT_NAME "${output_name}"
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        RUNTIME_OUTPUT_DIRECTORY_RELWITHDEBINFO "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        RUNTIME_OUTPUT_DIRECTORY_MINSIZEREL "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        LIBRARY_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        LIBRARY_OUTPUT_DIRECTORY_RELWITHDEBINFO "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        LIBRARY_OUTPUT_DIRECTORY_MINSIZEREL "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        ARCHIVE_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        ARCHIVE_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        ARCHIVE_OUTPUT_DIRECTORY_RELWITHDEBINFO "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
        ARCHIVE_OUTPUT_DIRECTORY_MINSIZEREL "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
    )
endfunction()

set(SBGC_PY_INSTALL_TARGETS sbgc_python_pyserial)
add_sbgc_python_library(sbgc_python_pyserial sbgc_py_transport_pyserial.c sbgc_python_pyserial)

if(WIN32)
    add_sbgc_python_library(sbgc_python sbgc_py_transport_win32.c sbgc_python)
    list(APPEND SBGC_PY_INSTALL_TARGETS sbgc_python)
endif()

install(TARGETS ${SBGC_PY_INSTALL_TARGETS}
    RUNTIME DESTINATION sbgc32/_native
    LIBRARY DESTINATION sbgc32/_native
    ARCHIVE DESTINATION sbgc32/_native
)
