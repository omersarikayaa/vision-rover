# Vision Rover

ROS 2 Jazzy and Gazebo Harmonic based four-wheel rover with an RGB camera and a
CPU-compatible YOLO11n perception pipeline.

## Run

```bash
cd /workspace/vision_rover_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch vision_rover vision_rover.launch.py
```

Drive from another container terminal:

```bash
source /opt/ros/jazzy/setup.bash
source /workspace/vision_rover_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

View annotated detections:

```bash
ros2 run image_view image_view --ros-args -r image:=/vision/detections/image
```

Machine-readable detections use `vision_msgs/msg/Detection2DArray` on
`/vision/detections`.
