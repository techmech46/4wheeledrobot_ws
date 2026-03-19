#!/usr/bin/env python3
"""
goal_publisher.py
──────────────────
ROS2 node that publishes navigation goals to /goal_pose.

Features
--------
  • Publish a single goal from command-line parameters
  • Cycle through a hard-coded or parameter-supplied waypoint list
  • Optionally loop the waypoint list forever

Parameters
----------
  goal_x          (float, default 0.0)  – x of single goal
  goal_y          (float, default 0.0)  – y of single goal
  goal_yaw_deg    (float, default 0.0)  – yaw of single goal (degrees)
  waypoint_mode   (bool,  default false) – if true, follow the waypoints list
  loop_waypoints  (bool,  default false) – if true, loop waypoints indefinitely
  waypoint_delay  (float, default 5.0)  – seconds between consecutive goals

Run (single goal):
    ros2 run nav2 goal_publisher --ros-args -p goal_x:=3.0 -p goal_y:=2.0

Run (waypoints):
    ros2 run nav2 goal_publisher --ros-args -p waypoint_mode:=true
"""

import math
import threading
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry


# Default waypoints  [(x, y, yaw_deg), …]
DEFAULT_WAYPOINTS = [
    ( 3.0,  2.0,   0.0),
    ( 3.0, -2.0, -90.0),
    (-3.0, -2.0, 180.0),
    (-3.0,  2.0,  90.0),
    ( 0.0,  0.0,   0.0),
]


class GoalPublisher(Node):
    """Publishes geometry_msgs/PoseStamped to /goal_pose."""

    def __init__(self):
        super().__init__("goal_publisher")

        # ── Parameters ────────────────────────────────────────────────────
        self.declare_parameter("goal_x",        0.0)
        self.declare_parameter("goal_y",        0.0)
        self.declare_parameter("goal_yaw_deg",  0.0)
        self.declare_parameter("waypoint_mode", False)
        self.declare_parameter("loop_waypoints", False)
        self.declare_parameter("waypoint_delay", 5.0)

        self._goal_x       = self.get_parameter("goal_x").value
        self._goal_y       = self.get_parameter("goal_y").value
        self._goal_yaw     = self.get_parameter("goal_yaw_deg").value
        self._wp_mode      = self.get_parameter("waypoint_mode").value
        self._loop_wp      = self.get_parameter("loop_waypoints").value
        self._wp_delay     = self.get_parameter("waypoint_delay").value

        # ── Publisher ─────────────────────────────────────────────────────
        self._goal_pub = self.create_publisher(PoseStamped, "/goal_pose", 10)

        # ── Subscription (optional feedback) ─────────────────────────────
        self._odom_sub = self.create_subscription(
            Odometry, "/odom", self._odom_callback, 10
        )
        self._current_x = 0.0
        self._current_y = 0.0

        self.get_logger().info(
            f"GoalPublisher started – waypoint_mode={self._wp_mode}, "
            f"loop={self._loop_wp}, delay={self._wp_delay}s"
        )

    # ── Odometry ──────────────────────────────────────────────────────────
    def _odom_callback(self, msg: Odometry):
        self._current_x = msg.pose.pose.position.x
        self._current_y = msg.pose.pose.position.y

    # ── Build PoseStamped ─────────────────────────────────────────────────
    def _make_pose(self, x: float, y: float, yaw_deg: float,
                   frame: str = "map") -> PoseStamped:
        ps = PoseStamped()
        ps.header.frame_id = frame
        ps.header.stamp    = self.get_clock().now().to_msg()
        ps.pose.position.x = x
        ps.pose.position.y = y
        ps.pose.position.z = 0.0
        yaw = math.radians(yaw_deg)
        ps.pose.orientation.z = math.sin(yaw / 2.0)
        ps.pose.orientation.w = math.cos(yaw / 2.0)
        return ps

    # ── Publish helpers ───────────────────────────────────────────────────
    def publish_single_goal(self, x: float, y: float, yaw_deg: float = 0.0):
        pose = self._make_pose(x, y, yaw_deg)
        self._goal_pub.publish(pose)
        self.get_logger().info(f"Published goal → ({x:.2f}, {y:.2f}, {yaw_deg:.1f}°)")

    def publish_waypoints(
        self,
        waypoints: list[tuple[float, float, float]] | None = None,
    ):
        """
        Publish waypoints sequentially with a delay between each.
        If loop_waypoints is True, restarts from the beginning after
        the last waypoint.
        """
        if waypoints is None:
            waypoints = DEFAULT_WAYPOINTS

        self.get_logger().info(
            f"Starting waypoint tour ({len(waypoints)} points, loop={self._loop_wp})"
        )

        while rclpy.ok():
            for idx, (x, y, yaw) in enumerate(waypoints):
                self.get_logger().info(
                    f"Waypoint {idx + 1}/{len(waypoints)}: "
                    f"({x:.2f}, {y:.2f}, {yaw:.1f}°)"
                )
                self.publish_single_goal(x, y, yaw)
                time.sleep(self._wp_delay)

            if not self._loop_wp:
                break

        self.get_logger().info("Waypoint tour finished.")

    # ── Entry point ───────────────────────────────────────────────────────
    def run(self):
        # Small startup delay so the subscriber can receive clock/map frames
        time.sleep(2.0)

        if self._wp_mode:
            self.publish_waypoints()
        else:
            self.publish_single_goal(self._goal_x, self._goal_y, self._goal_yaw)


def main(args=None):
    rclpy.init(args=args)
    node = GoalPublisher()

    run_thread = threading.Thread(target=node.run, daemon=True)
    run_thread.start()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
