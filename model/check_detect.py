"""Run preprocess -> ONNX model -> postprocess on one image and draw the boxes.

Run inside the export container (see the README):
    python /project/model/check_detect.py [image] [output.png]
Default image: YOLOX's own test photo (dog, bicycle, car).
"""
import importlib.util
import sys

import cv2
import onnxruntime as ort

from processing import postprocess, preprocess

# COCO class names, read straight from YOLOX's source file
spec = importlib.util.spec_from_file_location(
    'coco_classes', '/yolox/yolox/data/datasets/coco_classes.py')
names = importlib.util.module_from_spec(spec)
spec.loader.exec_module(names)
CLASSES = names.COCO_CLASSES

image_path = sys.argv[1] if len(sys.argv) > 1 else '/yolox/assets/dog.jpg'
out_path = sys.argv[2] if len(sys.argv) > 2 else 'boxes.png'
MODEL = '/project/models/yolox_s.onnx'

frame = cv2.imread(image_path)
x, scale = preprocess(frame)
session = ort.InferenceSession(MODEL)
output = session.run(None, {'images': x})[0]
boxes, scores, class_ids = postprocess(output, scale)

for box, score, class_id in zip(boxes, scores, class_ids):
    x1, y1, x2, y2 = box.astype(int)
    label = f'{CLASSES[class_id]} {score:.2f}'
    print(label, [x1, y1, x2, y2])
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(frame, label, (x1, max(y1 - 6, 14)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
cv2.imwrite(out_path, frame)
print('written', out_path)
