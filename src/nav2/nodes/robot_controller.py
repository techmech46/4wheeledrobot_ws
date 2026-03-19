#!/usr/bin/env python3
"""
robot_controller.py
────────────────────
ROS2 node that provides:
  • Keyboard teleoperation (WASD / arrow-keys) via stdin
  • Re-publishes /cmd_vel as wheel-speed commands on /wheel_cmd

Run:
    ros2 run nav2 robot_controller

Keyboard controls
-----------------
  W / ↑  : forward
  S / ↓  : backward
  A / ←  : turn left
  D / →  : turn right
  Space  : stop
  Q      : quit
"""

import sys
import threading
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64MultiArray

# ── terminal helper (Linux / macOS) ───────────────────────────────────────────
try:
    import tty
    import termios
    _TTY_AVAILABLE = True
except ImportError:
    _TTY_AVAILABLE = False


def _getch():
    """Read one character from stdin without echo."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ── Velocity presets ──────────────────────────────────────────────────────────
LINEAR_VEL  = 0.25   # m/s
ANGULAR_VEL = 0.80   # rad/s

KEY_BINDINGS = {
    "w": ( LINEAR_VEL, 0.0),
    "s": (-LINEAR_VEL, 0.0),
    "a": (0.0,  ANGULAR_VEL),
    "d": (0.0, -ANGULAR_VEL),
    " ": (0.0, 0.0),
}

# ANSI escape codes for arrow keys → reuse letter bindings
ARROW_BINDINGS = {
    "\x1b[A": KEY_BINDINGS["w"],
    "\x1b[B": KEY_BINDINGS["s"],
    "\x1b[C": KEY_BINDINGS["d"],
    "\x1b[D": KEY_BINDINGS["a"],
}


class RobotController(Node):
    """
    Listens for geometry_msgs/Twist on /cmd_vel, converts them to
    individual wheel velocities and re-publishes on /wheel_cmd.
    Also drives the keyboard teleoperation loop.
    """

    def __init__(self):
        super().__init__("robot_controller")

        # Robot geometry
        self.declare_parameter("wheel_separation", 0.35)   # metres
        self.declare_parameter("wheel_radius", 0.10)       # metres

        self._wheel_sep = self.get_parameter("wheel_separation").value
        self._wheel_rad = self.get_parameter("wheel_radius").value

        # Publisher → wheel speed commands  [fl, fr, rl, rr]  (rad/s)
        self._wheel_pub = self.create_publisher(
            Float64MultiArray, "/wheel_cmd", 10
        )

        # Subscriber → velocity commands from Nav2 / teleop
        self._cmd_sub = self.create_subscription(
            Twist, "/cmd_vel", self._cmd_vel_callback, 10
        )

        # Publisher → re-broadcast cmd_vel from teleop
        self._cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)

        self._current_twist = Twist()
        self.get_logger().info("RobotController node started.")

    # ── cmd_vel callback ──────────────────────────────────────────────────
    def _cmd_vel_callback(self, msg: Twist):
        self._current_twist = msg
        self._publish_wheel_cmd(msg.linear.x, msg.angular.z)

    def _publish_wheel_cmd(self, linear: float, angular: float):
        """
        Differential drive kinematics → individual wheel angular speeds.
        v_left  = (linear - angular * wheel_sep/2) / wheel_rad
        v_right = (linear + angular * wheel_sep/2) / wheel_rad
        """
        v_left  = (linear - angular * self._wheel_sep / 2.0) / self._wheel_rad
        v_right = (linear + angular * self._wheel_sep / 2.0) / self._wheel_rad

        msg = Float64MultiArray()
        msg.data = [v_left, v_right, v_left, v_right]   # fl, fr, rl, rr
        self._wheel_pub.publish(msg)

    # ── Teleop helpers ────────────────────────────────────────────────────
    def send_velocity(self, linear: float, angular: float):
        twist = Twist()
        twist.linear.x  = linear
        twist.angular.z = angular
        self._cmd_vel_pub.publish(twist)

    def run_teleop(self):
        if not _TTY_AVAILABLE:
            self.get_logger().warning(
                "TTY not available – keyboard teleop disabled. "
                "Use /cmd_vel topic to control the robot."
            )
            return

        print(
            "\n4-Wheeled Robot Keyboard Teleop\n"
            "────────────────────────────────\n"
            "  W/↑ : forward      S/↓ : backward\n"
            "  A/← : turn left    D/→ : turn right\n"
            "  Space : stop       Q : quit\n"
        )

        buf = ""
        while rclpy.ok():
            ch = _getch()

            # Escape sequence (arrow keys)
            if ch == "\x1b":
                buf = ch + sys.stdin.read(2)
                if buf in ARROW_BINDINGS:
                    lin, ang = ARROW_BINDINGS[buf]
                    self.send_velocity(lin, ang)
                buf = ""
                continue

            ch_lower = ch.lower()
            if ch_lower == "q":
                self.send_velocity(0.0, 0.0)
                break

            if ch_lower in KEY_BINDINGS:
                lin, ang = KEY_BINDINGS[ch_lower]
                self.send_velocity(lin, ang)


def main(args=None):
    rclpy.init(args=args)
    node = RobotController()

    # Spin in background thread so teleop loop can run in main thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    try:
        node.run_teleop()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
