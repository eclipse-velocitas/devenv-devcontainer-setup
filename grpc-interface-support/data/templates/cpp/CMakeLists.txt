cmake_minimum_required(VERSION 3.15)

set(PROJECT_NAME ${{ service_name_lower }}-service-sdk)

project(${PROJECT_NAME} CXX)

add_library(${PROJECT_NAME}
    ${{ cmake_sources }}
)

target_include_directories(${PROJECT_NAME}
    PUBLIC include
)

include_directories(
    ${CMAKE_INCLUDE_PATH}
    include/services/${{ service_name_lower }}
    include/${{ proto_location }}
)

set(HEADERS
    ${{ cmake_headers }}
)

set(PROTO_HEADERS
    ${{ proto_headers }}
)

set_target_properties(${PROJECT_NAME} PROPERTIES
    PUBLIC_HEADER "${HEADERS}"
)

install(TARGETS ${PROJECT_NAME}
    PUBLIC_HEADER DESTINATION include/services/${{ service_name_lower }}/${{ proto_location }}
)

install(FILES ${PROTO_HEADERS} DESTINATION include/${{ proto_location }})
