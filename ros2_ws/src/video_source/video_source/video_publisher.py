import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image


class VideoPublisher(Node):

    def __init__(self):
        super().__init__('video_publisher')
        path = self.declare_parameter('video_path', '').value
        self.scale_ = self.declare_parameter('scale', 1.0).value
        if not path:
            raise RuntimeError(
                'No video given: add --ros-args -p video_path:=/path/to/video')
        self.capture_ = cv2.VideoCapture(path)
        if not self.capture_.isOpened():
            raise RuntimeError(f'Cannot open video: {path}')
        fps = self.capture_.get(cv2.CAP_PROP_FPS)
        self.get_logger().info(
            f'Opened {path} at {fps:.1f} fps, scale {self.scale_}')
        self.bridge_ = CvBridge()
        self.publisher_ = self.create_publisher(Image, 'image_raw', 10)
        self.timer_ = self.create_timer(1.0 / fps, self.on_timer)
        self.count_ = 0

    def on_timer(self):
        ok, frame = self.capture_.read()
        if not ok:
            self.get_logger().info('End of video, starting again')
            self.capture_.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return
        if self.scale_ != 1.0:
            frame = cv2.resize(frame, None, fx=self.scale_, fy=self.scale_,
                               interpolation=cv2.INTER_AREA)
        msg = self.bridge_.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera'
        self.publisher_.publish(msg)
        self.count_ += 1
        if self.count_ % 30 == 0:
            self.get_logger().info(f'Published {self.count_} frames')


def main():
    rclpy.init()
    node = VideoPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
