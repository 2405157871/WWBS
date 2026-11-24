"""ok-script compatibility layer for the ported okww combat code."""
from .box import (
    Box, color_range_to_bound, find_boxes_by_name, find_boxes_within_boundary,
    find_color_rectangles, get_bounding_box, get_mask_in_color_range,
    is_pure_black, mask_white, safe_get, sort_boxes,
)
from .ocr import OcrBackend, OnnxOcrBackend, WindowsOcrBackend
from .task_shim import (
    BaseScene, BaseTask, CannotFindException, Config, ConfigOption, FindFeature,
    Icon, Logger, TaskDisabledException, TriggerTask, WaitFailedException,
    calculate_color_percentage, get_path_relative_to_exe, og, run_task,
)

__all__ = [
    'BaseScene', 'BaseTask', 'TriggerTask', 'Box', 'Config', 'ConfigOption',
    'Icon', 'FindFeature', 'Logger', 'og', 'get_path_relative_to_exe', 'run_task',
    'TaskDisabledException', 'CannotFindException', 'WaitFailedException',
    'find_boxes_by_name', 'find_boxes_within_boundary', 'get_bounding_box',
    'sort_boxes', 'find_color_rectangles', 'get_mask_in_color_range',
    'color_range_to_bound', 'calculate_color_percentage', 'mask_white',
    'is_pure_black', 'safe_get', 'OcrBackend', 'OnnxOcrBackend',
    'WindowsOcrBackend',
]
