# Development image: official ROS2 Humble + what the detector needs.
FROM ros:humble-perception

RUN apt-get update \
 && apt-get install -y --no-install-recommends ros-humble-vision-msgs ros-humble-web-video-server python3-pip \
 && rm -rf /var/lib/apt/lists/*

# numpy<2: the ROS2 packages (OpenCV, cv_bridge) are built against NumPy 1
RUN pip3 install --no-cache-dir onnxruntime==1.16.3 "numpy<2"
