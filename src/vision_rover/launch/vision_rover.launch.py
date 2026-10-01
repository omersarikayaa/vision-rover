from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = Path(get_package_share_directory('vision_rover'))
    ros_gz_share = Path(get_package_share_directory('ros_gz_sim'))
    world = package_share / 'worlds' / 'vision_rover.sdf'
    bridge_config = package_share / 'config' / 'bridge.yaml'

    use_sim_time = LaunchConfiguration('use_sim_time')
    headless = LaunchConfiguration('headless')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(ros_gz_share / 'launch' / 'gz_sim.launch.py')),
        launch_arguments={'gz_args': f'-r {world}'}.items(),
        condition=UnlessCondition(headless),
    )

    gazebo_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(ros_gz_share / 'launch' / 'gz_sim.launch.py')),
        launch_arguments={'gz_args': f'-s -r {world}'}.items(),
        condition=IfCondition(headless),
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        parameters=[{'config_file': str(bridge_config), 'use_sim_time': use_sim_time}],
    )

    image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        name='camera_image_bridge',
        arguments=['/camera/image'],
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    yolo_detector = Node(
        package='vision_rover_perception',
        executable='yolo_detector',
        name='yolo_detector',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'image_topic': '/camera/image',
            'annotated_topic': '/vision/detections/image',
            'detections_topic': '/vision/detections',
            'max_inference_fps': 10.0,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('headless', default_value='false'),
        gazebo,
        gazebo_headless,
        bridge,
        image_bridge,
        yolo_detector,
    ])
