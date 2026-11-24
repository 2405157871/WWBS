from wwbs_combat.Labels import Labels
from wwbs_combat.char.Aemeath import Aemeath
from wwbs_combat.char.Aalto import Aalto
from wwbs_combat.char.Augusta import Augusta
from wwbs_combat.char.Baizhi import Baizhi
from wwbs_combat.char.BaseChar import BaseChar, CharType, Elements, get_default_buff_time
from wwbs_combat.char.Brant import Brant
from wwbs_combat.char.Calcharo import Calcharo
from wwbs_combat.char.Camellya import Camellya
from wwbs_combat.char.Cantarella import Cantarella
from wwbs_combat.char.Carlotta import Carlotta
from wwbs_combat.char.Cartethyia import Cartethyia
from wwbs_combat.char.Changli import Changli
from wwbs_combat.char.Chisa import Chisa
from wwbs_combat.char.Chixia import Chixia
from wwbs_combat.char.Ciaccona import Ciaccona
from wwbs_combat.char.Danjin import Danjin
from wwbs_combat.char.Denia import Denia
from wwbs_combat.char.Douling import Douling
from wwbs_combat.char.Encore import Encore
from wwbs_combat.char.Galbrena import Galbrena
from wwbs_combat.char.Rover import Rover
from wwbs_combat.char.Hiyuki import Hiyuki
from wwbs_combat.char.Hsin import Hsin
from wwbs_combat.char.Iuno import Iuno
from wwbs_combat.char.Jianxin import Jianxin
from wwbs_combat.char.Jinhsi import Jinhsi
from wwbs_combat.char.JingRan import JingRan
from wwbs_combat.char.Jiyan import Jiyan
from wwbs_combat.char.Lily import Lily
from wwbs_combat.char.Lingyang import Lingyang
from wwbs_combat.char.Linnai import Linnai
from wwbs_combat.char.Lucilla import Lucilla
from wwbs_combat.char.Lucy import Lucy
from wwbs_combat.char.Lumi import Lumi
from wwbs_combat.char.Luhesi import Luhesi
from wwbs_combat.char.Lupa import Lupa
from wwbs_combat.char.Mortefi import Mortefi
from wwbs_combat.char.Mornye import Mornye
from wwbs_combat.char.Phoebe import Phoebe
from wwbs_combat.char.Phrolova import Phrolova
from wwbs_combat.char.Qingxiao import Qingxiao
from wwbs_combat.char.Qiuyuan import Qiuyuan
from wwbs_combat.char.Rebecca import Rebecca
from wwbs_combat.char.Roccia import Roccia
from wwbs_combat.char.Sanhua import Sanhua
from wwbs_combat.char.ShoreKeeper import ShoreKeeper
from wwbs_combat.char.Suisui import Suisui
from wwbs_combat.char.Suoming import Suoming
from wwbs_combat.char.Taoqi import Taoqi
from wwbs_combat.char.Verina import Verina
from wwbs_combat.char.Xiangliyao import Xiangliyao
from wwbs_combat.char.Xigelika import Xigelika
from wwbs_combat.char.Yinlin import Yinlin
from wwbs_combat.char.Yangyang import Yangyang
from wwbs_combat.char.YangYangSp import YangYangSp
from wwbs_combat.char.Youhu import Youhu
from wwbs_combat.char.Yuanwu import Yuanwu
from wwbs_combat.char.Zani import Zani
from wwbs_combat.char.Zhezhi import Zhezhi

