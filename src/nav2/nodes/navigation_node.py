#!/usr/bin/env python3
"""
navigation_node.py
──────────────────
ROS2 node that wraps nav2_simple_commander to provide autonomous navigation.

Features
--------
  • Send a single pose goal
  • Follow a list of waypoints
  • Cancel current navigation
  • Monitor and log navigation status

Run:
    ros2 run nav2 navigation_node
"""

import math
import threading
from enum import Enum, auto

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose, NavigateThroughPoses
from nav_msgs.msg import Odometry
from action_msgs.msg import GoalStatus


class NavState(Enum):
    IDLE       = auto()
    NAVIGATING = auto()
    SUCCEEDED  = auto()
    FAILED     = auto()
    CANCELLED  = auto()


class NavigationNode(Node):
    """
    High-level navigation node that drives a 4-wheeled robot to
    pose goals using the Nav2 NavigateToPose action.
    """

    def __init__(self):
        super().__init__("navigation_node")

        # Action clients
        self._nav_client = ActionClient(self, NavigateToPose, "navigate_to_pose")
        self._nav_through_client = ActionClient(
            self, NavigateThroughPoses, "navigate_through_poses"
        )

        # Odometry subscription (for current pose feedback)
        self._odom_sub = self.create_subscription(
            Odometry, "/odom", self._odom_callback, 10
        )
        self._current_pose: PoseStamped | None = None
        self._current_goal_handle = None
        self._state = NavState.IDLE

        self.get_logger().info("NavigationNode ready. Waiting for Nav2 action servers…")

    # ── Odometry ──────────────────────────────────────────────────────────
    def _odom_callback(self, msg: Odometry):
        ps = PoseStamped()
        ps.header = msg.header
        ps.pose   = msg.pose.pose
        self._current_pose = ps

    # ── Helper: build PoseStamped ─────────────────────────────────────────
    @staticmethod
    def make_pose(x: float, y: float, yaw_deg: float = 0.0,
                  frame: str = "map") -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = frame
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        yaw = math.radians(yaw_deg)
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose

    # ── Navigate to a single pose ─────────────────────────────────────────
    def navigate_to_pose(
        self,
        x: float,
        y: float,
        yaw_deg: float = 0.0,
        frame: str = "map",
        blocking: bool = True,
    ) -> bool:
        """
        Send a NavigateToPose goal.

        Parameters
        ----------
        blocking : bool
            If True, wait for the action to complete before returning.

        Returns
        -------
        bool
            True on success, False otherwise.
        """
        if not self._nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("NavigateToPose action server not available!")
            return False

        goal = NavigateToPose.Goal()
        goal.pose = self.make_pose(x, y, yaw_deg, frame)
        goal.pose.header.stamp = self.get_clock().now().to_msg()

        self.get_logger().info(f"Navigating to ({x:.2f}, {y:.2f}, {yaw_deg:.1f}°) …")
        self._state = NavState.NAVIGATING

        send_future = self._nav_client.send_goal_async(
            goal, feedback_callback=self._feedback_callback
        )
        send_future.add_done_callback(self._goal_response_callback)

        if blocking:
            self._wait_for_result()
            return self._state == NavState.SUCCEEDED
        return True

    # ── Navigate through multiple poses ──────────────────────────────────
    def navigate_through_poses(
        self,
        poses: list[tuple[float, float, float]],
        frame: str = "map",
        blocking: bool = True,
    ) -> bool:
        """
        Follow a list of (x, y, yaw_deg) waypoints via NavigateThroughPoses.
        """
        if not self._nav_through_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("NavigateThroughPoses action server not available!")
            return False

        goal = NavigateThroughPoses.Goal()
        now = self.get_clock().now().to_msg()
        for x, y, yaw in poses:
            ps = self.make_pose(x, y, yaw, frame)
            ps.header.stamp = now
            goal.poses.append(ps)

        self.get_logger().info(f"Following {len(poses)} waypoints …")
        self._state = NavState.NAVIGATING

        future = self._nav_through_client.send_goal_async(
            goal, feedback_callback=self._through_feedback_callback
        )
        future.add_done_callback(self._goal_response_callback)

        if blocking:
            self._wait_for_result()
            return self._state == NavState.SUCCEEDED
        return True

    # ── Cancel ────────────────────────────────────────────────────────────
    def cancel_navigation(self):
        if self._current_goal_handle is not None:
            self.get_logger().info("Cancelling current navigation goal …")
            self._current_goal_handle.cancel_goal_async()
            self._state = NavState.CANCELLED

    # ── Action callbacks ──────────────────────────────────────────────────
    def _goal_response_callback(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().warn("Goal was rejected by Nav2!")
            self._state = NavState.FAILED
            return
        self._current_goal_handle = handle
        result_future = handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

    def _result_callback(self, future):
        result = future.result()
        status = result.status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info("Navigation succeeded!")
            self._state = NavState.SUCCEEDED
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().info("Navigation cancelled.")
            self._state = NavState.CANCELLED
        else:
            self.get_logger().warn(f"Navigation failed with status: {status}")
            self._state = NavState.FAILED
        self._current_goal_handle = None

    def _feedback_callback(self, feedback_msg):
        fb = feedback_msg.feedback
        dist = fb.distance_remaining
        self.get_logger().debug(f"Distance remaining: {dist:.2f} m")

    def _through_feedback_callback(self, feedback_msg):
        fb = feedback_msg.feedback
        self.get_logger().debug(
            f"Remaining poses: {fb.number_of_poses_remaining}, "
            f"distance: {fb.distance_remaining:.2f} m"
        )

    # ── Blocking helper ───────────────────────────────────────────────────
    def _wait_for_result(self, timeout_sec: float = 120.0):
        import time
        elapsed = 0.0
        step    = 0.1
        while self._state == NavState.NAVIGATING and elapsed < timeout_sec:
            rclpy.spin_once(self, timeout_sec=step)
            elapsed += step
        if self._state == NavState.NAVIGATING:
            self.get_logger().warn("Navigation timed out!")
            self._state = NavState.FAILED

    # ── State query ───────────────────────────────────────────────────────
    @property
    def state(self) -> NavState:
        return self._state


def main(args=None):
    rclpy.init(args=args)
    node = NavigationNode()

    # Example: navigate to a sample goal after startup
    def _demo():
        import time
        time.sleep(3.0)  # wait for Nav2 stack to start
        node.navigate_to_pose(2.0, 1.5, 90.0)

    demo_thread = threading.Thread(target=_demo, daemon=True)
    demo_thread.start()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
