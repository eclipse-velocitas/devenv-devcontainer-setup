cmake_minimum_required(VERSION 3.16)

project(Dummy)

set(TARGET_NAME "app")

find_package(fmt REQUIRED CONFIG)

add_executable(${TARGET_NAME}
    main.cpp
)

target_include_directories(${TARGET_NAME}
    PRIVATE
    ${fmt_INCLUDE_DIRS}
)

target_link_libraries(${TARGET_NAME}
    fmt::fmt
)
