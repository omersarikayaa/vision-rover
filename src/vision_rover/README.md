# Vision Rover

ROS 2 Jazzy + Gazebo Harmonic example rover with four driven wheels and an RGB camera.

```bash
cd /workspace/vision_rover_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch vision_rover vision_rover.launch.py
```

In another terminal:

```bash
source /opt/ros/jazzy/setup.bash
source /workspace/vision_rover_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Camera topics are `/camera/image` and `/camera/camera_info`.
