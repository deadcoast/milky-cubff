// Windows-compatible version of common.h
// This provides Windows-specific compatibility layer

#ifndef COMMON_WINDOWS_H
#define COMMON_WINDOWS_H

// Include the standard common.h first
#include "common.h"

// Windows-specific overrides and compatibility
#ifdef _WIN32
    #ifndef __GNUC__
        // MSVC compatibility
        #pragma comment(lib, "brotlienc.lib")
        #pragma comment(lib, "brotlidec.lib")
        #ifdef _OPENMP
            #pragma comment(lib, "libiomp5md.lib")
        #endif
    #endif
#endif

#endif // COMMON_WINDOWS_H

