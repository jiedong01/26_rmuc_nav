cmake_minimum_required(VERSION 3.8)
project(elevation_bridge)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(grid_map_ros REQUIRED)
find_package(grid_map_msgs REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(pcl_ros REQUIRED)
find_package(PCL REQUIRED COMPONENTS common io)

add_executable(elevation_bridge_node src/elevation_bridge_node.cpp)

target_include_directories(elevation_bridge_node PRIVATE
  include
  ${PCL_INCLUDE_DIRS}
)

ament_target_dependencies(elevation_bridge_node
  rclcpp
  sensor_msgs
  nav_msgs
  grid_map_ros
  grid_map_msgs
  pcl_conversions
  pcl_ros
)

target_link_libraries(elevation_bridge_node
  ${PCL_LIBRARIES}
)

install(TARGETS elevation_bridge_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
