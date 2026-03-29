#!/usr/bin/env python3
"""
nav2_bringup.launch.py
Bring up the full Nav2 navigation stack using nav2_params.yaml.
Requires a running map source (either map_server or SLAM).
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node, PushRosNamespace
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    pkg_nav2 = get_package_share_directory("nav2")
    nav2_bringup_dir = get_package_share_directory("nav2_bringup")

    params_file = os.path.join(pkg_nav2, "config", "nav2_params.yaml")

    # ── Launch arguments ──────────────────────────────────────────────────
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time", default_value="true", description="Use simulation clock"
    )
    autostart_arg = DeclareLaunchArgument(
        "autostart", default_value="true", description="Auto-start lifecycle nodes"
    )
    params_file_arg = DeclareLaunchArgument(
        "params_file",
        default_value=params_file,
        description="Full path to the Nav2 parameters file",
    )
    map_yaml_file_arg = DeclareLaunchArgument(
        "map",
        default_value="",
        description="Full path to map yaml file to load (leave empty for SLAM)",
    )
    namespace_arg = DeclareLaunchArgument(
        "namespace", default_value="", description="Robot namespace"
    )
    use_namespace_arg = DeclareLaunchArgument(
        "use_namespace",
        default_value="false",
        description="Whether to apply a namespace to nav nodes",
    )

    # Rewrite params to substitute use_sim_time
    configured_params = RewrittenYaml(
        source_file=LaunchConfiguration("params_file"),
        root_key=LaunchConfiguration("namespace"),
        param_rewrites={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "autostart": LaunchConfiguration("autostart"),
        },
        convert_types=True,
    )

    # ── Nav2 nodes ────────────────────────────────────────────────────────
    nav2_nodes = GroupAction(
        actions=[
            PushRosNamespace(
                condition=IfCondition(LaunchConfiguration("use_namespace")),
                namespace=LaunchConfiguration("namespace"),
            ),
            Node(
                package="nav2_map_server",
                executable="map_server",
                name="map_server",
                output="screen",
                parameters=[configured_params, {"yaml_filename": LaunchConfiguration("map")}],
            ),
            Node(
                package="nav2_amcl",
                executable="amcl",
                name="amcl",
                output="screen",
                parameters=[configured_params],
            ),
            Node(
                package="nav2_planner",
                executable="planner_server",
                name="planner_server",
                output="screen",
                parameters=[configured_params],
            ),
            Node(
                package="nav2_controller",
                executable="controller_server",
                name="controller_server",
                output="screen",
                parameters=[configured_params],
                remappings=[("cmd_vel", "cmd_vel")],
            ),
            Node(
                package="nav2_smoother",
                executable="smoother_server",
                name="smoother_server",
                output="screen",
                parameters=[configured_params],
            ),
            Node(
                package="nav2_behaviors",
                executable="behavior_server",
                name="behavior_server",
                output="screen",
                parameters=[configured_params],
            ),
            Node(
                package="nav2_bt_navigator",
                executable="bt_navigator",
                name="bt_navigator",
                output="screen",
                parameters=[configured_params],
            ),
            Node(
                package="nav2_waypoint_follower",
                executable="waypoint_follower",
                name="waypoint_follower",
                output="screen",
                parameters=[configured_params],
            ),
            Node(
                package="nav2_velocity_smoother",
                executable="velocity_smoother",
                name="velocity_smoother",
                output="screen",
                parameters=[configured_params],
                remappings=[
                    ("cmd_vel", "cmd_vel_nav"),
                    ("cmd_vel_smoothed", "cmd_vel"),
                ],
            ),
            Node(
                package="nav2_lifecycle_manager",
                executable="lifecycle_manager",
                name="lifecycle_manager_navigation",
                output="screen",
                parameters=[
                    {"use_sim_time": LaunchConfiguration("use_sim_time")},
                    {"autostart": LaunchConfiguration("autostart")},
                    {
                        "node_names": [
                            "map_server",
                            "amcl",
                            "planner_server",
                            "controller_server",
                            "smoother_server",
                            "behavior_server",
                            "bt_navigator",
                            "waypoint_follower",
                            "velocity_smoother",
                        ]
                    },
                ],
            ),
        ]
    )

    return LaunchDescription(
        [
            use_sim_time_arg,
            autostart_arg,
            params_file_arg,
            map_yaml_file_arg,
            namespace_arg,
            use_namespace_arg,
            nav2_nodes,
        ]
    )
