cmake_minimum_required(VERSION 3.20.0)

set(BOARD_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")
set(DTS_ROOT   "${CMAKE_CURRENT_SOURCE_DIR}")

find_package(Zephyr)
project(my_zephyr_app)

file(GLOB application_sources src/antenna/**.c)
file(GLOB decadriver_sources lib/**.c)

target_sources(app PRIVATE ${application_sources})
target_sources(app PRIVATE ${decadriver_sources})
target_include_directories(app PRIVATE lib/compiler)
target_include_directories(app PRIVATE lib/decadriver)
target_include_directories(app PRIVATE lib/platform)