cmake_minimum_required(VERSION 3.8)
project(sector_visualization)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)

# install Python package
ament_python_install_package(${PROJECT_NAME})

# install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}/
)

# install Python executable script directly
install(PROGRAMS
  sector_visualization/sector_visualizer.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME sector_visualizer
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
