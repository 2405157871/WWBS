"""Box geometry and OpenCV colour helpers used by the ported okww combat code."""
from __future__ import annotations

import cv2
import numpy as np


class Box:
    def __init__(self, x, y, width, height, name=None):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.name = name
        self.confidence = 1.0
        self.mat = None

    @property
    def x1(self):
        return int(self.x)

    @property
    def y1(self):
        return int(self.y)

    @property
    def x2(self):
        return int(self.x + self.width)

    @property
    def y2(self):
        return int(self.y + self.height)

    def center(self):
        return int(self.x + self.width / 2), int(self.y + self.height / 2)

    def scale(self, fx, fy=None):
        """Scale around the box centre, as ok-script's Box does."""
        fy = fx if fy is None else fy
        centre_x = self.x + self.width / 2
        centre_y = self.y + self.height / 2
        return Box(centre_x - self.width * fx / 2, centre_y - self.height * fy / 2,
                   self.width * fx, self.height * fy, self.name)

    def copy(self, x_offset=0, y_offset=0, width_offset=0, height_offset=0, name=None):
        return Box(
            self.x + x_offset,
            self.y + y_offset,
            self.width + width_offset,
            self.height + height_offset,
            name if name is not None else self.name,
        )

    def crop_frame(self, frame):
        x1 = max(0, min(frame.shape[1], int(self.x)))
        y1 = max(0, min(frame.shape[0], int(self.y)))
        x2 = max(x1, min(frame.shape[1], int(self.x + self.width)))
        y2 = max(y1, min(frame.shape[0], int(self.y + self.height)))
        return frame[y1:y2, x1:x2]

    def __bool__(self):
        return True

    def __repr__(self):
        return f"Box({self.x:.0f}, {self.y:.0f}, {self.width:.0f}, {self.height:.0f}, name={self.name!r}, conf={self.confidence:.3f})"


def color_range_to_bound(color_dict):
    lower = np.array([color_dict['b'][0], color_dict['g'][0], color_dict['r'][0]], dtype=np.uint8)
    upper = np.array([color_dict['b'][1], color_dict['g'][1], color_dict['r'][1]], dtype=np.uint8)
    return lower, upper


def get_mask_in_color_range(frame, color_dict):
    lower, upper = color_range_to_bound(color_dict)
    mask = cv2.inRange(frame, lower, upper)
    return mask, int(np.count_nonzero(mask))


def color_percentage(frame, color_dict, box=None):
    if box is not None:
        frame = box.crop_frame(frame)
    if frame.size == 0:
        return 0.0
    mask, area = get_mask_in_color_range(frame, color_dict)
    return area / mask.size


def find_color_rectangles(frame, color_dict, min_width, min_height, box=None,
                          threshold=0.95, max_height=None):
    if box is not None:
        crop = box.crop_frame(frame)
        offset_x, offset_y = int(box.x), int(box.y)
    else:
        crop = frame
        offset_x = offset_y = 0
    if crop.size == 0:
        return []
    mask, _ = get_mask_in_color_range(crop, color_dict)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    results = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < min_width or h < min_height:
            continue
        if max_height is not None and h > max_height:
            continue
        fill = np.count_nonzero(mask[y:y + h, x:x + w]) / float(w * h)
        if fill < threshold:
            continue
        results.append(Box(x + offset_x, y + offset_y, w, h))
    return results


def mask_white(frame):
    _, mask = get_mask_in_color_range(frame, {'r': (210, 255), 'g': (210, 255), 'b': (210, 255)})
    return cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)


def is_pure_black(frame):
    return not np.any(frame)


def find_boxes_by_name(texts, match):
    """Return OCR boxes whose text matches one of ``texts`` (str / re.Pattern)."""
    boxes = []
    for box in texts or ():
        if isinstance(box, Box):
            for pattern in match if isinstance(match, (list, tuple)) else (match,):
                if isinstance(pattern, str) and pattern in (box.name or ''):
                    boxes.append(box)
                    break
                if hasattr(pattern, 'search') and pattern.search(box.name or ''):
                    boxes.append(box)
                    break
    return boxes


def find_boxes_within_boundary(boxes, boundary):
    if isinstance(boundary, str):
        return list(boxes)
    return [
        box for box in boxes
        if box.x >= boundary.x and box.y >= boundary.y
        and box.x + box.width <= boundary.x + boundary.width
        and box.y + box.height <= boundary.y + boundary.height
    ]


def get_bounding_box(boxes):
    if not boxes:
        return None
    x = min(box.x for box in boxes)
    y = min(box.y for box in boxes)
    x2 = max(box.x + box.width for box in boxes)
    y2 = max(box.y + box.height for box in boxes)
    return Box(x, y, x2 - x, y2 - y)


def sort_boxes(boxes):
    return sorted(boxes, key=lambda box: (box.y, box.x))


def safe_get(items, index, default=None):
    try:
        return items[index]
    except (IndexError, KeyError, TypeError):
        return default
