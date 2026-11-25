"""
Smoke test: play a street bag through the detector and check the output looks sane.

Not a unit test and not an accuracy test. It starts the real node with real ROS2
messages and checks only that detections come out and contain the expected kinds
of objects. It catches a broken pipeline, not wrong box positions.
"""
import os
import time
import unittest

import launch
import launch_ros.actions
import launch_testing.actions
import pytest
import rclpy
from vision_msgs.msg import Detection2DArray

BAG = os.environ.get('TEST_BAG', '/project/bags/street_half')
MODEL = os.environ.get('TEST_MODEL', '/project/models/yolox_s.onnx')
LISTEN_SECONDS = 25.0
VEHICLES = {'car', 'bus', 'truck'}


# Neither file is in the repository: skip, rather than fail, without them.
@pytest.mark.skipif(not (os.path.exists(BAG) and os.path.exists(MODEL)),
                    reason=f'needs {BAG} and {MODEL}')
@pytest.mark.launch_test
def generate_test_description():
    detector = launch_ros.actions.Node(
        package='perception_py', executable='detector',
        parameters=[{'model_path': MODEL}])
    player = launch.actions.ExecuteProcess(cmd=['ros2', 'bag', 'play', BAG])
    return launch.LaunchDescription([
        detector,
        launch.actions.TimerAction(period=3.0, actions=[player]),
        launch_testing.actions.ReadyToTest(),
    ])


class TestDetectorSmoke(unittest.TestCase):

    def test_smoke_people_and_vehicles(self):
        rclpy.init()
        node = rclpy.create_node('test_listener')
        received = []
        node.create_subscription(Detection2DArray, 'detections', received.append, 10)
        end = time.monotonic() + LISTEN_SECONDS
        while time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.1)
        node.destroy_node()
        rclpy.shutdown()

        labels = [{d.results[0].hypothesis.class_id for d in msg.detections}
                  for msg in received]
        print(f'{len(labels)} messages')
        self.assertGreater(len(labels), 20)
        with_person = sum('person' in frame for frame in labels)
        with_vehicle = sum(bool(frame & VEHICLES) for frame in labels)
        print(f'person in {with_person}, vehicle in {with_vehicle}')
        self.assertGreaterEqual(with_person / len(labels), 0.9)
        self.assertGreaterEqual(with_vehicle / len(labels), 0.5)