_char_dict_raw = {
    Labels.char_aalto: {'cls': Aalto, 'char_type': CharType.SUB_DPS,
                             'ring_index': Elements.WIND},
    Labels.char_yangyang: {'cls': Yangyang, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.WIND},
    Labels.yangyang_sp: {'cls': YangYangSp, 'char_type': CharType.MAIN_DPS,
                         'ring_index': Elements.HAVOC},
    Labels.char_yinlin: {'cls': Yinlin, 'char_type': CharType.SUB_DPS,
                         'ring_index': Elements.ELECTRIC},
    Labels.char_verina: {'cls': Verina, 'char_type': CharType.HEALER,
                         'ring_index': Elements.SPECTRO},
    Labels.char_shorekeeper: {'cls': ShoreKeeper, 'char_type': CharType.HEALER,
                              'ring_index': Elements.SPECTRO},
    Labels.char_suisui: {'cls': Suisui, 'char_type': CharType.HEALER},
    Labels.char_taoqi: {'cls': Taoqi, 'char_type': CharType.HEALER,
                        'ring_index': Elements.HAVOC},
    (Labels.char_rover, Labels.char_rover_male): {'cls': Rover, 'char_type': CharType.MAIN_DPS},
    Labels.char_encore: {'cls': Encore, 'char_type': CharType.MAIN_DPS,
                         'ring_index': Elements.FIRE},
    Labels.char_jianxin: {'cls': Jianxin, 'char_type': CharType.HEALER,
                          'ring_index': Elements.WIND},
    (Labels.char_sanhua, Labels.char_sanhua2): {'cls': Sanhua, 'char_type': CharType.SUB_DPS,
                                                'ring_index': Elements.ICE},
    (Labels.char_jinhsi, Labels.char_jinhsi2): {'cls': Jinhsi, 'char_type': CharType.MAIN_DPS,
                                                'ring_index': Elements.SPECTRO},
    Labels.char_yuanwu: {'cls': Yuanwu, 'char_type': CharType.SUB_DPS,
                         'ring_index': Elements.ELECTRIC},
    (Labels.chang_changli, Labels.char_changli2): {'cls': Changli, 'char_type': CharType.MAIN_DPS,
                                                   'ring_index': Elements.FIRE},
    Labels.char_chixia: {'cls': Chixia, 'char_type': CharType.MAIN_DPS,
                         'ring_index': Elements.FIRE},
    Labels.char_danjin: {'cls': Danjin, 'char_type': CharType.SUB_DPS,
                         'ring_index': Elements.HAVOC},
    Labels.char_baizhi: {'cls': Baizhi, 'char_type': CharType.HEALER,
                         'ring_index': Elements.ICE},
    Labels.char_calcharo: {'cls': Calcharo, 'char_type': CharType.MAIN_DPS,
                           'ring_index': Elements.ELECTRIC},
    Labels.char_jiyan: {'cls': Jiyan, 'char_type': CharType.MAIN_DPS,
                        'ring_index': Elements.WIND},
    Labels.char_lingyang: {'cls': Lingyang, 'char_type': CharType.MAIN_DPS,
                                'ring_index': Elements.ICE},
    Labels.char_mortefi: {'cls': Mortefi, 'char_type': CharType.SUB_DPS,
                          'ring_index': Elements.FIRE},
    Labels.char_zhezhi: {'cls': Zhezhi, 'char_type': CharType.SUB_DPS,
                         'ring_index': Elements.ICE},
    Labels.char_xiangliyao: {'cls': Xiangliyao, 'char_type': CharType.MAIN_DPS,
                             'ring_index': Elements.ELECTRIC},
    Labels.char_camellya: {'cls': Camellya, 'char_type': CharType.MAIN_DPS,
                           'ring_index': Elements.HAVOC},
    Labels.char_youhu: {'cls': Youhu, 'char_type': CharType.HEALER,
                        'ring_index': Elements.ICE},
    (Labels.char_carlotta, Labels.char_carlotta2): {'cls': Carlotta, 'char_type': CharType.MAIN_DPS,
                                                    'ring_index': Elements.ICE},
    Labels.char_roccia: {'cls': Roccia, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.HAVOC},
    Labels.char_phoebe: {'cls': Phoebe, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.SPECTRO},
    Labels.char_brant: {'cls': Brant, 'char_type': CharType.HEALER, 'ring_index': Elements.FIRE},
    Labels.char_cantarella: {'cls': Cantarella, 'char_type': CharType.HEALER, 'ring_index': Elements.HAVOC},
    (Labels.char_zani, Labels.char_zani2): {'cls': Zani, 'char_type': CharType.MAIN_DPS,
                                            'ring_index': Elements.SPECTRO},
    Labels.char_ciaccona: {'cls': Ciaccona, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.WIND},
    Labels.char_cartethyia: {'cls': Cartethyia, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.WIND},
    Labels.char_lupa: {'cls': Lupa, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.FIRE},
    Labels.char_phrolova: {'cls': Phrolova, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.HAVOC},
    Labels.Augusta: {'cls': Augusta, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.ELECTRIC},
    Labels.char_iuno: {'cls': Iuno, 'char_type': CharType.SUB_DPS,
                       'ring_index': Elements.WIND},
    Labels.char_galbrena: {'cls': Galbrena, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.FIRE},
    Labels.char_chouyuan: {'cls': Qiuyuan, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.WIND},
    (Labels.char_chisa, Labels.char_chisa2): {'cls': Chisa, 'char_type': CharType.HEALER, 'buff_time': 20,
                                              'ring_index': Elements.HAVOC},
    Labels.char_denia: {'cls': Denia, 'char_type': CharType.SUB_DPS, 'buff_time': 14, 'ring_index': Elements.FIRE},
    Labels.char_douling: {'cls': Douling, 'char_type': CharType.HEALER, 'ring_index': Elements.ELECTRIC},
    (Labels.char_linnai, Labels.char_linnai2): {'cls': Linnai, 'char_type': CharType.SUB_DPS,
                                                'ring_index': Elements.SPECTRO},
    (Labels.char_moning, Labels.char_moning_new): {'cls': Mornye, 'char_type': CharType.HEALER,
                                                   'ring_index': Elements.FIRE},
    Labels.char_aemeath: {'cls': Aemeath, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.FIRE},
    Labels.char_xigelika: {'cls': Xigelika, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.WIND},
    Labels.char_luhesi: {'cls': Luhesi, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.SPECTRO},
    (Labels.char_hiyuki, Labels.char_hiyuki2): {'cls': Hiyuki, 'char_type': CharType.MAIN_DPS,
                                             'ring_index': Elements.ICE},
    Labels.char_lucilla: {'cls': Lucilla, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.ICE,
                          'target_box_short_combat_check': True},
    Labels.char_lucy: {'cls': Lucy, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.SPECTRO},
    Labels.char_lumi: {'cls': Lumi, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.ELECTRIC},
    Labels.char_rebecca: {'cls': Rebecca, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.ELECTRIC},
    Labels.char_qingxiao: {'cls': Qingxiao, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.WIND},
    Labels.char_jingran: {'cls': JingRan, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.FIRE},
    Labels.char_hsin: {'cls': Hsin, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.ELECTRIC},
    Labels.char_suoming: {'cls': Suoming, 'char_type': CharType.SUB_DPS, 'buff_time': 8,
                         'ring_index': Elements.ELECTRIC},
    Labels.char_lily: {'cls': Lily, 'char_type': CharType.HEALER, 'buff_time': 30,
                      'ring_index': Elements.SPECTRO},
}

