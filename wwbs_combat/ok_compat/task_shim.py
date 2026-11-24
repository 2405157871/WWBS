"""Minimal ok-script compatible task surface.

The ported okww combat classes call ``from ok import ...`` and rely on a set of
``BaseTask`` helpers.  This module reimplements exactly that surface on top of
WWBS's ``ClientWindowController`` (SendInput + in-memory capture), OpenCV
template matching and the local Windows OCR helper.  No ok-script dependency.
"""
from __future__ import annotations

import ctypes
import logging
import re
import time
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

from . import hotkeys
from .box import (
    Box, color_percentage, color_range_to_bound, find_color_rectangles,
    find_boxes_by_name, find_boxes_within_boundary, get_bounding_box,
    get_mask_in_color_range, is_pure_black, mask_white, safe_get, sort_boxes,
)
from .matcher import TemplateMatcher
from .ocr import OcrBackend, WindowsOcrBackend


class TaskDisabledException(Exception):
    pass


class CannotFindException(Exception):
    pass


class WaitFailedException(Exception):
    pass


class _Logger:
    def __init__(self, name):
        self._logger = logging.getLogger(name)

    def _write(self, method, msg, args, kwargs):
        kwargs.pop('notify', None)
        text = str(msg)
        if args:
            text = text + ' ' + ' '.join(str(arg) for arg in args)
        getattr(self._logger, method)(text, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._write('debug', msg, args, kwargs)

    def info(self, msg, *args, **kwargs):
        self._write('info', msg, args, kwargs)

    def warning(self, msg, *args, **kwargs):
        self._write('warning', msg, args, kwargs)

    def error(self, msg, *args, **kwargs):
        self._write('error', msg, args, kwargs)


class Logger:
    @staticmethod
    def get_logger(name):
        return _Logger(name)


class Config(dict):
    def __init__(self, name=None, defaults=None):
        super().__init__(defaults or {})
        self.name = name


class ConfigOption:
    def __init__(self, name=None, defaults=None, **kwargs):
        self.name = name
        self.defaults = defaults or {}
        self.__dict__.update(kwargs)


class Icon:
    GAME = 'game'
    PEOPLE = 'people'


class FindFeature:
    pass


class BaseScene:
    def __init__(self, *args, **kwargs):
        pass


class _GlobalApp:
    logged_in = True

    @staticmethod
    def yolo_detect(*args, **kwargs):
        return []


class _GlobalConfig(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class og:
    config = _GlobalConfig({'ocr': {'params': {'use_openvino': False}}})
    my_app = _GlobalApp()


def get_path_relative_to_exe(path):
    return Path(path)


def run_task(config, task=None, debug=False):
    raise RuntimeError('run_task is only available inside the ok-script runtime')


def calculate_color_percentage(frame, color_dict=None, box=None):
    if isinstance(frame, np.ndarray):
        return color_percentage(frame, color_dict, box)
    if isinstance(color_dict, np.ndarray):
        return color_percentage(color_dict, frame, box)
    return 0.0


class BaseTask:
    """Base contract consumed by all ported okww combat classes."""

    def __init__(self, *args, **kwargs):
        self.controller = kwargs.pop('controller', None)
        self.stop_event = kwargs.pop('stop_event', None)
        ocr_backend = kwargs.pop('ocr_backend', None)
        template_dir = kwargs.pop('template_dir', None)
        self.debug = bool(kwargs.pop('debug', False))
        self.hwnd_title = 'Wuthering Waves'
        self.default_config = {}
        self.config_description = {}
        self.config = dict(hotkeys.GLOBAL_CONFIG.get('Game Hotkey', {}))
        self.config['_enabled'] = True
        self.config.update(kwargs.pop('config', {}) or {})
        self.info = {}
        self._app = None
        self.frame = None
        self.width = 0
        self.height = 0
        self.last_capture_at = 0.0
        self.trigger_interval = 0.1
        self.enabled = True
        self._matcher = TemplateMatcher(template_dir)
        self._ocr: OcrBackend = ocr_backend or WindowsOcrBackend()
        self.logger = Logger.get_logger(type(self).__name__)
        self.executor = SimpleNamespace(
            interaction=SimpleNamespace(
                capture=SimpleNamespace(get_abs_cords=lambda x, y: (int(x), int(y))),
            ),
            ocr_lib=lambda *a, **kw: [],
        )

    # ---------------------------------------------------------------- lifecycle
    def _stopped(self):
        return self.stop_event is not None and self.stop_event.is_set()

    def _ensure_frame(self, max_age=0.05):
        if self.controller is None:
            return self.frame
        now = time.monotonic()
        if self.frame is None or now - self.last_capture_at >= max_age:
            self.next_frame()
        return self.frame

    def next_frame(self):
        if self._stopped():
            raise TaskDisabledException('task stopped')
        if self.controller is None:
            return self.frame
        self.frame = self.controller.capture_frame()
        if self.frame is None or self.frame.size == 0:
            raise RuntimeError('未能截取游戏画面，图像识别战斗已停止。')
        self.height, self.width = self.frame.shape[:2]
        self.last_capture_at = time.monotonic()
        return self.frame

    def sleep(self, sec):
        if sec <= 0:
            if self._stopped():
                raise TaskDisabledException('task stopped')
            return
        if self.stop_event is None:
            time.sleep(sec)
        else:
            self.stop_event.wait(sec)
        if self._stopped():
            raise TaskDisabledException('task stopped')

    def disable(self):
        self.enabled = False
        if self.stop_event is not None:
            self.stop_event.set()

    def run(self):
        return None

    def tr(self, text):
        return text

    def log_info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def log_debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def log_warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def log_error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def info_set(self, key, value):
        self.info[key] = value

    def info_get(self, key, default=None):
        return self.info.get(key, default)

    def is_browser(self):
        return False

    def is_pure_black(self, frame):
        return is_pure_black(frame if frame is not None else self.frame)

    # --------------------------------------------------------------- geometry
    def width_of_screen(self, ratio):
        return int(self.width * ratio)

    def height_of_screen(self, ratio):
        return int(self.height * ratio)

    def box_of_screen(self, x1, y1, x2, y2, hcenter=False, vcenter=False, name=None):
        if hcenter:
            shift = (1 - (x2 - x1)) / 2
            x1, x2 = x1 + shift, x2 + shift
        if vcenter:
            shift = (1 - (y2 - y1)) / 2
            y1, y2 = y1 + shift, y2 + shift
        return Box(x1 * self.width, y1 * self.height,
                   (x2 - x1) * self.width, (y2 - y1) * self.height, name=name)

    def box_of_screen_scaled(self, ref_width, ref_height, x1, y1, x2, y2,
                             name=None, hcenter=False, vcenter=False):
        scale_x = self.width / ref_width
        scale_y = self.height / ref_height
        if hcenter:
            shift = (1 - (x2 - x1) / ref_width) / 2
            x1, x2 = x1 + shift * ref_width, x2 + shift * ref_width
        if vcenter:
            shift = (1 - (y2 - y1) / ref_height) / 2
            y1, y2 = y1 + shift * ref_height, y2 + shift * ref_height
        return Box(x1 * scale_x, y1 * scale_y,
                   (x2 - x1) * scale_x, (y2 - y1) * scale_y, name=name)

    def get_box_by_name(self, name):
        if not self.width or not self.height:
            self._ensure_frame()
        found = self._matcher.get_box_by_name(name, self.width, self.height)
        if found is not None:
            return found
        return Box(self.width * 0.2, self.height * 0.2,
                   self.width * 0.6, self.height * 0.6, name=str(name))

    def get_feature_by_name(self, name):
        return self._matcher.get_feature_by_name(name)

    def feature_exists(self, name):
        return self._matcher.has_template(name)

    # --------------------------------------------------------------- matching
    def find_one(self, name, box=None, threshold=0.8, target_height=None,
                 frame_processor=None, template=None, horizontal_variance=0.002,
                 vertical_variance=0.002, *args, **kwargs):
        frame = self._ensure_frame()
        if frame is None:
            return None
        if args and isinstance(args[0], (int, float)):
            threshold = args[0]
        return self._matcher.find_one(
            name, frame, box=box, threshold=threshold, target_height=target_height,
            frame_processor=frame_processor, template=template,
            horizontal_variance=horizontal_variance, vertical_variance=vertical_variance,
        )

    def find_best_match_in_box(self, box, names, threshold=0.6, *args, **kwargs):
        frame = self._ensure_frame()
        return self._matcher.find_best_match_in_box(box, names, threshold=threshold,
                                                    frame=frame)

    def find_feature(self, name, box=None, threshold=0.8, **kwargs):
        frame = self._ensure_frame()
        return self._matcher.find_feature(name, frame, box=box,
                                          threshold=threshold,
                                          target_height=kwargs.get('target_height'))

    def find_boxes(self, ocr_result, boundary=None, match=None, **kwargs):
        boxes = find_boxes_by_name(ocr_result or (), match)
        if boundary is not None:
            if isinstance(boundary, str):
                boundary = self.get_box_by_name(boundary)
            boxes = find_boxes_within_boundary(boxes, boundary)
        return boxes

    def wait_feature(self, name, threshold=0.8, box=None, time_out=5,
                     raise_if_not_found=False, settle_time=0, **kwargs):
        deadline = time.monotonic() + time_out
        while True:
            self.next_frame()
            found = self.find_one(name, box=box, threshold=threshold)
            if found:
                if settle_time:
                    self.sleep(settle_time)
                return found
            if time.monotonic() >= deadline:
                if raise_if_not_found:
                    raise WaitFailedException(f'feature not found: {name}')
                return None
            self.sleep(0.05)

    def wait_click_feature(self, name, raise_if_not_found=False, time_out=5,
                           click_after_delay=0, threshold=0.8, **kwargs):
        found = self.wait_feature(name, threshold=threshold, time_out=time_out,
                                  raise_if_not_found=raise_if_not_found)
        if found:
            self.click(found)
            return found
        return None

    def wait_ocr(self, match=None, box=None, time_out=5, raise_if_not_found=False,
                 settle_time=0, **kwargs):
        deadline = time.monotonic() + time_out
        while True:
            self.next_frame()
            found = self.ocr(box=box, match=match)
            if found:
                if settle_time:
                    self.sleep(settle_time)
                return found
            if time.monotonic() >= deadline:
                if raise_if_not_found:
                    raise WaitFailedException('ocr text not found')
                return []
            self.sleep(0.05)

    def wait_until(self, func, time_out=5, raise_if_not_found=True,
                   post_action=None, settle_time=0):
        deadline = time.monotonic() + time_out
        while True:
            if post_action is not None:
                post_action()
            self.next_frame()
            result = func()
            if result:
                if settle_time:
                    self.sleep(settle_time)
                return result
            if time.monotonic() >= deadline:
                if raise_if_not_found:
                    raise WaitFailedException('wait_until timed out')
                return None
            self.sleep(0.05)

    # -------------------------------------------------------------------- OCR
    def ocr(self, x1=None, y1=None, x2=None, y2=None, box=None, match=None,
            frame_processor=None, target_height=None, name=None, log=None, **kwargs):
        frame = self._ensure_frame()
        if frame is None:
            return []
        if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
            box = self.box_of_screen(x1, y1, x2, y2)
        if target_height:
            scale = target_height / frame.shape[0]
            frame = cv2.resize(frame, None, fx=scale, fy=scale)
            if box is not None:
                box = Box(box.x * scale, box.y * scale, box.width * scale, box.height * scale)
        if frame_processor is not None:
            frame = frame_processor(frame)
        return self._ocr.recognize(frame, box=box, match=match,
                                   cancelled=self.stop_event.is_set if self.stop_event else None)

    # ------------------------------------------------------------------ input
    def click(self, x=-1, y=-1, move_back=False, name=None, interval=-1,
              move=False, down_time=0.01, after_sleep=0, key='left', **kwargs):
        if self.controller is None or self._stopped():
            return None
        if isinstance(x, Box):
            px, py = x.center()
        elif x == -1 and y == -1:
            px, py = self.width // 2, self.height // 2
        else:
            px = int(x * self.width) if 0 <= x <= 1 else int(x)
            py = int(y * self.height) if 0 <= y <= 1 else int(y)
        if key == 'middle':
            with self.controller._input_lock:
                self.controller.middle_click()
        else:
            self.controller.tap(px, py)
        if after_sleep:
            self.sleep(after_sleep)
        return None

    def click_box(self, box, after_sleep=0, relative_x=0.5, **kwargs):
        return self.click(box.x + box.width * relative_x, box.center()[1],
                          after_sleep=after_sleep)

    def click_relative(self, x, y, hcenter=False, vcenter=False, after_sleep=0, **kwargs):
        return self.click(x, y, after_sleep=after_sleep)

    def middle_click(self, after_sleep=0, interval=-1, down_time=0.1, **kwargs):
        if self.controller is None or self._stopped():
            return None
        with self.controller._input_lock:
            self.controller.middle_click()
        if after_sleep:
            self.sleep(after_sleep)
        return None

    def move(self, x, y):
        if self.controller is None or self._stopped():
            return None
        sx, sy = self.controller.screenshot_to_screen(int(x), int(y))
        ctypes.windll.user32.SetCursorPos(sx, sy)
        return None

    def scroll_relative(self, x, y, amount, **kwargs):
        if self.controller is None or self._stopped():
            return None
        self.controller.wheel_at(int(x * self.width), int(y * self.height), int(amount * 120))
        return None

    def mouse_down(self, key='left'):
        if self.controller is None or self._stopped():
            return None
        flag = 0x0008 if key == 'right' else 0x0002
        with self.controller._input_lock:
            self.controller._send_mouse_button(flag)

    def mouse_up(self, key='left'):
        if self.controller is None:
            return None
        flag = 0x0010 if key == 'right' else 0x0004
        with self.controller._input_lock:
            self.controller._send_mouse_button(flag)

    def back(self, after_sleep=0, **kwargs):
        return self.send_key('esc', after_sleep=after_sleep)

    def input_text(self, value):
        return None

    @staticmethod
    def _key_name(key):
        if isinstance(key, int):
            return str(key)
        return str(key)

    def send_key(self, key, interval=-1, down_time=0.05, after_sleep=0, **kwargs):
        if self.controller is None or self._stopped():
            return None
        self.controller.press_key(self._key_name(key), max(1, int(down_time * 1000)))
        if interval and interval > 0:
            self.sleep(interval)
        if after_sleep:
            self.sleep(after_sleep)
        return None

    def send_key_down(self, key):
        if self.controller is None or self._stopped():
            return None
        vk = self.controller._virtual_key(self._key_name(key))
        self.controller._send_keyboard_event(vk, key_up=False)

    def send_key_up(self, key):
        if self.controller is None:
            return None
        vk = self.controller._virtual_key(self._key_name(key))
        self.controller._send_keyboard_event(vk, key_up=True)

    # -------------------------------------------------------------- utilities
    def calculate_color_percentage(self, color_dict, box):
        frame = self._ensure_frame()
        return color_percentage(frame, color_dict, box)

    def draw_boxes(self, *args, **kwargs):
        return None

    def screenshot(self, name, frame=None):
        if not self.debug:
            return None
        target_dir = Path(__file__).resolve().parents[1] / '_debug'
        target_dir.mkdir(exist_ok=True)
        safe = re.sub(r'[^\w\-]+', '_', str(name))[:80]
        frame = frame if frame is not None else self.frame
        if frame is not None:
            cv2.imwrite(str(target_dir / f'{safe}.png'), frame)
        return None

    def get_global_config(self, name):
        if name in self.config:
            return self.config
        return hotkeys.GLOBAL_CONFIG.get(name, {})

    def validate_config(self, key, value):
        return None

    def add_text_fix(self, fixes):
        self.text_fixes = dict(fixes)

    def start_device(self):
        return None

    def get_task_by_class(self, cls):
        return self if isinstance(self, cls) else None

    def close(self):
        if self._ocr is not None and hasattr(self._ocr, 'close'):
            self._ocr.close()


class TriggerTask(BaseTask):
    def run(self):
        return None


__all__ = [
    'BaseTask', 'TriggerTask', 'BaseScene', 'Box', 'Config', 'ConfigOption', 'Icon',
    'FindFeature', 'Logger', 'og', 'get_path_relative_to_exe', 'run_task',
    'TaskDisabledException', 'CannotFindException', 'WaitFailedException',
    'find_boxes_by_name', 'find_boxes_within_boundary', 'get_bounding_box',
    'sort_boxes', 'find_color_rectangles', 'get_mask_in_color_range',
    'color_range_to_bound', 'calculate_color_percentage', 'mask_white',
    'is_pure_black', 'safe_get',
]
