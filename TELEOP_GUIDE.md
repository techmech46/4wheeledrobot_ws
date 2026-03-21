# TELEOP_GUIDE

## Step-by-Step Instructions to Control the 4-Wheeled Robot with Teleop from a Phone

### 1. Network Setup
   - Ensure that your phone and the 4-wheeled robot are connected to the same Wi-Fi network.
   - Configure the robot's Wi-Fi settings, accessing the configuration file located in `/etc/wpa_supplicant/wpa_supplicant.conf` or through the setup interface.
   - Use the following network configuration:
     ```
     network={
         ssid="YourNetworkSSID"
         psk="YourNetworkPassword"
     }
     ```

### 2. Package Installation
   - Make sure you have ROS (Robot Operating System) installed on your robot.
   - Install the teleop package using the following command:
     ```bash
     sudo apt-get install ros-noetic-teleop
     ```
   - Ensure that `rosbridge_server` is installed to facilitate communication:
     ```bash
     sudo apt-get install ros-noetic-rosbridge-server
     ```
   - Additionally, install any dependencies required for your specific robot control:
     ```bash
     sudo apt-get install ros-noetic-robot-localization
     ```

### 3. Launch ROS Nodes
   - Start the ROS core:
     ```bash
     roscore
     ```
   - Launch the teleop node:
     ```bash
     rosrun teleop_twist_keyboard teleop_twist_keyboard.py
     ```
   - Start the rosbridge server:
     ```bash
     roslaunch rosbridge_server rosbridge_websocket.launch
     ```

### 4. Phone Setup
   - Download and install a mobile app that can send commands to ROS (e.g., Robot Commander, ROS Mobile).
   - Connect the app to the ROS bridge by entering the robot's IP address (e.g., `ws://192.168.1.100:9090`).

### 5. Usage Examples
   - Open the teleop app and connect to your robot.
   - Use the on-screen joystick or buttons to control the robot's movement.
   - Make sure to test the commands in a safe environment to ensure proper functionality.

### 6. Troubleshooting
   - If you encounter connection issues, verify the Wi-Fi settings on both your phone and robot.
   - Check that the appropriate ROS nodes are running.
   - Ensure that the firewall settings on the robot allow for WebSocket connections.

### Additional Resources
   - ROS Documentation: [ROS Wiki](http://wiki.ros.org/)
   - Teleop Tutorial: [Teleop Guide](http://wiki.ros.org/teleop_twist_keyboard/Tutorials)

---

This guide was created on 2026-03-20 05:51:06 UTC. 

Use this guide to get started with controlling your 4-wheeled robot using teleop from your phone!