char_dict = {}
for keys, value in _char_dict_raw.items():
    value = dict(value)
    value.setdefault('buff_time', get_default_buff_time(value.get('char_type', CharType.MAIN_DPS)))
    template_names = keys if isinstance(keys, tuple) else (keys,)
    value['canonical_name'] = template_names[0]
    value['template_names'] = template_names
    for key in template_names:
        char_dict[key] = value

char_names = char_dict.keys()


def _get_char_type(task, info):
    return info.get('char_type', CharType.MAIN_DPS)


def _get_buff_time(task, info):
    char_type = _get_char_type(task, info)
    return info.get('buff_time', get_default_buff_time(char_type))


def _apply_char_config(task, char, info):
    if char and info:
        char.char_name = info['canonical_name']
        char.set_char_type(_get_char_type(task, info))
        char.set_buff_time(_get_buff_time(task, info))
        char.target_box_short_combat_check = info.get('target_box_short_combat_check', False)
    return char


def _find_registered_char(task, box, info):
    template_names = info['template_names']
    if len(template_names) == 1:
        return task.find_one(template_names[0], box=box, threshold=0.6)
    return task.find_best_match_in_box(box, template_names, threshold=0.6)


def get_char_by_pos(task, box, index, old_char):
    highest_confidence = 0
    info = None
    name = "unknown"
    char = None
    if old_char and old_char.confidence > 0.92 and old_char.char_name in char_names:
        info = char_dict.get(old_char.char_name)
        char = _find_registered_char(task, box, info)
        if char:
            cls = info.get('cls')
            if not isinstance(old_char, cls):
                return _apply_char_config(task, cls(task, index, char_name=info['canonical_name'],
                                                    confidence=char.confidence,
                                                    ring_index=info.get('ring_index', -1),
                                                    char_type=_get_char_type(task, info),
                                                    buff_time=_get_buff_time(task, info)), info)
            _apply_char_config(task, old_char, info)
            return old_char
    if not char:
        char = task.find_best_match_in_box(box, char_names, threshold=0.6)
        if char:
            info = char_dict.get(char.name)
            name = char.name
            cls = info.get('cls')
            return _apply_char_config(task, cls(task, index, char_name=info['canonical_name'],
                                                confidence=char.confidence,
                                                ring_index=info.get('ring_index', -1),
                                                char_type=_get_char_type(task, info),
                                                buff_time=_get_buff_time(task, info)), info)
    task.log_info(task.tr('could not find char {index} {info} {highest_confidence}').format(index=index, info=info, highest_confidence=highest_confidence))
    if old_char:
        return old_char
    if task.debug:
        task.screenshot(f'could not find char {index}')
    return BaseChar(task, index, char_name=name)


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
