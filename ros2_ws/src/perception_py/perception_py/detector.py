import time

import onnxruntime as ort
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose

from perception_py.coco_classes import COCO_CLASSES
from perception_py.processing import postprocess, preprocess


def to_detection(box, score, class_id, header):
    x1, y1, x2, y2 = box
    detection = Detection2D()
    detection.header = header
    detection.bbox.center.position.x = float((x1 + x2) / 2)
    detection.bbox.center.position.y = float((y1 + y2) / 2)
    detection.bbox.size_x = float(x2 - x1)
    detection.bbox.size_y = float(y2 - y1)
    result = ObjectHypothesisWithPose()
    result.hypothesis.class_id = COCO_CLASSES[class_id]
    result.hypothesis.score = float(score)
    detection.results.append(result)
    return detection


class Detector(Node):

    def __init__(self):
        super().__init__('detector')
        model_path = self.declare_parameter('model_path', '').value
        self.threshold_ = self.declare_parameter('score_threshold', 0.3).value
        if not model_path:
            raise RuntimeError(
                'No model given: add --ros-args -p model_path:=/path/to/model.onnx')
        self.session_ = ort.InferenceSession(model_path)
        self.bridge_ = CvBridge()
        self.publisher_ = self.create_publisher(Detection2DArray, 'detections', 10)
        self.subscription_ = self.create_subscription(
            Image, 'image_raw', self.on_image, 10)
        self.count_ = 0
        self.total_ms_ = 0.0
        self.get_logger().info(f'Loaded {model_path}')

    def on_image(self, msg):
        start = time.perf_counter()
        frame = self.bridge_.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        x, scale = preprocess(frame)
        output = self.session_.run(None, {'images': x})[0]
        boxes, scores, class_ids = postprocess(output, scale, self.threshold_)
        detections = Detection2DArray()
        detections.header = msg.header
        for box, score, class_id in zip(boxes, scores, class_ids):
            detections.detections.append(to_detection(box, score, class_id, msg.header))
        self.publisher_.publish(detections)
        self.total_ms_ += (time.perf_counter() - start) * 1000
        self.count_ += 1
        if self.count_ % 30 == 0:
            names = [COCO_CLASSES[c] for c in class_ids]
            self.get_logger().info(
                f'{self.count_} frames, {self.total_ms_ / self.count_:.1f} ms per frame, '
                f'last: {names}')


def main():
    rclpy.init()
    node = Detector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
