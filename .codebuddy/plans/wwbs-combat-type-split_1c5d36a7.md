---
name: wwbs-combat-type-split
overview: 为 WWBS 增加"战斗方式"分类（轴战斗 / 图像识别），按 4C、日常、深塔三种模式分别选择并保存；本次只搭分类的存储、界面、启动快照和执行入口分流，图像识别本身不实现，选中它的模式在执行到战斗步骤时提示并停止。
todos:
  - id: store-combat-types
    content: 在 combat_rotation.py 增加 COMBAT_TYPES 并让 validate_store 输出 combat_types
    status: completed
  - id: runner-dispatch
    content: 给 TaskRunner 增加 combat_types 入参和 combat_type、_combat_type_unavailable 方法
    status: completed
    dependencies:
      - store-combat-types
  - id: battle-entry-guards
    content: 在 4C、日常、深塔三个战斗入口按模式分流，图像识别时提示并停止
    status: completed
    dependencies:
      - runner-dispatch
  - id: ui-and-startup
    content: 在排轴页每个模式下增加战斗方式选择，启动时写入日志并传给 TaskRunner
    status: completed
    dependencies:
      - store-combat-types
  - id: tests-and-regression
    content: 新增 tests/test_combat_types.py，跑 ruff 与完整测试回归
    status: completed
    dependencies:
      - battle-entry-guards
      - ui-and-startup
---

## 产品概览
在 WWBS 的战斗排轴页增加"战斗方式"分类：轴战斗（现有排轴）和图像识别。本次只把分类的保存、界面、启动快照和执行入口分流做出来，图像识别战斗本身不实现。

## 核心功能
- 战斗排轴页的三种模式（4C 刷取、一键日常、深塔挑战）各自多一个"战斗方式"选择：轴战斗 / 图像识别，默认轴战斗，随 `combat-presets.json` 保存。
- 启动任务时，日志写出本次涉及的每个模式使用的战斗方式。
- 选了图像识别的模式，执行到战斗步骤时写日志并弹窗提示"图像识别战斗尚未实现"，然后停止该战斗步骤，不回退到轴战斗，不发送任何按键。
- 现有轴战斗行为、预设分配、种子导入导出、本地设置继承全部保持不变；旧版本保存的设置没有该字段时按轴战斗处理。


## 技术栈
沿用项目现有实现：Python + tkinter（界面）、`unittest`（测试）、`ruff`（`ruff.toml`）。不引入新依赖，不新增文档文件。

## 实现方案
分类存放在排轴配置 `store` 的**新顶层字段** `combat_types`，按模式取值 `"axis"` 或 `"vision"`。不放进现有 `modes` 字典，也不给预设加字段，原因：
- 现有测试对 `store['modes']` 做整字典相等断言（`tests/test_combat_rotation.py:326`、`tests/test_combat_seed.py:109,257`、`tests/test_tower_challenge.py:160` 等），往里加键会全部失败。
- 旧版程序读取新文件时会忽略未知顶层字段，向前兼容。
- 种子只编码单个预设，`combat_seed.py` 文件头的兼容契约要求不改编解码，分类与预设解耦后种子完全不受影响。

执行侧在 `TaskRunner` 增加 `combat_types` 入参与统一判断方法，三个战斗入口在进入战斗前分流。图像识别分支只有一个"提示并停止"的占位实现，后续实现图像识别时在该分支接入即可，轴战斗代码路径不动。

