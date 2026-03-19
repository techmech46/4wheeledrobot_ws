#!/usr/bin/env python3
"""
rviz.launch.py
Start RViz2 with the project's RViz configuration.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_nav2 = get_package_share_directory("nav2")

    rviz_config_file = os.path.join(pkg_nav2, "config", "rviz_config.rviz")

    rviz_config_arg = DeclareLaunchArgument(
        "rviz_config",
        default_value=rviz_config_file,
        description="Full path to the RViz config file",
    )

    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time", default_value="true", description="Use simulation clock"
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", LaunchConfiguration("rviz_config")],
        parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
    )

    return LaunchDescription([use_sim_time_arg, rviz_config_arg, rviz_node])
