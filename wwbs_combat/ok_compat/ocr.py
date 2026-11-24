"""Pluggable OCR backends for the ported okww combat code.

The default backend reuses WWBS's local ``WindowsOcr`` helper (no extra model
download).  ``Box.name`` carries the recognised text, matching ok-script's OCR
result shape used by ``get_cd`` / ``convert_cd``.
"""
from __future__ import annotations

import logging
import re
import tempfile
from pathlib import Path
from typing import Protocol

import cv2

from .box import Box

logger = logging.getLogger(__name__)


class OcrBackend(Protocol):
    def recognize(self, frame, box: Box | None, match=None, cancelled=None) -> list[Box]: ...


class WindowsOcrBackend:
    """Uses Windows.Media.Ocr through the existing WWBS PowerShell worker."""

    def __init__(self, scale: int = 3):
        self.scale = scale
        self._ocr = None
        self._failed = False

    def _ensure(self):
        if self._ocr is None and not self._failed:
            try:
                from windows_ocr import WindowsOcr
                self._ocr = WindowsOcr()
            except Exception as exc:
                self._failed = True
                logger.warning('Windows OCR unavailable: %s', exc)
        return self._ocr

    @staticmethod
    def _normalise_text(text: str) -> str:
        for punctuation in ('·', '。', '，', '．', ',', ' '):
            text = text.replace(punctuation, '.') if punctuation != ' ' else text.replace(punctuation, '')
        return text.strip()

    @staticmethod
    def _coerce_cd(text: str, match) -> str:
        patterns = match if isinstance(match, (list, tuple)) else (match,)
        cd_like = any(hasattr(pattern, 'pattern') and '\\d' in pattern.pattern
                      and '\\.' in pattern.pattern for pattern in patterns)
        if cd_like and re.fullmatch(r'\d{2,3}', text):
            return text[:-1] + '.' + text[-1]
        return text

    @staticmethod
    def _matches(text: str, match) -> bool:
        if not match:
            return True
        patterns = match if isinstance(match, (list, tuple)) else (match,)
        for pattern in patterns:
            if isinstance(pattern, str) and pattern in text:
                return True
            if hasattr(pattern, 'search') and pattern.search(text):
                return True
        return False

    @staticmethod
    def _group_words(words):
        """Windows OCR splits '12.3' into separate words; regroup by gaps."""
        words = sorted(words, key=lambda word: float(word.get('x', 0)))
        groups: list[list[dict]] = []
        current: list[dict] = []
        for word in words:
            if current:
                previous = current[-1]
                gap = float(word.get('x', 0)) - (float(previous.get('x', 0)) + float(previous.get('width', 0)))
                widths = [float(item.get('width', 0)) for item in current + [word]] or [1]
                if gap > max(8, 0.8 * sorted(widths)[len(widths) // 2]):
                    groups.append(current)
                    current = []
            current.append(word)
        if current:
            groups.append(current)
        return groups

    def recognize(self, frame, box: Box | None = None, match=None, cancelled=None) -> list[Box]:
        ocr = self._ensure()
        if ocr is None or frame is None or frame.size == 0:
            return []
        crop = box.crop_frame(frame) if box is not None else frame
        if crop.size == 0:
            return []
        offset_x, offset_y = (int(box.x), int(box.y)) if box is not None else (0, 0)
        enlarged = cv2.resize(crop, None, fx=self.scale, fy=self.scale, interpolation=cv2.INTER_CUBIC)
        path = Path(tempfile.gettempdir()) / 'wwbs_vision_ocr.png'
        try:
            cv2.imwrite(str(path), enlarged)
            lines = ocr.recognize(path, cancelled=cancelled or (lambda: False), timeout=6)
        except Exception as exc:
            logger.debug('OCR recognition failed: %s', exc)
            return []
        results: list[Box] = []
        for line in lines or ():
            for group in self._group_words(line.get('words', ())):
                text = self._coerce_cd(
                    self._normalise_text(''.join(str(word.get('text', '')) for word in group)), match)
                if not text or not self._matches(text, match):
                    continue
                x = min(float(word.get('x', 0)) for word in group)
                y = min(float(word.get('y', 0)) for word in group)
                x2 = max(float(word.get('x', 0)) + float(word.get('width', 0)) for word in group)
                y2 = max(float(word.get('y', 0)) + float(word.get('height', 0)) for word in group)
                found = Box(offset_x + x / self.scale, offset_y + y / self.scale,
                            (x2 - x) / self.scale, (y2 - y) / self.scale, name=text)
                found.confidence = 1.0
                results.append(found)
        return results

    def close(self):
        if self._ocr is not None:
            try:
                self._ocr.close()
            except Exception:
                pass
            self._ocr = None


class OnnxOcrBackend:
    """Reserved slot for an ``onnxocr-ppocrv6`` backend.

    Not used by default: WWBS already ships ``WindowsOcr`` and the CD digits are
    small enough that a local OCR engine is sufficient.  Inject any object with
    ``recognize(frame, box, match, cancelled)`` via ``BaseTask(ocr_backend=...)``.
    """

    def __init__(self, recognizer=None):
        self.recognizer = recognizer

    def recognize(self, frame, box=None, match=None, cancelled=None):
        if self.recognizer is None:
            return []
        return self.recognizer(frame, box, match, cancelled)

    def close(self):
        pass


__all__ = ['OcrBackend', 'WindowsOcrBackend', 'OnnxOcrBackend', 'Box', 're']
