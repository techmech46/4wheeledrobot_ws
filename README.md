# 4-Wheeled Mobile Robot – ROS2 Navigation Workspace

A complete ROS2 **Humble** workspace for a 4-wheeled differential-drive robot
featuring Gazebo Fortress (Ignition) simulation, Nav2 autonomous navigation,
SLAM Toolbox mapping, AMCL localisation, and RViz2 visualisation.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Building the Workspace](#building-the-workspace)
6. [Running the Simulation](#running-the-simulation)
7. [RViz Visualisation](#rviz-visualisation)
8. [SLAM – Building a Map](#slam--building-a-map)
9. [AMCL – Localisation with a Saved Map](#amcl--localisation-with-a-saved-map)
10. [Nav2 Navigation Stack](#nav2-navigation-stack)
11. [Complete System Launch](#complete-system-launch)
12. [Node Descriptions](#node-descriptions)
13. [Configuration Guide](#configuration-guide)
14. [Keyboard Teleoperation](#keyboard-teleoperation)
15. [Sending Navigation Goals](#sending-navigation-goals)
16. [Troubleshooting](#troubleshooting)

---

## Project Overview

| Item | Value |
|------|-------|
| ROS2 distribution | **Humble Hawksbill** |
| Gazebo version | **Ignition Fortress** (via `ros_gz`) |
| Package name | `nav2` |
| Language | Python (rclpy) |
| Robot type | 4-wheeled differential drive |
| Sensors | 2-D LiDAR · RGB Camera · IMU |
| Navigation | Nav2 (DWB controller, NavFn planner) |
| Mapping | SLAM Toolbox (online-async) |
| Localisation | AMCL (likelihood-field laser model) |

### Robot Dimensions

| Part | Size / Value |
|------|-------------|
| Base body | 0.50 m × 0.30 m × 0.15 m |
| Wheel radius | 0.10 m |
| Wheel separation | 0.35 m |
| Max linear speed | 0.26 m/s |
| Max angular speed | 1.0 rad/s |

---

## Repository Structure

```
4wheeledrobot_ws/
├── src/
│   └── nav2/
│       ├── launch/
│       │   ├── gazebo.launch.py          # Gazebo + robot spawn + bridge
│       │   ├── rviz.launch.py            # RViz2
│       │   ├── slam.launch.py            # SLAM Toolbox
│       │   ├── amcl.launch.py            # AMCL + map_server
│       │   ├── nav2_bringup.launch.py    # Full Nav2 stack
│       │   └── complete_system.launch.py # Master launch file
│       ├── config/
│       │   ├── nav2_params.yaml          # Nav2 tuning parameters
│       │   ├── slam_params.yaml          # SLAM Toolbox parameters
│       │   ├── amcl_params.yaml          # AMCL parameters
│       │   └── rviz_config.rviz          # RViz2 display configuration
│       ├── urdf/
│       │   ├── robot.urdf.xacro          # Robot kinematic description
│       │   └── gazebo.xacro              # Gazebo sensors & plugins
│       ├── worlds/
│       │   └── rectangle_room.world      # 10 m × 8 m SDF world
│       ├── nodes/
│       │   ├── robot_controller.py       # Teleoperation + wheel commands
│       │   ├── navigation_node.py        # nav2_simple_commander wrapper
│       │   └── goal_publisher.py         # Goal / waypoint publisher
│       ├── resource/nav2
│       ├── package.xml
│       ├── CMakeLists.txt
│       ├── setup.py
│       └── setup.cfg
├── .gitignore
└── README.md
```

---

## Prerequisites

### System packages

```bash
# Base ROS2 Humble desktop
sudo apt install ros-humble-desktop

# Gazebo Fortress (Ignition) – ros_gz bridge
sudo apt install ros-humble-ros-gz

# Nav2
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup

# SLAM Toolbox
sudo apt install ros-humble-slam-toolbox

# Robot state publisher, xacro
sudo apt install ros-humble-robot-state-publisher ros-humble-xacro \
                 ros-humble-joint-state-publisher

# Nav2 simple commander (Python API)
sudo apt install ros-humble-nav2-simple-commander
```

### Environment setup

```bash
source /opt/ros/humble/setup.bash
```

---

## Installation

```bash
# 1. Clone (or navigate to) the workspace
git clone <repo-url> ~/4wheeledrobot_ws
cd ~/4wheeledrobot_ws

# 2. Install ROS dependencies
rosdep install --from-paths src --ignore-src -r -y

# 3. Build
colcon build --symlink-install

# 4. Source the workspace overlay
source install/setup.bash
```

---

## Building the Workspace

```bash
cd ~/4wheeledrobot_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select nav2
source install/setup.bash
```

---

## Running the Simulation

Launch Gazebo Fortress with the rectangular room and spawn the robot:

```bash
ros2 launch nav2 gazebo.launch.py
```

Optional arguments:

| Argument | Default | Description |
|----------|---------|-------------|
| `world` | `rectangle_room.world` | Path to SDF world file |
| `robot_x` | `0.0` | Spawn X position |
| `robot_y` | `0.0` | Spawn Y position |
| `use_sim_time` | `true` | Use Gazebo clock |

---

## RViz Visualisation

```bash
ros2 launch nav2 rviz.launch.py
```

The pre-configured displays include:

- **RobotModel** – 3-D robot visualisation
- **LaserScan** – `/scan` topic
- **Map** – `/map` topic
- **GlobalPath / LocalPath** – `/plan` and `/local_plan`
- **Odometry** – `/odom`
- **TF** frames
- **2D Goal Pose tool** – click to send a navigation goal

---

## SLAM – Building a Map

Terminal 1 – simulation:
```bash
ros2 launch nav2 gazebo.launch.py
```

Terminal 2 – SLAM:
```bash
ros2 launch nav2 slam.launch.py
```

Terminal 3 – RViz:
```bash
ros2 launch nav2 rviz.launch.py
```

Terminal 4 – keyboard teleop to drive around and build the map:
```bash
ros2 run nav2 robot_controller
```

Save the map when finished:
```bash
ros2 run nav2_map_server map_saver_cli -f ~/my_map
# Produces ~/my_map.yaml + ~/my_map.pgm
```

---

## AMCL – Localisation with a Saved Map

```bash
ros2 launch nav2 amcl.launch.py map:=/path/to/my_map.yaml
```

After the nodes start, set an initial pose estimate in RViz using
**2D Pose Estimate**, then AMCL will converge on the robot's location.

---

## Nav2 Navigation Stack

With a map available (SLAM or AMCL), launch Nav2:

```bash
ros2 launch nav2 nav2_bringup.launch.py map:=/path/to/my_map.yaml
```

| Argument | Default | Description |
|----------|---------|-------------|
| `map` | `""` | Map YAML file path |
| `params_file` | `nav2_params.yaml` | Nav2 parameter file |
| `autostart` | `true` | Auto-activate lifecycle nodes |

---

## Complete System Launch

One command to launch everything:

```bash
# SLAM mode (default – builds map on the fly)
ros2 launch nav2 complete_system.launch.py

# AMCL mode (with a pre-built map)
ros2 launch nav2 complete_system.launch.py use_slam:=false map:=/path/to/my_map.yaml
```

| Argument | Default | Description |
|----------|---------|-------------|
| `use_slam` | `true` | `true` = SLAM, `false` = AMCL |
| `map` | `""` | Map path (AMCL mode) |
| `world` | `rectangle_room.world` | Gazebo world |
| `robot_x / robot_y` | `0.0` | Spawn position |

---

## Node Descriptions

### `robot_controller`
- **Package**: `nav2`
- **Executable**: `ros2 run nav2 robot_controller`
- **Subscribes**: `/cmd_vel` (geometry_msgs/Twist)
- **Publishes**: `/wheel_cmd` (std_msgs/Float64MultiArray), `/cmd_vel`
- **Features**: Differential-drive kinematics, keyboard teleoperation

### `navigation_node`
- **Package**: `nav2`
- **Executable**: `ros2 run nav2 navigation_node`
- **Action clients**: `navigate_to_pose`, `navigate_through_poses`
- **Features**: Single-goal and multi-waypoint navigation, status monitoring

### `goal_publisher`
- **Package**: `nav2`
- **Executable**: `ros2 run nav2 goal_publisher`
- **Publishes**: `/goal_pose` (geometry_msgs/PoseStamped)
- **Features**: Single goal from parameters, waypoint list, optional looping

---

## Configuration Guide

### Nav2 (`config/nav2_params.yaml`)

Key parameters to tune for the robot:

| Parameter | Location | Effect |
|-----------|----------|--------|
| `robot_radius` | costmaps | Inflation clearance |
| `max_vel_x` | `controller_server` | Max linear speed |
| `max_vel_theta` | `controller_server` | Max angular speed |
| `xy_goal_tolerance` | `controller_server` | Positional goal tolerance |
| `inflation_radius` | `inflation_layer` | Obstacle padding |

### SLAM (`config/slam_params.yaml`)

| Parameter | Default | Effect |
|-----------|---------|--------|
| `resolution` | `0.05` | Map resolution (m/cell) |
| `max_laser_range` | `10.0` | Max scan range used |
| `minimum_travel_distance` | `0.5` | Min movement before scan update |

### AMCL (`config/amcl_params.yaml`)

| Parameter | Default | Effect |
|-----------|---------|--------|
| `min_particles` / `max_particles` | 500 / 2000 | Particle filter size |
| `update_min_d` | `0.25` | Min distance before pose update |
| `sigma_hit` | `0.2` | Laser hit noise std dev |

---

## Keyboard Teleoperation

```bash
ros2 run nav2 robot_controller
```

| Key | Action |
|-----|--------|
| `W` / `↑` | Forward |
| `S` / `↓` | Backward |
| `A` / `←` | Turn left |
| `D` / `→` | Turn right |
| `Space` | Stop |
| `Q` | Quit |

---

## Sending Navigation Goals

### From RViz
Use the **2D Goal Pose** tool in the toolbar.

### From command line
```bash
ros2 topic pub --once /goal_pose geometry_msgs/msg/PoseStamped \
  '{header: {frame_id: map}, pose: {position: {x: 2.0, y: 1.5}, orientation: {w: 1.0}}}'
```

### Using goal_publisher node
```bash
# Single goal
ros2 run nav2 goal_publisher --ros-args -p goal_x:=3.0 -p goal_y:=2.0 -p goal_yaw_deg:=90.0

# Waypoint tour
ros2 run nav2 goal_publisher --ros-args -p waypoint_mode:=true -p loop_waypoints:=true
```

---

## Troubleshooting

### Gazebo doesn't find the world file
```bash
# Ensure the workspace is sourced
source ~/4wheeledrobot_ws/install/setup.bash
# Verify the file exists
ros2 pkg prefix nav2
```

### Robot not spawning in Gazebo
- Wait a few extra seconds for the Gazebo scene to fully load
- Check that `robot_description` topic is being published:
  ```bash
  ros2 topic echo /robot_description --once
  ```

### Nav2 nodes not activating
- Ensure `use_sim_time:=true` everywhere (Gazebo publishes `/clock`)
- Check lifecycle status:
  ```bash
  ros2 lifecycle list
  ```

### SLAM map not updating
- Make sure the `/scan` topic is receiving data:
  ```bash
  ros2 topic hz /scan
  ```
- Verify TF chain: `map → odom → base_footprint → base_link`
  ```bash
  ros2 run tf2_tools view_frames
  ```

### ros_gz_bridge errors
- Confirm `ros-humble-ros-gz` is installed and the Ignition topic names
  match those configured in `gazebo.xacro` and `gazebo.launch.py`.

### Build errors (missing packages)
```bash
cd ~/4wheeledrobot_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```
