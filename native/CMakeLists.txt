if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    cmake_minimum_required(VERSION 3.21)
    project(sbgc_python_protocol LANGUAGES C)
endif()

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# This target contains only the framing/CRC/parser adapter and its local headers.
# Python owns request queues, correlation, deadlines and callbacks.
add_library(sbgc_python_protocol SHARED
    sbgc_py_protocol.c
    sbgc_py_protocol.h
    adjunct.h
)

target_include_directories(sbgc_python_protocol PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
)

target_compile_definitions(sbgc_python_protocol PRIVATE
    SBGC_PYTHON_EXPORTS
)

if(MSVC)
    # The protocol structures exchanged through the ABI must have fixed layout.
    # Treat every compiler diagnostic from the bridge itself as a build failure.
    target_compile_options(sbgc_python_protocol PRIVATE /Zp1 /W4 /WX)
endif()

set_target_properties(sbgc_python_protocol PROPERTIES
    OUTPUT_NAME "sbgc_python_protocol"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
    LIBRARY_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/../src/sbgc32/_native"
)

install(TARGETS sbgc_python_protocol
    RUNTIME DESTINATION sbgc32/_native
    LIBRARY DESTINATION sbgc32/_native
    ARCHIVE DESTINATION sbgc32/_native
)
