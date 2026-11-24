"""Ported ok-wuthering-waves image-recognition combat for WWBS.

Public entry point: :class:`VisionCombatRunner`.  It drives the original okww
combat state machine through the ``ok_compat`` shim, using WWBS's game window
controller for both capture and input.
"""
from __future__ import annotations

import threading

text_white_color = {
    'r': (244, 255),
    'g': (244, 255),
    'b': (244, 255),
}

__all__ = ['VisionCombatRunner', 'text_white_color']


class VisionCombatRunner:
    """Runs one closed-loop okww combat session in the caller's thread."""

    def __init__(self, controller, stop_event=None, *, ocr_backend=None,
                 template_dir=None, debug=False, options=None):
        self.controller = controller
        self.stop_event = stop_event or threading.Event()
        self.ocr_backend = ocr_backend
        self.template_dir = template_dir
        self.debug = debug
        self.options = options or {}
        self.task = None

    def _create_task(self):
        from wwbs_combat.scene.WWScene import WWScene
        from wwbs_combat.task.AutoCombatTask import AutoCombatTask

        task = AutoCombatTask(
            controller=self.controller,
            stop_event=self.stop_event,
            ocr_backend=self.ocr_backend,
            template_dir=self.template_dir,
            debug=self.debug,
        )
        task.scene = WWScene()
        if self.options.get('hotkeys'):
            task.key_config.update(self.options['hotkeys'])
        task.config.update({
            'Auto Target': self.options.get('auto_target', True),
            'Use Liberation': self.options.get('use_liberation', True),
            'Check Levitator': self.options.get('check_levitator', False),
            'Switch to Healer before and after Combat': self.options.get('switch_healer', False),
        })
        self.task = task
        return task

    def run(self) -> bool:
        task = self._create_task()
        try:
            task.next_frame()
            return bool(task.run())
        except Exception as exc:
            from wwbs_combat.ok_compat import TaskDisabledException
            if isinstance(exc, TaskDisabledException):
                return False
            task.logger.error(f'vision combat failed: {exc}')
            return False
        finally:
            task.close()

    def close(self):
        if self.task is not None:
            self.task.close()
