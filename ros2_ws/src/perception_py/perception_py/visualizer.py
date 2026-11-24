import cv2
import message_filters
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray


def draw(frame, detections):
    for detection in detections.detections:
        box = detection.bbox
        x1 = int(box.center.position.x - box.size_x / 2)
        y1 = int(box.center.position.y - box.size_y / 2)
        x2 = int(box.center.position.x + box.size_x / 2)
        y2 = int(box.center.position.y + box.size_y / 2)
        result = detection.results[0].hypothesis
        label = f'{result.class_id} {result.score:.2f}'
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, max(y1 - 6, 14)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return frame


class Visualizer(Node):

    def __init__(self):
        super().__init__('visualizer')
        self.bridge_ = CvBridge()
        self.publisher_ = self.create_publisher(Image, 'detections/image', 10)
        images = message_filters.Subscriber(self, Image, 'image_raw')
        detections = message_filters.Subscriber(self, Detection2DArray, 'detections')
        self.sync_ = message_filters.TimeSynchronizer([images, detections], 30)
        self.sync_.registerCallback(self.on_pair)

    def on_pair(self, image, detections):
        frame = self.bridge_.imgmsg_to_cv2(image, desired_encoding='bgr8')
        annotated = draw(frame.copy(), detections)
        out = self.bridge_.cv2_to_imgmsg(annotated, encoding='bgr8')
        out.header = image.header
        self.publisher_.publish(out)


def main():
    rclpy.init()
    node = Visualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
