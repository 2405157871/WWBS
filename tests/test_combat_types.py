"""Each battle mode picks how it fights: the axis, or screen-reading combat."""
import json
import tempfile
import threading
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import app
import local_settings as settings
from app import DAILY_ZONE_NAMES
from combat_rotation import COMBAT_MODES, default_store, load_store, save_store, validate_store
from combat_seed import decode_seed, import_seed
from tasks.models import Step, TaskNeedsReview, WeeklyTask


SEED = '【默认战斗轴】WWBS4.AYv-g9l9L0bsvLcDxGNgYJADqmARcmDQYGRhZcShDADWKANg'
AXIS = {mode: 'axis' for mode in COMBAT_MODES}


def legacy_store():
    store = validate_store(default_store())
    del store['combat_types']
    return store


class CombatTypeStoreTests(unittest.TestCase):
    def test_new_and_legacy_settings_fight_with_the_axis(self):
        self.assertEqual(validate_store(default_store())['combat_types'], AXIS)
        checked = validate_store(legacy_store())
        self.assertEqual(checked['combat_types'], AXIS)
        self.assertEqual(checked['modes'], validate_store(default_store())['modes'])

    def test_unknown_combat_type_is_rejected(self):
        for value, message in (('magic', '战斗方式无效'), (['vision'], '战斗方式配置格式错误')):
            with self.subTest(value=value):
                store = legacy_store()
                store['combat_types'] = {'daily': value} if isinstance(value, str) else value
                with self.assertRaisesRegex(ValueError, message):
                    validate_store(store)

    def test_combat_types_survive_saving_and_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'axis.json'
            store = validate_store(default_store())
            store['combat_types']['tower'] = 'vision'
            save_store(path, store)
            loaded = load_store(path)
            self.assertEqual(loaded['combat_types'], {'daily': 'axis', 'combat_4c': 'axis', 'tower': 'vision'})
            self.assertEqual(loaded['modes'], store['modes'])


class CombatTypeRunnerTests(unittest.TestCase):
    def runner(self, combat_types=None, *, dry_run=False, notice=None):
        controller = Mock()
        controller.normalize_input_binding = lambda value: value
        return app.TaskRunner(controller, Mock(), dry_run=dry_run, notice=notice,
                              combat_types=combat_types)

    def test_modes_default_to_the_axis(self):
        self.assertEqual({mode: self.runner().combat_type(mode) for mode in COMBAT_MODES}, AXIS)
        self.assertEqual(self.runner().combat_type('unknown'), 'axis')
        self.assertEqual(self.runner({'daily': 'bogus'}).combat_type('daily'), 'axis')
        self.assertEqual(self.runner({'daily': 'vision'}).combat_type('daily'), 'vision')
        self.assertEqual(self.runner({'daily': 'vision'}).combat_type('tower'), 'axis')

    def test_axis_never_raises_or_notifies(self):
        notice = Mock()
        for mode in COMBAT_MODES:
            self.assertIsNone(self.runner(notice=notice)._check_combat_type(mode))
        notice.assert_not_called()

    def test_vision_stops_before_any_input_and_is_not_reported_as_done(self):
        for mode, start in (('combat_4c', '_run_4c_combat'), ('tower', '_run_tower_challenge'),
                            ('daily', '_run_daily_routine')):
            with self.subTest(mode=mode):
                runner = self.runner({mode: 'vision'}, notice=Mock())
                runner._run_4c_battle, runner._approach_tower_start, runner._open_daily_tacet_field = (
                    Mock(), Mock(), Mock())
                runner.daily_zone_name = DAILY_ZONE_NAMES[0]
                step = Mock(timeout=1200) if mode != 'daily' else Step(action='daily_routine')
                with self.assertRaisesRegex(TaskNeedsReview, '图像识别战斗'):
                    getattr(runner, start)(step)
                runner.notice.assert_called_once()
                runner._run_4c_battle.assert_not_called()
                runner._approach_tower_start.assert_not_called()
                runner._open_daily_tacet_field.assert_not_called()
                for name in ('press_key', 'press_binding', 'left_click', 'middle_click', 'press_keys'):
                    getattr(runner.controller, name).assert_not_called()

    def test_dry_run_reports_vision_without_a_dialog(self):
        runner = self.runner({'combat_4c': 'vision'}, dry_run=True, notice=Mock())
        with self.assertRaises(TaskNeedsReview):
            runner._run_4c_combat(Mock(timeout=1200))
        runner.notice.assert_not_called()
        runner.log.assert_any_call('    4C 刷取已选择图像识别战斗，但该功能尚未实现，任务未完成。')

    def test_axis_mode_still_reaches_the_battle_loop(self):
        runner = self.runner({'tower': 'vision'}, dry_run=False)
        runner.max_cycles = 1
        runner._run_4c_battle, runner._collect_4c_reward, runner._restart_4c_challenge = Mock(), Mock(), Mock()
        runner._run_4c_combat(Mock(timeout=1200))
        runner._run_4c_battle.assert_called_once()


