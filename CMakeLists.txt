cmake_minimum_required(VERSION 3.15)
project(cubff CXX CUDA)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable CUDA if available (optional)
if(NOT DEFINED USE_CUDA)
    set(USE_CUDA ON CACHE BOOL "Enable CUDA support")
endif()

# Find required packages
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(BROTLI REQUIRED libbrotlienc libbrotlicommon)
else()
    # Fallback for Windows without pkg-config
    find_library(BROTLIENC_LIB brotlienc)
    find_library(BROTLIDEC_LIB brotlidec)
    find_library(BROTLICOMMON_LIB brotlicommon)
    find_path(BROTLI_INCLUDE_DIRS brotli/encode.h)
endif()

# Add include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR})
if(PkgConfig_FOUND)
    include_directories(${BROTLI_INCLUDE_DIRS})
endif()

# Windows-specific configuration
if(WIN32)
    # Disable CUDA on Windows by default unless explicitly enabled
    if(NOT USE_CUDA_FORCED)
        set(USE_CUDA OFF)
        message(STATUS "CUDA disabled on Windows (use -DUSE_CUDA=ON to enable)")
    endif()
    
    # Add Windows compatibility defines
    add_definitions(-D_WIN32_WINNT=0x0601)
endif()

# Language source files
file(GLOB LANGUAGE_FILES "*.cu")

# Common sources
set(COMMON_SOURCES
    main.cc
    common.cc
)

# Choose compiler based on CUDA availability
if(USE_CUDA AND NOT WIN32)
    enable_language(CUDA)
    
    # Add CUDA language files
    foreach(LANG_FILE ${LANGUAGE_FILES})
        get_filename_component(LANG_NAME ${LANG_FILE} NAME_WE)
        add_library(${LANG_NAME} OBJECT ${LANG_FILE})
        set_target_properties(${LANG_NAME} PROPERTIES
            POSITION_INDEPENDENT_CODE ON
            CUDA_SEPARABLE_COMPILATION ON
        )
    endforeach()
    
    get_target_property(CUDA_ARCH CUDA_COMPUTE_ARCHITECTURES "")
    if(NOT CUDA_ARCH)
        set(CUDA_ARCH "sm_75")
    endif()
    
else()
    # CPU-only build - compile .cu files as C++
    foreach(LANG_FILE ${LANGUAGE_FILES})
        get_filename_component(LANG_NAME ${LANG_FILE} NAME_WE)
        add_library(${LANG_NAME} OBJECT ${LANG_FILE})
        set_target_properties(${LANG_NAME} PROPERTIES
            POSITION_INDEPENDENT_CODE ON
            LANGUAGE CXX
        )
    endforeach()
endif()

# Get object files from languages
foreach(LANG_FILE ${LANGUAGE_FILES})
    get_filename_component(LANG_NAME ${LANG_FILE} NAME_WE)
    list(APPEND LANGUAGE_OBJECTS $<TARGET_OBJECTS:${LANG_NAME}>)
endforeach()

# Main executable
add_executable(main ${COMMON_SOURCES} ${LANGUAGE_OBJECTS})

# Link libraries
if(PkgConfig_FOUND)
    target_link_libraries(main ${BROTLI_LIBRARIES})
else()
    if(WIN32)
        # Windows specific libraries
        target_link_libraries(main 
            ${BROTLIENC_LIB}
            ${BROTLIDEC_LIB}
            ${BROTLICOMMON_LIB}
        )
    else()
        # Try to find libraries manually
        target_link_libraries(main brotlienc brotlidec brotlicommon)
    endif()
endif()

# OpenMP for parallel processing
find_package(OpenMP)
if(OpenMP_CXX_FOUND)
    target_link_libraries(main OpenMP::OpenMP_CXX)
endif()

# Set output directory
set_target_properties(main PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Install target
install(TARGETS main DESTINATION bin)

