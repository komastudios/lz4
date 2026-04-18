cmake_minimum_required(VERSION 3.21)

project(lz4 LANGUAGES C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED True)

set(CMAKE_POSITION_INDEPENDENT_CODE ON)

enable_testing()

option(BUILD_SHARED "Build shared library" ON)
option(BUILD_TESTING "Build tests" ON)
option(USE_MSVC_STATIC_RUNTIME "Use MSVC static runtime" OFF)

if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang|AppleClang")
    add_compile_options("-ffile-prefix-map=${CMAKE_CURRENT_SOURCE_DIR}=.")
    add_compile_options("-fdebug-prefix-map=${CMAKE_CURRENT_SOURCE_DIR}=.")
endif()

if (${CMAKE_SYSTEM_NAME} MATCHES "Android")
    set(BUILD_TESTING OFF)
    set(BUILD_SHARED OFF)

    set(CMAKE_C_FLAGS_RELWITHDEBINFO "-O2 -g -DNDEBUG")
    set(CMAKE_C_FLAGS_RELEASE "-O2 -g1 -DNDEBUG")

    add_compile_options(-fsigned-char)
    add_link_options("-Wl,-z,max-page-size=16384")
elseif(${CMAKE_SYSTEM_NAME} MATCHES "iOS")
    set(BUILD_TESTING OFF)
    set(BUILD_SHARED OFF)

    set(CMAKE_C_FLAGS_RELWITHDEBINFO "-O2 -g -DNDEBUG")
    set(CMAKE_C_FLAGS_RELEASE "-O2 -g1 -DNDEBUG")
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Emscripten")
    set(BUILD_TESTING OFF)
    set(BUILD_SHARED OFF)

    set(CMAKE_C_FLAGS_RELWITHDEBINFO "-O2 -g -DNDEBUG")
    set(CMAKE_C_FLAGS_RELEASE "-O2 -g1 -DNDEBUG")
endif()

if(CMAKE_C_COMPILER_ID MATCHES "MSVC")
    add_compile_options("/Brepro")
    add_link_options("/Brepro")
    add_compile_options("/pathmap:${CMAKE_CURRENT_SOURCE_DIR}=.")
    # add_link_options only reaches link.exe (executables + shared libs).
    # Static archives go through lib.exe, which needs /Brepro via the
    # separate CMAKE_STATIC_LINKER_FLAGS variable — otherwise the .lib
    # picks up a per-run timestamp in its archive header.
    string(APPEND CMAKE_STATIC_LINKER_FLAGS " /Brepro")
    if(USE_MSVC_STATIC_RUNTIME)
        message(STATUS "Using MSVC static runtime")
        set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
    else()
        message(STATUS "Using MSVC dynamic runtime")
        set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
    endif()
endif()

set(LIB_SOURCE_FILES
    lib/lz4.c
    lib/lz4hc.c
    lib/lz4frame.c
    lib/lz4file.c
    lib/xxhash.c)

set(LIB_PUBLIC_HEADERS
    lib/lz4.h
    lib/lz4hc.h
    lib/lz4frame.h
    lib/lz4file.h)

function(add_lz4_library TARGET_NAME LIB_TYPE)
    add_library(${TARGET_NAME} ${LIB_TYPE} ${LIB_SOURCE_FILES})
    target_include_directories(${TARGET_NAME} PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/lib)
    set_property(TARGET ${TARGET_NAME} PROPERTY C_VISIBILITY_PRESET hidden)
    target_compile_definitions(${TARGET_NAME} PRIVATE XXH_NAMESPACE=LZ4_)

    if(LIB_TYPE STREQUAL "SHARED")
        target_compile_definitions(${TARGET_NAME} PRIVATE XXH_EXPORT)
        if(WIN32)
            target_compile_definitions(${TARGET_NAME} PRIVATE LZ4_DLL_EXPORT=1)
        endif()
    endif()

    install(TARGETS ${TARGET_NAME}
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin)
endfunction()

add_lz4_library(lz4-static STATIC)

install(FILES
    ${LIB_PUBLIC_HEADERS}
    DESTINATION include)

if(BUILD_SHARED)
    add_lz4_library(lz4 SHARED)
endif()

if(BUILD_TESTING)
    add_executable(test-lz4-static test-lz4.c)
    target_link_libraries(test-lz4-static PUBLIC lz4-static)
    target_include_directories(test-lz4-static PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/lib)
    add_test(NAME test-lz4-static COMMAND $<TARGET_FILE:test-lz4-static>)

    if(BUILD_SHARED)
        add_executable(test-lz4 test-lz4.c)
        target_link_libraries(test-lz4 PUBLIC lz4)
        target_include_directories(test-lz4 PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/lib)
        add_test(NAME test-lz4 COMMAND $<TARGET_FILE:test-lz4>)
    endif()
endif()
