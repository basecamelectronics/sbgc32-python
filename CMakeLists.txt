cmake_minimum_required(VERSION 3.21)

# Keep the CMake entry point at the repository root so Visual Studio discovers
# the project when this folder is opened.  The implementation remains in the
# native subdirectory and can still be configured directly if needed.
project(sbgc_python_protocol_workspace LANGUAGES C)

add_subdirectory(native)
