#!/usr/bin/env python3
"""
gazebo.launch.py
Launch Ignition Gazebo (Fortress), spawn the robot, and start ros_gz_bridge.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    ExecuteProcess,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_nav2 = get_package_share_directory("nav2")

    # ── Launch arguments ──────────────────────────────────────────────────
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time", default_value="true", description="Use simulation clock"
    )
    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(pkg_nav2, "worlds", "rectangle_room.world"),
        description="Path to Gazebo world file",
    )
    robot_x_arg = DeclareLaunchArgument(
        "robot_x", default_value="0.0", description="Robot spawn X position"
    )
    robot_y_arg = DeclareLaunchArgument(
        "robot_y", default_value="0.0", description="Robot spawn Y position"
    )
    robot_z_arg = DeclareLaunchArgument(
        "robot_z", default_value="0.1", description="Robot spawn Z position"
    )

    # ── Robot description (xacro → URDF) ─────────────────────────────────
    xacro_file = os.path.join(pkg_nav2, "urdf", "robot.urdf.xacro")
    robot_description_content = Command(
        [FindExecutable(name="xacro"), " ", xacro_file]
    )
    robot_description = {"robot_description": robot_description_content}

    # ── robot_state_publisher ─────────────────────────────────────────────
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": LaunchConfiguration("use_sim_time")}],
    )

    # ── Ignition Gazebo ───────────────────────────────────────────────────
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
            )
        ),
        launch_arguments={"gz_args": ["-r ", LaunchConfiguration("world")]}.items(),
    )

    # ── Spawn robot entity ────────────────────────────────────────────────
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        name="spawn_robot",
        output="screen",
        arguments=[
            "-name", "four_wheel_robot",
            "-topic", "robot_description",
            "-x", LaunchConfiguration("robot_x"),
            "-y", LaunchConfiguration("robot_y"),
            "-z", LaunchConfiguration("robot_z"),
        ],
    )

    # ── ros_gz_bridge ─────────────────────────────────────────────────────
    # Bridge Ignition ↔ ROS 2 topics
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="ros_gz_bridge",
        output="screen",
        arguments=[
            # clock
            "/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock",
            # cmd_vel  (ROS2 → Ignition)
            "/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist",
            # odom  (Ignition → ROS2)
            "/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry",
            # scan  (Ignition → ROS2)
            "/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan",
            # camera  (Ignition → ROS2)
            "/camera/image_raw@sensor_msgs/msg/Image[ignition.msgs.Image",
            "/camera/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo",
            # IMU  (Ignition → ROS2)
            "/imu/data@sensor_msgs/msg/Imu[ignition.msgs.IMU",
            # TF  (Ignition → ROS2)
            "/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
            # joint states  (Ignition → ROS2)
            "/joint_states@sensor_msgs/msg/JointState[ignition.msgs.Model",
        ],
        parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
    )

    return LaunchDescription(
        [
            use_sim_time_arg,
            world_arg,
            robot_x_arg,
            robot_y_arg,
            robot_z_arg,
            robot_state_publisher_node,
            gazebo,
            spawn_robot,
            bridge,
        ]
    )
