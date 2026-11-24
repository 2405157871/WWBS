"""ok-script compatible template matching backed by OpenCV.

Templates are the original okww PNG assets.  Their file names carry the
resolution they were captured at: ``<name>_<w>x<h>_<x>_<y>.png``.  Both the
frame and the template are normalised to a common matching height before
``cv2.matchTemplate`` so that assets captured at 2160p also work at 1080p.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

from .box import Box

_TEMPLATE_NAME = re.compile(r'^(?P<name>.+)_(?P<w>\d+)x(?P<h>\d+)_(?P<x>\d+)_(?P<y>\d+)\.png$', re.I)


@dataclass(frozen=True)
class TemplateEntry:
    name: str
    path: Path
    src_w: int
    src_h: int
    x: int
    y: int


def _as_name(value):
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


class TemplateMatcher:
    def __init__(self, template_dir: Path | str | None = None):
        self.template_dir = Path(template_dir) if template_dir else (
            Path(__file__).resolve().parents[2] / 'assets' / 'okww_templates'
        )
        self._index: dict[str, list[TemplateEntry]] | None = None

    @property
    def index(self):
        if self._index is None:
            entries: dict[str, list[TemplateEntry]] = {}
            if self.template_dir.is_dir():
                for path in self.template_dir.glob('*.png'):
                    match = _TEMPLATE_NAME.match(path.name)
                    if not match:
                        continue
                    entry = TemplateEntry(
                        match.group('name'), path,
                        int(match.group('w')), int(match.group('h')),
                        int(match.group('x')), int(match.group('y')),
                    )
                    entries.setdefault(entry.name, []).append(entry)
            self._index = entries
        return self._index

    def has_template(self, name) -> bool:
        return _as_name(name) in self.index

    def get_box_by_name(self, name, width, height) -> Box | None:
        entries = self.index.get(_as_name(name))
        if not entries or not width or not height:
            return None
        aspect = width / height
        entry = min(entries, key=lambda e: abs(e.src_w / e.src_h - aspect))
        mat = self._load_mat(entry)
        scale_x = width / entry.src_w
        scale_y = height / entry.src_h
        return Box(entry.x * scale_x, entry.y * scale_y,
                   mat.shape[1] * scale_x, mat.shape[0] * scale_y, name=entry.name)

    def get_feature_by_name(self, name):
        entry = self._preferred_entry(_as_name(name), 16 / 9)
        return SimpleNamespace(mat=self._load_mat(entry), name=entry.name) if entry else None

    def _preferred_entry(self, name, aspect):
        entries = self.index.get(name)
        if not entries:
            return None
        return min(entries, key=lambda e: abs(e.src_w / e.src_h - aspect))

    @staticmethod
    @lru_cache(maxsize=512)
    def _load_mat_cached(path: str) -> np.ndarray:
        mat = cv2.imread(path, cv2.IMREAD_COLOR)
        if mat is None:
            raise FileNotFoundError(path)
        return mat

    def _load_mat(self, entry: TemplateEntry) -> np.ndarray:
        mat = self._load_mat_cached(str(entry.path))
        try:
            from wwbs_combat.task.process_feature import process_feature
            feature = SimpleNamespace(mat=mat)
            process_feature(entry.name, feature)
            mat = feature.mat
        except (ImportError, AttributeError):
            pass
        return mat

    @staticmethod
    def _resize(mat, scale):
        if scale <= 0 or abs(scale - 1.0) < 1e-6:
            return mat
        return cv2.resize(mat, None, fx=scale, fy=scale,
                          interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)

    @classmethod
    def _scale_template(cls, mat, entry, match_height):
        # Template pixel size is a crop of its capture frame; the filename's
        # source resolution determines the scale, not the crop's own height.
        return cls._resize(mat, match_height / entry.src_h)

    def _resolve_box(self, box, frame, width, height):
        if box is None:
            return Box(0, 0, frame.shape[1], frame.shape[0])
        if isinstance(box, str):
            return self.get_box_by_name(box, width, height) or Box(0, 0, frame.shape[1], frame.shape[0])
        return box

    def find_one(self, name, frame, box=None, threshold=0.8, target_height=None,
                 frame_processor=None, template=None, horizontal_variance=0.002,
                 vertical_variance=0.002) -> Box | None:
        if frame is None or frame.size == 0:
            return None
        is_collection = hasattr(name, '__iter__') and not isinstance(name, (str, bytes))
        originals = list(name) if is_collection else [name]
        names = [_as_name(item) for item in originals]
        original_by_name = dict(zip(names, originals))
        region = self._resolve_box(box, frame, frame.shape[1], frame.shape[0])
        crop = region.crop_frame(frame)
        if crop.size == 0:
            return None

        match_height = target_height or frame.shape[0]
        frame_scale = match_height / frame.shape[0]
        crop_scaled = self._resize(crop, frame_scale)
        if frame_processor is not None:
            crop_scaled = frame_processor(crop_scaled)

        candidates = []
        if template is not None:
            candidates.append((None, template))
        else:
            aspect = crop.shape[1] / crop.shape[0]
            for feature_name in names:
                entry = self._preferred_entry(feature_name, aspect)
                if entry is not None:
                    candidates.append((feature_name, self._scale_template(self._load_mat(entry), entry, match_height)))

        best = None
        for feature_name, templ in candidates:
            if templ.size == 0 or crop_scaled.shape[0] < templ.shape[0] or crop_scaled.shape[1] < templ.shape[1]:
                continue
            result = cv2.matchTemplate(crop_scaled, templ, cv2.TM_CCOEFF_NORMED)
            _, score, _, (px, py) = cv2.minMaxLoc(result)
            if score < threshold:
                continue
            if best is None or score > best.confidence:
                x = region.x + px / frame_scale
                y = region.y + py / frame_scale
                found = Box(x, y, templ.shape[1] / frame_scale, templ.shape[0] / frame_scale,
                            name=original_by_name.get(feature_name, feature_name or name))
                found.confidence = float(score)
                best = found
        return best

    def find_best_match_in_box(self, box, names, threshold=0.6, target_height=None,
                               frame=None) -> Box | None:
        if frame is None:
            return None
        return self.find_one(names, frame, box=box, threshold=threshold,
                             target_height=target_height)

    def find_feature(self, name, frame, box=None, threshold=0.8, target_height=None) -> list[Box]:
        if frame is None or frame.size == 0:
            return []
        feature_name = _as_name(name)
        region = self._resolve_box(box, frame, frame.shape[1], frame.shape[0])
        crop = region.crop_frame(frame)
        if crop.size == 0:
            return []
        match_height = target_height or frame.shape[0]
        frame_scale = match_height / frame.shape[0]
        crop_scaled = self._resize(crop, frame_scale)
        found: list[Box] = []
        for entry in self.index.get(feature_name, ()):
            templ = self._scale_template(self._load_mat(entry), entry, match_height)
            if crop_scaled.shape[0] < templ.shape[0] or crop_scaled.shape[1] < templ.shape[1]:
                continue
            result = cv2.matchTemplate(crop_scaled, templ, cv2.TM_CCOEFF_NORMED)
            ys, xs = np.where(result >= threshold)
            for y, x in zip(ys, xs):
                box = Box(region.x + x / frame_scale, region.y + y / frame_scale,
                          templ.shape[1] / frame_scale, templ.shape[0] / frame_scale,
                          name=feature_name)
                box.confidence = float(result[y, x])
                found.append(box)
        found.sort(key=lambda b: b.confidence, reverse=True)
        kept: list[Box] = []
        for candidate in found:
            overlap = False
            for box_kept in kept:
                ix = min(candidate.x + candidate.width, box_kept.x + box_kept.width) - max(candidate.x, box_kept.x)
                iy = min(candidate.y + candidate.height, box_kept.y + box_kept.height) - max(candidate.y, box_kept.y)
                if ix > 0 and iy > 0 and ix * iy > 0.5 * min(candidate.width * candidate.height,
                                                             box_kept.width * box_kept.height):
                    overlap = True
                    break
            if not overlap:
                kept.append(candidate)
        return kept
