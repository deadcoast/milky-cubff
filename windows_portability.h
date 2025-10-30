// Windows portability header for CuBFF
// This file should be included in common.h to make the code Windows-compatible

#ifndef WINDOWS_PORTABILITY_H
#define WINDOWS_PORTABILITY_H

#ifdef _WIN32
    // Windows-specific includes
    #include <io.h>
    #include <direct.h>
    
    // Define Unix compatibility macros
    #define getpid _getpid
    #define mkdir(name, mode) _mkdir(name)
    #define access _access
    
    // strerror_r compatibility for Windows
    #include <string>
    #include <errno.h>
    
    inline char* strerror_r(int errnum, char* buf, size_t buflen) {
        #ifdef _MSC_VER
            strerror_s(buf, buflen, errnum);
            return buf;
        #else
            char* result = strerror(errnum);
            strncpy(buf, result, buflen);
            buf[buflen - 1] = '\0';
            return buf;
        #endif
    }
    
    // Constructor attribute compatibility (GCC-specific)
    #ifndef __GNUC__
        #define __attribute__(x)
    #endif
    
    // pkg-config alternative: define paths manually or use vcpkg
    // The Makefile.windows should handle this
    
#else
    // Unix/Linux - include standard headers
    #include <sys/stat.h>
    #include <sys/types.h>
    #include <unistd.h>
#endif

#endif // WINDOWS_PORTABILITY_H

