"""Default game hotkeys and global config used by the ported okww tasks."""
from __future__ import annotations

GAME_HOTKEY = {
    'Echo Key': 'q',
    'Liberation Key': 'r',
    'Resonance Key': 'e',
    'Tool Key': 't',
    'Jump Key': 'space',
    'Dodge Key': 'lshift',
    'Wheel Key': 'tab',
    'Guidebook Key': 'f2',
    'Bag Key': 'b',
}

CHARACTER_CONFIG = {
    'Iuno C6': False,
    'Roccia C6': False,
    'Chisa DPS': False,
    'Suoming DPS': False,
}

MONTHLY_CARD_CONFIG = {
    'Check Monthly Card': False,
    'Monthly Card Time': 4,
}

GLOBAL_CONFIG = {
    'Game Hotkey': GAME_HOTKEY,
    'Character Config': CHARACTER_CONFIG,
    'Monthly Card Config': MONTHLY_CARD_CONFIG,
}
