project(Dummy)

# use conan for dependency management
set(CONAN_BUILD_INFO_FILE ${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)

if(NOT EXISTS ${CONAN_BUILD_INFO_FILE})
    message(FATAL_ERROR "Conan build info file missing.")
    return()
else()
    include(${CONAN_BUILD_INFO_FILE})
    conan_basic_setup(TARGETS)
endif()

set(TARGET_NAME "app")

add_executable(${TARGET_NAME}
    main.cpp
)

include_directories(${TARGET_NAME}
    ${CONAN_INCLUDE_DIRS}
)

target_link_libraries(${TARGET_NAME}
    ${CONAN_LIBS}
)
