from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='red_standard_robot1',
        description='Robot namespace'
    )
    
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time'
    )
    
    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    
    elevation_bridge_node = Node(
        package='elevation_bridge',
        executable='elevation_bridge_node',
        name='elevation_bridge_node',
        namespace=namespace,
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'map_length_x': 30.0,
            'map_length_y': 30.0,
            'resolution': 0.2,
            'max_slope_deg': 25.0,
            'obstacle_slope_deg': 35.0,
            'vehicle_height': 0.5,
            'map_frame': 'odom',
        }],
        remappings=[
            # 注意：因为有 namespace，这里不需要加前缀
            ('registered_scan', 'cloud_registered'),
            ('lidar_odometry', 'lidar_odometry'),  # 改成实际的话题名
        ]
    )
    
    return LaunchDescription([
        namespace_arg,
        use_sim_time_arg,
        elevation_bridge_node,
    ])