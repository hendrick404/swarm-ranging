cmake_minimum_required(VERSION 3.20.0)

set(BOARD_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")
set(DTS_ROOT   "${CMAKE_CURRENT_SOURCE_DIR}")

find_package(Zephyr)
project(my_zephyr_app)

file(GLOB application_sources ../src/antenna/**.c)

target_sources(app PRIVATE ${application_sources})
