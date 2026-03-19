#!/usr/bin/env python3
"""
complete_system.launch.py
Master launch file that brings up the entire system:
  1. Gazebo simulation  (gazebo.launch.py)
  2. RViz2              (rviz.launch.py)
  3. SLAM               (slam.launch.py)   -- default
     OR AMCL            (amcl.launch.py)   -- when use_slam:=false + map:=<path>
  4. Nav2 navigation stack (nav2_bringup.launch.py)

Usage examples
--------------
  # SLAM mode (default)
  ros2 launch nav2 complete_system.launch.py

  # AMCL mode with a saved map
  ros2 launch nav2 complete_system.launch.py use_slam:=false map:=/path/to/map.yaml
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_nav2 = get_package_share_directory("nav2")
    launch_dir = os.path.join(pkg_nav2, "launch")

    # ── Launch arguments ──────────────────────────────────────────────────
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time", default_value="true", description="Use simulation clock"
    )
    use_slam_arg = DeclareLaunchArgument(
        "use_slam",
        default_value="true",
        description="Use SLAM (true) or AMCL with a saved map (false)",
    )
    map_arg = DeclareLaunchArgument(
        "map",
        default_value="",
        description="Full path to the map YAML file (only used when use_slam:=false)",
    )
    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(pkg_nav2, "worlds", "rectangle_room.world"),
        description="Path to the Gazebo world file",
    )
    robot_x_arg = DeclareLaunchArgument("robot_x", default_value="0.0")
    robot_y_arg = DeclareLaunchArgument("robot_y", default_value="0.0")

    # ── 1. Gazebo ─────────────────────────────────────────────────────────
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "gazebo.launch.py")),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "world": LaunchConfiguration("world"),
            "robot_x": LaunchConfiguration("robot_x"),
            "robot_y": LaunchConfiguration("robot_y"),
        }.items(),
    )

    # ── 2. RViz2 ─────────────────────────────────────────────────────────
    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "rviz.launch.py")),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
        }.items(),
    )

    # ── 3a. SLAM (use_slam = true) ────────────────────────────────────────
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "slam.launch.py")),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
        }.items(),
        condition=IfCondition(LaunchConfiguration("use_slam")),
    )

    # ── 3b. AMCL (use_slam = false) ───────────────────────────────────────
    amcl_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "amcl.launch.py")),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "map": LaunchConfiguration("map"),
        }.items(),
        condition=UnlessCondition(LaunchConfiguration("use_slam")),
    )

    # ── 4. Nav2 navigation stack ──────────────────────────────────────────
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "nav2_bringup.launch.py")),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "map": LaunchConfiguration("map"),
        }.items(),
    )

    return LaunchDescription(
        [
            use_sim_time_arg,
            use_slam_arg,
            map_arg,
            world_arg,
            robot_x_arg,
            robot_y_arg,
            LogInfo(msg="Launching complete 4-wheeled robot system …"),
            gazebo_launch,
            rviz_launch,
            slam_launch,
            amcl_launch,
            nav2_launch,
        ]
    )
