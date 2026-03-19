#!/usr/bin/env python3
"""
amcl.launch.py
Start AMCL-based localisation together with map_server.
Requires a pre-built map YAML file passed via the 'map' argument.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_nav2 = get_package_share_directory("nav2")
    amcl_params_file = os.path.join(pkg_nav2, "config", "amcl_params.yaml")

    # ── Launch arguments ──────────────────────────────────────────────────
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time", default_value="true", description="Use simulation clock"
    )
    map_arg = DeclareLaunchArgument(
        "map",
        default_value="",
        description="Full path to the map YAML file",
    )
    amcl_params_arg = DeclareLaunchArgument(
        "amcl_params_file",
        default_value=amcl_params_file,
        description="Full path to the AMCL parameters file",
    )

    # ── map_server ────────────────────────────────────────────────────────
    map_server_node = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
            {"yaml_filename": LaunchConfiguration("map")},
        ],
    )

    # ── amcl ──────────────────────────────────────────────────────────────
    amcl_node = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        parameters=[
            LaunchConfiguration("amcl_params_file"),
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
        ],
    )

    # ── lifecycle_manager (localisation only) ─────────────────────────────
    lifecycle_manager_node = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_localization",
        output="screen",
        parameters=[
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
            {"autostart": True},
            {"node_names": ["map_server", "amcl"]},
        ],
    )

    return LaunchDescription(
        [
            use_sim_time_arg,
            map_arg,
            amcl_params_arg,
            map_server_node,
            amcl_node,
            lifecycle_manager_node,
        ]
    )
