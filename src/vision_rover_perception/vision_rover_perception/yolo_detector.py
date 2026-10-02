import time
from pathlib import Path

import cv2
import rclpy
from ament_index_python.packages import get_package_share_directory
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose


COCO_TARGET_CLASSES = [0, 1, 2, 3, 5, 7]


class YoloDetector(Node):
    def __init__(self):
        super().__init__('yolo_detector')

        default_model = str(
            Path(get_package_share_directory('vision_rover_perception'))
            / 'models'
            / 'yolo11n.pt'
        )
        self.declare_parameter('image_topic', '/camera/image')
        self.declare_parameter('annotated_topic', '/vision/detections/image')
        self.declare_parameter('detections_topic', '/vision/detections')
        self.declare_parameter('model_path', default_model)
        self.declare_parameter('confidence_threshold', 0.25)
        self.declare_parameter('max_inference_fps', 10.0)
        self.declare_parameter('device', 'auto')

        image_topic = self.get_parameter('image_topic').value
        annotated_topic = self.get_parameter('annotated_topic').value
        detections_topic = self.get_parameter('detections_topic').value
        model_path = self.get_parameter('model_path').value
        self.confidence = float(self.get_parameter('confidence_threshold').value)
        max_fps = float(self.get_parameter('max_inference_fps').value)
        requested_device = str(self.get_parameter('device').value)

        try:
            import torch
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                'YOLO dependencies are missing. Install the ultralytics package.'
            ) from exc

        if requested_device == 'auto':
            self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = requested_device

        self.model = YOLO(model_path)
        self.bridge = CvBridge()
        self.minimum_period = 0.0 if max_fps <= 0.0 else 1.0 / max_fps
        self.last_inference_started = 0.0
        self.smoothed_fps = 0.0

        self.image_publisher = self.create_publisher(Image, annotated_topic, 10)
        self.detections_publisher = self.create_publisher(
            Detection2DArray, detections_topic, 10
        )
        self.subscription = self.create_subscription(
            Image, image_topic, self.image_callback, qos_profile_sensor_data
        )

        self.get_logger().info(
            f'YOLO ready: model={model_path}, device={self.device}, input={image_topic}'
        )

    def image_callback(self, message: Image) -> None:
        now = time.monotonic()
        if now - self.last_inference_started < self.minimum_period:
            return
        self.last_inference_started = now

        try:
            frame = self.bridge.imgmsg_to_cv2(message, desired_encoding='bgr8')
            started = time.perf_counter()
            result = self.model.predict(
                source=frame,
                conf=self.confidence,
                classes=COCO_TARGET_CLASSES,
                device=self.device,
                verbose=False,
            )[0]
            elapsed = max(time.perf_counter() - started, 1e-6)
            instantaneous_fps = 1.0 / elapsed
            self.smoothed_fps = (
                instantaneous_fps
                if self.smoothed_fps == 0.0
                else 0.9 * self.smoothed_fps + 0.1 * instantaneous_fps
            )

            detections_message = Detection2DArray()
            detections_message.header = message.header
            annotated = frame.copy()

            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls[0].item())
                    confidence = float(box.conf[0].item())
                    x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                    class_name = str(result.names[class_id])

                    detection = Detection2D()
                    detection.header = message.header
                    hypothesis = ObjectHypothesisWithPose()
                    hypothesis.hypothesis.class_id = class_name
                    hypothesis.hypothesis.score = confidence
                    detection.results.append(hypothesis)
                    detection.bbox.center.position.x = (x1 + x2) / 2.0
                    detection.bbox.center.position.y = (y1 + y2) / 2.0
                    detection.bbox.size_x = x2 - x1
                    detection.bbox.size_y = y2 - y1
                    detections_message.detections.append(detection)

                    cv2.rectangle(
                        annotated,
                        (int(x1), int(y1)),
                        (int(x2), int(y2)),
                        (0, 255, 0),
                        2,
                    )
                    cv2.putText(
                        annotated,
                        f'{class_name} {confidence:.2f}',
                        (int(x1), max(20, int(y1) - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 255, 0),
                        2,
                        cv2.LINE_AA,
                    )

            cv2.putText(
                annotated,
                f'FPS: {self.smoothed_fps:.1f}',
                (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

            annotated_message = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
            annotated_message.header = message.header
            self.image_publisher.publish(annotated_message)
            self.detections_publisher.publish(detections_message)
        except Exception as exc:
            self.get_logger().error(f'Image processing failed: {exc}', throttle_duration_sec=2.0)


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
