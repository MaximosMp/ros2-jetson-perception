# One-off tool image: converts YOLOX PyTorch weights to ONNX.
# Not needed at runtime; the ONNX file is all the other images use.
FROM python:3.10-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends git curl libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# PyTorch for the CPU (on arm64, the PyPI wheels are CPU-only)
RUN pip install --no-cache-dir torch==2.2.2 torchvision==0.17.2 "numpy<2"

# YOLOX source at a fixed release, used straight from the folder
RUN git clone --depth 1 --branch 0.3.0 https://github.com/Megvii-BaseDetection/YOLOX.git /yolox
RUN pip install --no-cache-dir opencv-python-headless==4.8.1.78 loguru tabulate thop psutil \
    onnx==1.14.1 onnxruntime==1.17.3

ENV PYTHONPATH=/yolox
WORKDIR /yolox
