"""Offline checks for the ported okww image-recognition combat layer."""
import unittest
from unittest.mock import Mock

import numpy as np

from wwbs_combat import VisionCombatRunner
from wwbs_combat.ok_compat import Box
from wwbs_combat.scene.WWScene import WWScene
from wwbs_combat.task.AutoCombatTask import AutoCombatTask
from wwbs_combat.task.BaseCombatTask import convert_cd
from wwbs_combat.char.BaseChar import BaseChar
from wwbs_combat.char.CharFactory import char_names


class FakeOcr:
    def recognize(self, frame, box=None, match=None, cancelled=None):
        width = frame.shape[1]
        return [
            Box(width * 0.84, 930, 30, 18, name='12.3'),
            Box(width * 0.89, 930, 30, 18, name='5.6'),
            Box(width * 0.94, 930, 30, 18, name='2.1'),
        ]

    def close(self):
        pass


class VisionShimTests(unittest.TestCase):
    def test_all_character_rotations_are_registered(self):
        self.assertGreaterEqual(len(char_names), 50)
        task = AutoCombatTask()
        self.assertTrue(issubclass(AutoCombatTask, object))
        task.close()

    def test_box_geometry(self):
        box = Box(100, 200, 40, 60, name='skill')
        self.assertEqual(box.center(), (120, 230))
        scaled = box.scale(2)
        self.assertEqual((scaled.x, scaled.width, scaled.center()), (80, 80, (120, 230)))
        copied = box.copy(x_offset=10, height_offset=-20, name='copy')
        self.assertEqual((copied.x, copied.height, copied.name), (110, 40, 'copy'))
        frame = np.zeros((400, 300, 3), dtype=np.uint8)
        self.assertEqual(box.crop_frame(frame).shape, (60, 40, 3))

    def test_template_matching_from_asset(self):
        task = AutoCombatTask()
        matcher = task._matcher
        entry = matcher._preferred_entry('char_1_text', 1920 / 1080)
        self.assertIsNotNone(entry)
        template = matcher._load_mat(entry)
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        frame[200:200 + template.shape[0], 300:300 + template.shape[1]] = template
        found = matcher.find_one('char_1_text', frame, threshold=0.8)
        self.assertIsNotNone(found)
        self.assertGreaterEqual(found.confidence, 0.8)
        self.assertLess(abs(found.x - 300), 3)
        self.assertLess(abs(found.y - 200), 3)

    def test_cd_reading_uses_ocr_results(self):
        task = AutoCombatTask(ocr_backend=FakeOcr())
        task.scene = WWScene()
        task.frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        task.width, task.height = 1920, 1080
        char = BaseChar(task, 0, char_name='test')
        char.is_current_char = True
        task.chars = [char]
        task.refresh_cd()
        cds = task.cds[0]
        self.assertEqual(cds['resonance'], 12.3)
        self.assertEqual(cds['echo'], 5.6)
        self.assertEqual(cds['liberation'], 2.1)
        self.assertEqual(convert_cd(Box(0, 0, 1, 1, name='CD 7.5')), 7.5)
        remaining = task.get_cd('resonance')
        self.assertLessEqual(remaining, 12.3)
        self.assertGreaterEqual(remaining, 11.5)

    def test_vision_runner_is_safe_without_a_controller(self):
        runner = VisionCombatRunner(Mock(capture_frame=Mock(return_value=None)))
        self.assertFalse(runner.run())


if __name__ == '__main__':
    unittest.main()
