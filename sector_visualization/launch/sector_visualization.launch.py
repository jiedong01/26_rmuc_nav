from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='sector_visualization',
            executable='sector_visualizer',
            name='sector_visualizer',
            parameters=[{
                # 'robot_namespace': 'red_standard_robot1',
                'frame_id': 'odom',  # 可以根据实际情况修改，如 'chassis', 'base_footprint' 等
                'radius': 2.0,            # 扇区半径（米）
                'update_rate': 10.0,       # 更新频率（Hz）
            }],
            output='screen',
        ),
    ])