## 执行注意事项（已核对的调用关系）
- **日常不能在 `_run_daily_battle` 里拦截**：`tasks/daily_154.py:613-618` 是 `while not stop: _run_daily_battle(...); if _collect_daily_reward(...): break`，若战斗直接 return，外层会无限循环找奖励。拦截点放在 `_run_daily_routine`（`tasks/daily_154.py:573`）的干运行分支之后、`_open_daily_tacet_field` 之前，整个日常步骤停止，不会进本后卡住。
- **4C**：拦截点放在 `_run_4c_combat`（`tasks/combat_4c.py:20`）的干运行分支和 `boss_challenge.enter` 之前，避免战歌重奏先走进副本。
- **深塔**：拦截点放在 `_run_tower_challenge`（`tasks/other.py:101`）的干运行分支之后、`_approach_tower_start` 之前。
- `tasks/weekly_150.py:121-124` 的周常分发器调用的是同一批 `_run_4c_combat` / `_run_daily_routine`，自动覆盖。
- 停止采用直接 `return`（与干运行一致），不抛异常；此时没有按键被按下，不需要释放按键。真实执行时调用 `self.notice` 弹窗，干运行只写日志。
- `RotationClock` 只在 `tasks/combat_4c.py:101`、`tasks/other.py:141`、`tasks/other.py:978` 三处构造，分流完成后再也不会为图像识别模式构造时钟。
- `load_store` 里旧默认轴的迁移逻辑、`default_store()`、`import_seed` 一律不改；`import_seed` 首尾都经过 `validate_store`，分类会自动保留。
- `local_settings.py` 的 `convert_settings` 对 `combat-presets.json` 直接走 `validate_store`，旧版本目录缺少该字段时自动补为轴战斗，无需改代码。
- `TaskRunner` 大量在测试中直接构造且不传新参数，新参数必须带默认值 `None` 并按轴战斗处理；`tests/test_tower_challenge.py:85` 等直接给 `runner.rotation_presets` 赋值的写法也要继续可用。

## 目录结构
```
e:/PythonProject/WWBS/
├── combat_rotation.py                 # [MODIFY] 新增 COMBAT_TYPES 常量；validate_store 输出新增顶层 combat_types（缺失时每个模式默认 "axis"，未知值抛中文 ValueError）；default_store 同步带上该字段
├── app.py                             # [MODIFY] _rotation_refresh_modes 每列预设下方增加"战斗方式"选择；新增 _rotation_assign_combat_type（复用 _rotation_save_new_structure，失败回滚并刷新）；启动日志写出各模式战斗方式；TaskRunner(...) 增传 combat_types
├── tasks/runner.py                    # [MODIFY] TaskRunner.__init__ 新增 combat_types 入参（默认 None）；新增 combat_type(mode) 与 _combat_type_unavailable(mode)（写日志、真实执行时 notice 弹窗、返回 True）
├── tasks/combat_4c.py                 # [MODIFY] _run_4c_combat 开头按 "combat_4c" 分流，图像识别时提示并 return
├── tasks/other.py                     # [MODIFY] _run_tower_challenge 开头按 "tower" 分流，图像识别时提示并 return
├── tasks/daily_154.py                 # [MODIFY] _run_daily_routine 在打开无音区之前按 "daily" 分流，图像识别时提示并 return
└── tests/test_combat_types.py         # [NEW] 分类的存储、界面、启动快照与三处入口分流的回归测试
```

## 关键结构
```python
# combat_rotation.py
COMBAT_TYPES = {"axis": "轴战斗", "vision": "图像识别"}
# validate_store(raw) 返回值新增：
#   "combat_types": {mode: "axis" | "vision" for mode in COMBAT_MODES}

# tasks/runner.py
class TaskRunner:
    def __init__(self, ..., combat_types: dict[str, str] | None = None): ...
    def combat_type(self, mode: str) -> str: ...            # 未知模式或缺省返回 "axis"
    def _combat_type_unavailable(self, mode: str) -> bool:  # 图像识别未实现：提示并返回 True
        ...
```

## 验证
- 新增测试覆盖：`旧配置无字段时默认轴战斗`；未知值报错；保存与读取往返；界面选择保存及保存失败回滚；`TaskRunner` 未传参时默认轴战斗；三种模式选图像识别时入口提示并停止、控制器未收到任何按键；选轴战斗时三处入口行为不变；导入历史种子后 `combat_types` 不变；本地设置继承旧目录配置。
- 回归 `tests/test_combat_rotation.py`、`test_combat_seed.py`、`test_tower_challenge.py`、`test_local_settings.py`、`test_default_axis.py`、`test_role_cards.py`、`test_seed_compatibility.py`、`test_settings_startup.py`、`test_daily_routine.py`，然后跑完整 `tests` 目录。
- 解释器用 `e:\PythonProject\WWBS\.venv\Scripts\python.exe`（`python` 不在 PATH），改完运行 `ruff`。

