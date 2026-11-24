import cv2
import numpy as np

INPUT_SIZE = 640
PAD_VALUE = 114


STRIDES = (8, 16, 32)


def preprocess(frame, size=INPUT_SIZE):
    height, width = frame.shape[:2]
    scale = min(size / height, size / width)
    new_h, new_w = int(height * scale), int(width * scale)
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((size, size, 3), PAD_VALUE, dtype=np.uint8)
    canvas[:new_h, :new_w] = resized
    chw = canvas.transpose(2, 0, 1)
    return chw[np.newaxis].astype(np.float32), scale


def decode(rows, size=INPUT_SIZE):
    grids, strides = [], []
    for stride in STRIDES:
        cells = size // stride
        xs, ys = np.meshgrid(np.arange(cells), np.arange(cells))
        grids.append(np.stack((xs, ys), axis=2).reshape(-1, 2))
        strides.append(np.full((cells * cells, 1), stride))
    grid = np.concatenate(grids)
    stride = np.concatenate(strides)
    centers = (rows[:, :2] + grid) * stride
    sizes = np.exp(rows[:, 2:4]) * stride
    return np.concatenate((centers - sizes / 2, centers + sizes / 2), axis=1)


def nms(boxes, scores, threshold):
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        best, rest = order[0], order[1:]
        keep.append(best)
        x1 = np.maximum(boxes[best, 0], boxes[rest, 0])
        y1 = np.maximum(boxes[best, 1], boxes[rest, 1])
        x2 = np.minimum(boxes[best, 2], boxes[rest, 2])
        y2 = np.minimum(boxes[best, 3], boxes[rest, 3])
        overlap = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
        iou = overlap / (areas[best] + areas[rest] - overlap)
        order = rest[iou < threshold]
    return keep


def postprocess(output, scale, score_threshold=0.3, nms_threshold=0.45):
    rows = output[0]
    boxes = decode(rows) / scale
    class_ids = rows[:, 5:].argmax(axis=1)
    scores = rows[:, 4] * rows[np.arange(len(rows)), 5 + class_ids]
    mask = scores > score_threshold
    boxes, scores, class_ids = boxes[mask], scores[mask], class_ids[mask]
    keep = []
    for class_id in np.unique(class_ids):
        idx = np.where(class_ids == class_id)[0]
        keep.extend(idx[nms(boxes[idx], scores[idx], nms_threshold)])
    keep = np.array(keep, dtype=int)
    return boxes[keep], scores[keep], class_ids[keep]
