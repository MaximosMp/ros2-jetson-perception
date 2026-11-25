"""
Unit tests for pre- and post-processing: plain functions, no ROS2, no model file.

Every expected value is worked out by hand in the comments, so the tests also
serve as the reference the C++ node has to match.
"""
import numpy as np

from perception_py.processing import decode, nms, postprocess, preprocess

ROWS = 8400        # 80x80 + 40x40 + 20x20 grid cells
COLUMNS = 85       # 4 box values + objectness + 80 class scores


def model_output():
    """Return an all-zero model output: no detections."""
    return np.zeros((1, ROWS, COLUMNS), dtype=np.float32)


# preprocess

def test_preprocess_shape_and_scale():
    frame = np.zeros((540, 1160, 3), dtype=np.uint8)
    x, scale = preprocess(frame)
    assert x.shape == (1, 3, 640, 640)
    assert x.dtype == np.float32
    assert scale == 640 / 1160          # the longer side fits exactly


def test_preprocess_pads_bottom_with_grey():
    frame = np.full((540, 1160, 3), 200, dtype=np.uint8)
    x, _ = preprocess(frame)
    # 540 * 640 / 1160 = 297.9 -> 297 rows of image, the rest padding
    assert np.all(x[0, :, :297, :] == 200)
    assert np.all(x[0, :, 297:, :] == 114)


def test_preprocess_keeps_bgr_order():
    frame = np.zeros((640, 640, 3), dtype=np.uint8)
    frame[:] = (10, 20, 30)             # OpenCV order: blue, green, red
    x, _ = preprocess(frame)
    assert x[0, 0, 0, 0] == 10          # YOLOX expects BGR, not RGB
    assert x[0, 1, 0, 0] == 20
    assert x[0, 2, 0, 0] == 30


# decode

def test_decode_grid_cells_and_strides():
    boxes = decode(model_output()[0])
    # zero offsets: box centred on the cell corner, size = stride
    assert np.allclose(boxes[0], [-4, -4, 4, 4])        # stride 8, cell x=0 y=0
    assert np.allclose(boxes[1], [4, -4, 12, 4])        # stride 8, cell x=1 y=0
    assert np.allclose(boxes[80], [-4, 4, 4, 12])       # stride 8, cell x=0 y=1
    assert np.allclose(boxes[6400], [-8, -8, 8, 8])     # first stride-16 cell
    assert np.allclose(boxes[8000], [-16, -16, 16, 16])  # first stride-32 cell


def test_decode_offsets_and_size():
    rows = model_output()[0]
    rows[81, :2] = 0.5                  # cell x=1 y=1, centre (1.5 * 8, 1.5 * 8)
    rows[81, 2:4] = np.log(2)           # size 2 * 8 = 16
    assert np.allclose(decode(rows)[81], [4, 4, 20, 20])


# nms

def test_nms_drops_strong_overlap():
    boxes = np.array([[0, 0, 10, 10], [1, 1, 11, 11], [20, 20, 30, 30]], float)
    scores = np.array([0.9, 0.8, 0.7])
    # IoU of the first two = 81 / 119 = 0.68 > 0.45, the third touches neither
    assert list(nms(boxes, scores, 0.45)) == [0, 2]


def test_nms_keeps_weak_overlap():
    boxes = np.array([[0, 0, 10, 10], [5, 0, 15, 10]], float)
    scores = np.array([0.9, 0.8])
    # IoU = 50 / 150 = 0.33 < 0.45
    assert list(nms(boxes, scores, 0.45)) == [0, 1]


# postprocess

def test_postprocess_one_detection():
    output = model_output()
    output[0, 81, :2] = 0.5
    output[0, 81, 2:4] = np.log(2)      # box (4, 4, 20, 20) in the 640 image
    output[0, 81, 4] = 0.9              # objectness
    output[0, 81, 5 + 2] = 0.8          # class 2 (car)
    boxes, scores, class_ids = postprocess(output, scale=0.5)
    assert np.allclose(boxes, [[8, 8, 40, 40]])         # divided by the scale
    assert np.allclose(scores, [0.72])                  # 0.9 * 0.8
    assert list(class_ids) == [2]


def test_postprocess_below_threshold_gives_nothing():
    output = model_output()
    output[0, 81, 4] = 0.5
    output[0, 81, 5] = 0.5              # score 0.25 < 0.3
    boxes, scores, class_ids = postprocess(output, scale=1.0)
    assert boxes.shape == (0, 4)
    assert len(scores) == 0 and len(class_ids) == 0


def same_box_twice(second_class):
    """Two rows that decode to the same box (4, 4, 20, 20), class 0 and another."""
    output = model_output()
    output[0, 81, :4] = [0.5, 0.5, np.log(2), np.log(2)]     # cell x=1 y=1
    output[0, 82, :4] = [-0.5, 0.5, np.log(2), np.log(2)]    # cell x=2 y=1
    output[0, 81, 4] = output[0, 82, 4] = 1.0
    output[0, 81, 5] = 0.9
    output[0, 82, 5 + second_class] = 0.8
    return postprocess(output, scale=1.0)


def test_postprocess_nms_within_one_class():
    _, scores, class_ids = same_box_twice(second_class=0)
    assert np.allclose(scores, [0.9]) and list(class_ids) == [0]


def test_postprocess_no_nms_across_classes():
    _, scores, class_ids = same_box_twice(second_class=2)
    assert sorted(class_ids) == [0, 2]
