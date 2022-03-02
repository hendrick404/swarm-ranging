cmake_minimum_required(VERSION 3.20.0)

set(BOARD_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")
set(DTS_ROOT   "${CMAKE_CURRENT_SOURCE_DIR}")

find_package(Zephyr)
project(my_zephyr_app)

file(GLOB application_sources src/antenna/common/**.c)
file(GLOB application_zephyr_sources src/antenna/zephyr/**.c)
file(GLOB decadriver_sources lib/decadriver/*.c lib/platform/*.c)
file(GLOB test_souces test/antenna/**.c)
file(GLOB unity_souces lib/unity/**.c)

target_sources(app PRIVATE ${application_sources})
target_sources(app PRIVATE ${application_zephyr_sources})
target_sources(app PRIVATE ${decadriver_sources})
target_include_directories(app PRIVATE lib/compiler)
target_include_directories(app PRIVATE lib/decadriver)
target_include_directories(app PRIVATE lib/platform)

