"""Chinese display names for the ported okww character rotations.

Source: okww ``i18n/zh_CN/LC_MESSAGES/ok.po`` (gettext msgid = official English
name), with the class-name remapping from okww ``BaseCombatTask.mismatched_names``.
``Qingxiao`` comes from the okww Chinese changelog; names absent from okww's
translations fall back to their English class name.
"""
from __future__ import annotations

CHAR_NAMES_ZH = {
    'Aalto': '秋水',
    'Aemeath': '爱弥斯',
    'Augusta': '奥古斯塔',
    'Baizhi': '白芷',
    'Brant': '布兰特',
    'Calcharo': '卡卡罗',
    'Camellya': '椿',
    'Cantarella': '坎特蕾拉',
    'Carlotta': '珂莱塔',
    'Cartethyia': '卡提希娅',
    'Changli': '长离',
    'Chisa': '千咲',
    'Chixia': '炽霞',
    'Ciaccona': '夏空',
    'Danjin': '丹瑾',
    'Denia': '达妮娅',
    'Douling': '卜灵',
    'Encore': '安可',
    'Galbrena': '嘉贝莉娜',
    'Hiyuki': '绯雪',
    'Hsin': '心',
    'Iuno': '尤诺',
    'Jianxin': '鉴心',
    'JingRan': '景燃',
    'Jinhsi': '今汐',
    'Jiyan': '忌炎',
    'Lily': '莉莉',
    'Lingyang': '凌阳',
    'Linnai': '琳奈',
    'Lucilla': '洛瑟菈',
    'Lucy': '露西',
    'Luhesi': '陆·赫斯',
    'Lumi': '灯灯',
    'Lupa': '露帕',
    'Mornye': '莫宁',
    'Mortefi': '莫特斐',
    'Phoebe': '菲比',
    'Phrolova': '弗洛洛',
    'Qingxiao': '清霄',
    'Qiuyuan': '仇远',
    'Rebecca': '丽贝卡',
    'Roccia': '洛可可',
    'Rover': '漂泊者',
    'Sanhua': '散华',
    'ShoreKeeper': '守岸人',
    'Suisui': '穗穗',
    'Suoming': '锁暝',
    'Taoqi': '桃祈',
    'Verina': '维里奈',
    'Xiangliyao': '相里要',
    'Xigelika': '西格莉卡',
    'YangYangSp': '秧秧·玄翎',
    'Yangyang': '秧秧',
    'Yinlin': '吟霖',
    'Youhu': '釉瑚',
    'Yuanwu': '渊武',
    'Zani': '赞妮',
    'Zhezhi': '折枝',
}


def character_display_name(cls) -> str:
    """Return the Chinese name for a character class, or its class name."""
    name = getattr(cls, '__name__', str(cls))
    return CHAR_NAMES_ZH.get(name, name)
