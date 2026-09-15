if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    cmake_minimum_required(VERSION 3.21)
    project(sbgc_python_protocol LANGUAGES C)
endif()

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# This target deliberately does not build the SerialAPI request scheduler.
# Python owns request queues, correlation, deadlines and callbacks. The
# vendor tree remains available as the source of the framing/CRC/parser logic
# that will be exposed through this narrow protocol adapter.
add_library(sbgc_python_protocol SHARED
    sbgc_py_protocol.c
)

file(GLOB_RECURSE SBGC_PY_VENDOR_C_SOURCES CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/../vendor/*.c"
)

# The protocol DLL is intentionally narrow, so vendor object files are not
# linked into it.  Compile them in a separate object target nevertheless: this
# supplies Visual Studio IntelliSense with the same C11/include context for
# every vendor source and makes a broken vendor C file fail a DLL build.
add_library(sbgc_python_vendor_sources OBJECT ${SBGC_PY_VENDOR_C_SOURCES})
add_dependencies(sbgc_python_protocol sbgc_python_vendor_sources)

target_include_directories(sbgc_python_protocol PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../vendor/serialAPI"
)

target_include_directories(sbgc_python_vendor_sources PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../vendor/serialAPI"
)

target_compile_definitions(sbgc_python_protocol PRIVATE
    SBGC_PYTHON_EXPORTS
)

target_compile_definitions(sbgc_python_vendor_sources PRIVATE
    SBGC_EXTERNAL_WAIT_HANDLER
)

if(MSVC)
    # The protocol structures exchanged through the ABI must have fixed layout.
    # Treat every compiler diagnostic from the bridge itself as a build failure.
    target_compile_options(sbgc_python_protocol PRIVATE /Zp1 /W4 /WX)
    target_compile_options(sbgc_python_vendor_sources PRIVATE /Zp1)
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
