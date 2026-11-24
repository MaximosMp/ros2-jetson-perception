from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    video = LaunchConfiguration('video')
    scale = LaunchConfiguration('scale')
    model = LaunchConfiguration('model')
    return LaunchDescription([
        DeclareLaunchArgument('video', description='Video file to play'),
        DeclareLaunchArgument('scale', default_value='1.0'),
        DeclareLaunchArgument('model', default_value='/project/models/yolox_s.onnx'),
        Node(package='video_source', executable='video_publisher',
             parameters=[{'video_path': video, 'scale': scale}]),
        Node(package='perception_py', executable='detector',
             parameters=[{'model_path': model}]),
        Node(package='perception_py', executable='visualizer'),
        Node(package='web_video_server', executable='web_video_server'),
    ])