class CombatTypeCompatibilityTests(unittest.TestCase):
    def test_seed_import_keeps_combat_types_and_seeds_carry_none(self):
        imported, _identity = import_seed(legacy_store(), SEED)
        self.assertEqual(imported['combat_types'], AXIS)
        store = validate_store(default_store())
        store['combat_types']['daily'] = 'vision'
        imported, _identity = import_seed(store, SEED)
        self.assertEqual(imported['combat_types'], {'daily': 'vision', 'combat_4c': 'axis', 'tower': 'axis'})
        self.assertNotIn('combat_types', decode_seed(SEED))

    def test_settings_from_an_older_installation_inherit_as_axis(self):
        chosen = validate_store(default_store())
        chosen['combat_types']['daily'] = 'vision'
        for value, expected in ((legacy_store(), AXIS), (chosen, chosen['combat_types'])):
            with self.subTest(expected=expected):
                # Older installations never wrote this field.
                raw = json.loads(json.dumps(value, ensure_ascii=False))
                raw.pop('version', None)
                self.assertEqual(settings.convert_settings('combat-presets.json', raw)['combat_types'], expected)


class CombatTypeUiTests(unittest.TestCase):
    def build_ui(self, root):
        window = app.App.__new__(app.App)
        window.root = root
        window.rotation_store = default_store()
        window.rotation_choice = tk.StringVar()
        window.rotation_status = tk.StringVar()
        window.rotation_tab = tk.Frame(root, bg=app.COLORS['panel'])
        window.rotation_tab.pack(fill=tk.BOTH, expand=True)
        root.geometry('1050x800')
        window._build_rotation_tab()
        root.update()
        return window

    @staticmethod
    def texts(widget):
        for child in widget.winfo_children():
            if 'text' in child.keys():
                yield child.cget('text')
            yield from CombatTypeUiTests.texts(child)

    def test_each_mode_can_choose_a_combat_type_and_it_is_saved(self):
        root = tk.Tk()
        try:
            with tempfile.TemporaryDirectory() as directory, patch.object(
                    app, 'COMBAT_PRESETS_CONFIG', Path(directory)/'combat.json'):
                window = self.build_ui(root)
                self.assertEqual(set(window.rotation_combat_type_choices), set(COMBAT_MODES))
                self.assertNotIn('图像识别战斗尚未实现', ''.join(self.texts(window.rotation_modes_parent)))
                window.rotation_combat_type_choices['tower'].set('图像识别')
                window._rotation_assign_combat_type('tower')
                saved = load_store(app.COMBAT_PRESETS_CONFIG)
                self.assertEqual(saved['combat_types'], {'daily': 'axis', 'combat_4c': 'axis', 'tower': 'vision'})
                self.assertEqual(saved['modes'], validate_store(default_store())['modes'])
                self.assertIn('深塔挑战的战斗方式：图像识别', window.rotation_status.get())
                self.assertIn('图像识别战斗尚未实现', ''.join(self.texts(window.rotation_modes_parent)))
                window.rotation_combat_type_choices['tower'].set('轴战斗')
                window._rotation_assign_combat_type('tower')
                self.assertEqual(load_store(app.COMBAT_PRESETS_CONFIG)['combat_types'], AXIS)
                self.assertNotIn('图像识别战斗尚未实现', ''.join(self.texts(window.rotation_modes_parent)))
        finally:
            root.destroy()

    def test_failed_save_restores_the_previous_combat_type(self):
        root = tk.Tk()
        try:
            window = self.build_ui(root)
            window._rotation_save = Mock(return_value=True)
            window._rotation_save_new_structure = Mock(return_value=False)
            window.rotation_combat_type_choices['daily'].set('图像识别')
            window._rotation_assign_combat_type('daily')
            self.assertEqual(window.rotation_store['combat_types'], AXIS)
            self.assertEqual(window.rotation_combat_type_choices['daily'].get(), '轴战斗')
        finally:
            root.destroy()

    def test_starting_a_task_logs_the_chosen_combat_type(self):
        root = tk.Tk()
        try:
            with tempfile.TemporaryDirectory() as directory, patch.object(
                    app, 'COMBAT_PRESETS_CONFIG', Path(directory)/'combat.json'):
                window = self.build_ui(root)
                window.worker = None
                window.max_cycles = None
                window.dry_run = tk.BooleanVar(root, value=False)
                window.stop_event = threading.Event()
                window._ensure_admin_for_real_run = Mock(return_value=True)
                window._pet_feedback, window._event_line, window._set_pet_working, window._log = (
                    Mock(), Mock(return_value='start'), Mock(), Mock())
                window.template_status = tk.StringVar()
                window.rotation_store['combat_types']['tower'] = 'vision'
                task = WeeklyTask(name='深塔挑战', template_group='tower',
                                  steps=[Step(action='tower_challenge')])
                with patch.object(app.threading, 'Thread') as thread:
                    window._start_worker([task])
                thread.return_value.start.assert_called_once()
                self.assertEqual(window._rotation_run_store['combat_types']['tower'], 'vision')
                logged = [call.args[0] for call in window._log.call_args_list]
                self.assertTrue(any('深塔挑战战斗方式：图像识别' in line for line in logged), logged)
        finally:
            root.destroy()
