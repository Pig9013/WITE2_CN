# -*- coding: utf-8 -*-
"""二战东线部队番号 / 缩写 术语库与确定性译名规则（WitE2 汉化用）。

为什么要有这个文件
------------------
游戏数据里的番号是**英文转写的俄文/德文缩写**，例如 6 IAK PVO、101st RVGK、
1 AOK、5th O.T.、FBD 1。这些缩写不是英文单词，直接丢给英语语感的翻译
会得到「防空航空军」「近卫步兵师」「帕奥克军」这类凭空发明的译名。
本模块把每一个缩写还原到原语全称，再给出中文定译，并把规则固定下来，
保证同一个模式永远得到同一个中文名。

每条术语都带原语全称，便于核对：
    俄文：иак = истребительный авиационный корпус
    德文：AOK = Armeeoberkommando

译名原则（与中文军事文献惯例一致）
----------------------------------
1. 番号序：近卫第 6 步兵师、防空第 6 歼击航空军——修饰语（近卫 / 防空 /
   预备队 / 舰队）在「第 N」之前。
2. 建制序：第 6 歼击航空军——「第 N」+ 兵种 + 建制。
3. 苏联空军建制统一用「航空军 / 航空师 / 航空团」，不用「航空兵军」。
4. ПВО（противовоздушная оборона，对空防御）译「防空」；Войска ПВО 作为军种译
   「国土防空军」，作为部队隶属关系（иак ПВО）译前缀「防空」。
5. РВГК（Резерв Верховного Главнокомандования）译「最高统帅部预备队」。
6. 德军 AOK / PAOK 是 Oberkommando（司令部），不是「方面军」。
"""

from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------------
# 一、苏联空军番号缩写（俄文原语 + 中文定译）
# ---------------------------------------------------------------------------
# key = 游戏里出现的英文转写；value = (俄文缩写, 俄文全称, 中文)
SOV_AIR = {
    "IAK":  ("иак",  "истребительный авиационный корпус", "歼击航空军"),
    "GIAK": ("гиак", "гвардейский истребительный авиационный корпус", "近卫歼击航空军"),
    "BAK":  ("бак",  "бомбардировочный авиационный корпус", "轰炸航空军"),
    "GBAK": ("гбак", "гвардейский бомбардировочный авиационный корпус", "近卫轰炸航空军"),
    "SAK":  ("сак",  "смешанный авиационный корпус", "混成航空军"),
    "GSAK": ("гсак", "гвардейский смешанный авиационный корпус", "近卫混成航空军"),
    "ShAK": ("шак",  "штурмовой авиационный корпус", "强击航空军"),
    "TBAK": ("тбак", "тяжёлый бомбардировочный авиационный корпус", "重型轰炸航空军"),

    "IAD":  ("иад",  "истребительная авиационная дивизия", "歼击航空师"),
    "GIAD": ("гиад", "гвардейская истребительная авиационная дивизия", "近卫歼击航空师"),
    "NIAD": ("ниад", "ночная истребительная авиационная дивизия", "夜间歼击航空师"),
    "ShAD": ("шад",  "штурмовая авиационная дивизия", "强击航空师"),
    "GShAD":("гшад", "гвардейская штурмовая авиационная дивизия", "近卫强击航空师"),
    "BAD":  ("бад",  "бомбардировочная авиационная дивизия", "轰炸航空师"),
    "GBAD": ("гбад", "гвардейская бомбардировочная авиационная дивизия", "近卫轰炸航空师"),
    "SAD":  ("сад",  "смешанная авиационная дивизия", "混成航空师"),
    "GSAD": ("гсад", "гвардейская смешанная авиационная дивизия", "近卫混成航空师"),
    "DBAD": ("дбад", "дальняя бомбардировочная авиационная дивизия", "远程轰炸航空师"),
    "TBAD": ("тбад", "тяжёлая бомбардировочная авиационная дивизия", "重型轰炸航空师"),
    "NBAD": ("нбад", "ночная бомбардировочная авиационная дивизия", "夜间轰炸航空师"),

    "IAP":  ("иап",  "истребительный авиационный полк", "歼击航空团"),
    "GIAP": ("гиап", "гвардейский истребительный авиационный полк", "近卫歼击航空团"),
    "ShAP": ("шап",  "штурмовой авиационный полк", "强击航空团"),
    "GShAP":("гшап", "гвардейский штурмовой авиационный полк", "近卫强击航空团"),
    "BAP":  ("бап",  "бомбардировочный авиационный полк", "轰炸航空团"),
    "GBAP": ("гбап", "гвардейский бомбардировочный авиационный полк", "近卫轰炸航空团"),
    "NBAP": ("нбап", "ночной бомбардировочный авиационный полк", "夜间轰炸航空团"),
    "DBAP": ("дбап", "дальний бомбардировочный авиационный полк", "远程轰炸航空团"),
    "BBAP": ("ббап", "ближний бомбардировочный авиационный полк", "近程轰炸航空团"),
    "RAP":  ("рап",  "разведывательный авиационный полк", "侦察航空团"),
    "TAP":  ("тап",  "транспортный авиационный полк", "运输航空团"),
    "UAP":  ("уап",  "учебный авиационный полк", "训练航空团"),
    "OSAP": ("осап", "отдельный смешанный авиационный полк", "独立混成航空团"),
}

# 舰队航空兵后缀：иап ЧФ = 黑海舰队航空兵歼击航空团
SOV_FLEET = {
    "ChF":  ("ЧФ",  "Черноморский флот", "黑海舰队"),
    "KBF":  ("КБФ", "Краснознамённый Балтийский флот", "波罗的海舰队"),
    "SF":   ("СФ",  "Северный флот", "北方舰队"),
    "PF":   ("ТОФ", "Тихоокеанский флот", "太平洋舰队"),
    "TOF":  ("ТОФ", "Тихоокеанский флот", "太平洋舰队"),
}

# 苏联地面部队缩写
SOV_GROUND = {
    "RVGK": ("РВГК", "Резерв Верховного Главнокомандования", "最高统帅部预备队"),
    "PVO":  ("ПВО",  "противовоздушная оборона", "防空"),
    "Gv.":  ("гв.",  "гвардейский", "近卫"),
}

# ---------------------------------------------------------------------------
# 二、德军番号缩写（德文原语 + 中文定译）
# ---------------------------------------------------------------------------
DE_ABBR = {
    "AOK":   ("Armeeoberkommando", "集团军司令部"),
    "PAOK":  ("Panzerarmeeoberkommando", "装甲集团军司令部"),
    "Pz.AOK":("Panzerarmeeoberkommando", "装甲集团军司令部"),
    "FBD":   ("Feldeisenbahn-Baudirektion", "野战铁道局"),
    "RHG":   ("rückwärtiges Heeresgebiet", "后方军区"),
    "OT":    ("Organisation Todt", "托特组织"),
    "RAD":   ("Reichsarbeitsdienst", "帝国劳工局"),
    "GD":    ("Großdeutschland", "大德意志"),
    "LAH":   ("Leibstandarte SS Adolf Hitler", "阿道夫·希特勒警卫旗队"),
    "HG":    ("Hermann Göring", "赫尔曼·戈林"),
    "Korück":("Kommandeur des rückwärtigen Armeegebiets", "集团军后方地域司令"),
    "SS":    ("Schutzstaffel", "党卫军"),
    "LW":    ("Luftwaffe", "空军"),
    "OKH":   ("Oberkommando des Heeres", "陆军总司令部"),
    "OKL":   ("Oberkommando der Luftwaffe", "空军总司令部"),
    "AOK-Sturm": ("Armeeoberkommando-Sturmabteilung", "集团军突击支队"),
}

# 德军空军联队缩写
DE_AIR = {
    "JG":  ("Jagdgeschwader", "战斗机联队"),
    "KG":  ("Kampfgeschwader", "轰炸机联队"),
    "SG":  ("Schlachtgeschwader", "对地攻击联队"),
    "StG": ("Sturzkampfgeschwader", "俯冲轰炸机联队"),
    "ZG":  ("Zerstörergeschwader", "重型战斗机联队"),
    "NJG": ("Nachtjagdgeschwader", "夜间战斗机联队"),
    "TG":  ("Transportgeschwader", "运输机联队"),
    "SKG": ("Schnellkampfgeschwader", "快速轰炸机联队"),
    "LG":  ("Lehrgeschwader", "教导联队"),
    "NAGr":("Nahaufklärungsgruppe", "近程侦察大队"),
    "FAGr":("Fernaufklärungsgruppe", "远程侦察大队"),
    "AufklarGr": ("Aufklärungsgruppe", "侦察大队"),
    "Koluft": ("Kommandeur der Luftwaffe", "空军联络司令部"),
}

# ---------------------------------------------------------------------------
# 三、编制（TO&E）词表：英文 → 中文
# ---------------------------------------------------------------------------
OB_WORDS = {
    # 建制
    "Battalion": "营", "Battalions": "营", "Battery": "连",
    "Division": "师", "Brigade": "旅", "Brigades": "旅",
    "Regiment": "团", "Regiments": "团", "Corps": "军",
    "Army": "集团军", "Company": "连", "Battery": "炮兵连",
    "Squadron": "中队", "Group": "群", "Detachment": "支队",
    "Command": "司令部", "Front": "方面军", "Zone": "地域",
    "Base": "基地", "Region": "区域", "District": "军区",
    "HQ": "司令部", "HQs": "司令部", "Force": "部队",
    "Battlegroup": "战斗群", "Kampfgruppe": "战斗群",
    # 兵种 / 性质
    "Infantry": "步兵", "Rifle": "步兵", "Mot.": "摩托化",
    "Motorized": "摩托化", "Mechanized": "机械化", "Motorcycle": "摩托车",
    "Ski": "滑雪", "Ski-Jaeger": "滑雪猎兵", "Skijaeger": "滑雪猎兵",
    "Mountain": "山地", "Airborne": "空降", "Airlanding": "机降",
    "Parachute": "伞兵", "Cavalry": "骑兵", "Cossack": "哥萨克",
    "Tank": "坦克", "Armored": "装甲", "Armoured": "装甲", "Panzer": "装甲",
    "Panzergrenadier": "装甲掷弹兵", "Grenadier": "掷弹兵",
    "Volksgrenadier": "国民掷弹兵", "Jaeger": "猎兵", "Fusilier": "步兵",
    "Sturm": "突击", "Assault": "突击", "Shock": "突击", "Breakthrough": "突破",
    "Guard": "近卫", "Guards": "近卫", "Security": "治安", "Static": "静态",
    "Reserve": "预备", "Ersatz": "补充", "Training": "训练", "Militia": "民兵",
    "Volks": "国民", "Landesschuetzen": "地方守备", "Schuetzen": "步兵",
    "Ost": "东方", "zbV": "特种任务", "SS": "党卫军", "LW": "空军",
    "Luftwaffe": "空军", "FJ": "伞兵", "Fallschirmjaeger": "伞兵",
    "Fallschirm": "伞兵", "Luftlande": "机降", "Marine": "海军",
    "Naval": "海军", "Coastal": "滨海", "NKVD": "内务人民委员部",
    "NKPS": "交通人民委员部", "MNR": "蒙古人民共和国",
    "FF": "自由法国", "RSI": "意大利社会共和国", "CCNN": "黑衫军",
    "Celere": "快速", "Alpina": "阿尔卑斯山地", "Bersaglieri": "狙击兵",
    "Sissi": "锡西", "Hussar": "骠骑兵", "Royal": "皇家",
    "Brandenburg": "勃兰登堡", "Brandenburger": "勃兰登堡",
    "Ranger": "游骑兵", "Commando": "突击队", "Special": "特种",
    "Guard": "近卫", "Launcher": "发射器", "AssaultGun": "突击炮",
    "Tactical": "战术", "Mobile": "机动", "Fast": "快速", "Schnelle": "快速",
    # 炮兵 / 技术兵种
    "Artillery": "炮兵", "Anti-Tank": "反坦克", "Anti-tank": "反坦克",
    "Panzerjaeger": "坦克歼击", "Panzerjagd": "坦克猎歼", "AT-Rifle": "反坦克枪",
    "AA": "高射炮", "AAA": "高射炮", "Anti-Aircraft": "高射炮",
    "AAMG": "高射机枪", "Flak": "高射炮", "MG-Artillery": "机枪炮兵",
    "Machine": "机枪", "Howitzer": "榴弹炮", "Gun": "加农炮", "Cannon": "加农炮",
    "Mortar": "迫击炮", "Rocket": "火箭炮", "Werfer": "火箭炮",
    "Nebelwerfer": "火箭炮", "Launcher": "发射器", "Sturmmoerser": "突击迫击炮",
    "Siege": "攻城", "RR": "铁道", "Railway": "铁道", "Rail": "铁道",
    "Railroad": "铁道", "Engineer": "工兵", "Engineer-Sapper": "工兵",
    "Pioneer": "战斗工兵", "Construction": "建筑", "Labor": "劳工",
    "Chemical": "化学", "Signal": "通信", "Road": "道路", "Bridge": "桥梁",
    "Support": "支援", "Service": "勤务", "Supply": "补给",
    "Reconnaissance": "侦察", "Recon": "侦察", "Recce": "侦察",
    "Light": "轻型", "Heavy": "重型", "Medium": "中型", "Super": "超重型",
    "High": "大", "Power": "威力", "GS": "通用", "Panzer Group": "装甲集群",
    "SP": "自行", "SU": "自行火炮", "Stug": "突击炮", "StuG": "突击炮",
    "Sturmpanzer": "突击坦克", "Flammpanzer": "喷火坦克", "FKL": "遥控",
    "Gep.": "装甲", "Semi-Mot.": "半摩托化", "Sep.": "独立",
    "Separate": "独立", "Mixed": "混成", "Combined": "合成",
    "Fortified": "筑垒", "Fortress": "要塞", "Tower": "塔",
    "Border": "边防", "Bicycle": "自行车", "Amphibious": "两栖",
    "leFH": "轻型野战榴弹炮", "sFH": "重型野战榴弹炮", "BM": "大威力",
    "Aviation": "航空",
    # 国别
    "Rum.": "罗马尼亚", "Hun.": "匈牙利", "Ital.": "意大利", "Fin.": "芬兰",
    "Slov.": "斯洛伐克", "Croat.": "克罗地亚", "BR": "英国", "US": "美国",
    "CA": "加拿大", "SA": "南非", "IN": "印度", "NZ": "新西兰", "AU": "澳大利亚",
    "PO": "波兰", "PVO": "防空", "RVGK": "最高统帅部预备队",
}

# 需要整体识别、不能逐词拼的编制名
OB_PHRASES = {
    "Rifle Division": "步兵师", "Rifle Corps": "步兵军", "Rifle Brigade": "步兵旅",
    "Guards Rifle Division": "近卫步兵师", "Guards Rifle Corps": "近卫步兵军",
    "Tank Corps": "坦克军", "Guards Tank Corps": "近卫坦克军",
    "Mechanized Corps": "机械化军", "Guards Mechanized Corps": "近卫机械化军",
    "Cavalry Corps": "骑兵军", "Guards Cavalry Corps": "近卫骑兵军",
    "Tank Brigade": "坦克旅", "Tank Division": "坦克师",
    "Air Base": "空军基地", "Fortified Zone": "筑垒地域",
    "MG-Artillery Battalion": "机枪炮兵营",
    "Light Division": "轻装师", "Fortified Region": "筑垒地域",
    "Panzer Group": "装甲集群", "Kampfgruppe Panzer Division": "装甲师战斗群",
    "Infantry Gun Company": "步兵炮连", "Infantry Gun Battalion": "步兵炮营",
    "RR Construction Battalion": "铁道建筑营", "RR Construction Brigade": "铁道建筑旅",
    "Rum. RR Construction Battalion": "罗马尼亚铁道建筑营",
    "Hun. RR Construction Battalion": "匈牙利铁道建筑营",
    "Ital. RR Construction Battalion": "意大利铁道建筑营",
    "Slov. RR Construction Battalion": "斯洛伐克铁道建筑营",
    "Light SU Regiment": "轻型自行火炮团", "Medium SU Regiment": "中型自行火炮团",
    "Heavy SU Regiment": "重型自行火炮团",
    "High Power Artillery Battalion": "大威力炮兵营",
    "Heavy Gun Regiment": "重型加农炮团",
    "Army Artillery Regiment": "集团军属炮兵团",
    "Corps Artillery Regiment": "军属炮兵团",
    "Anti-Tank Regiment": "反坦克团", "Anti-Tank Brigade": "反坦克旅",
    "BM Howitzer Regiment": "大威力榴弹炮团",
    "Howitzer Regiment": "榴弹炮团", "Cannon Regiment": "加农炮团",
    "Gun Regiment": "加农炮团", "Mortar Regiment": "迫击炮团",
    "Light Rocket Regiment": "轻型火箭炮团", "Heavy Rocket Battalion": "重型火箭炮营",
    "Light Rocket Battalion": "轻型火箭炮营",
    "Separate Tank Regiment": "独立坦克团", "Separate Tank Battalion": "独立坦克营",
    "Heavy Tank Regiment": "重型坦克团",
    # 复合词必须整体译，逐词拼会出「机枪加农炮营」「轻型野战榴弹炮榴弹炮营」这类废名
    "Machine Gun Battalion": "机枪营",
    "Machine Gun Regiment": "机枪团",
    "Mot. Machine Gun Battalion": "摩托化机枪营",
    "Ital. Mot. Machine Gun Battalion": "意大利摩托化机枪营",
    "leFH Howitzer Battalion": "轻型野战榴弹炮营",
    "sFH Heavy Howitzer Battalion": "重型野战榴弹炮营",
    "Mot. leFH Howitzer Battalion": "摩托化轻型野战榴弹炮营",
    "Mot. sFH Heavy Howitzer Battalion": "摩托化重型野战榴弹炮营",
    "Mot. Super Heavy Howitzer Battalion": "摩托化超重型榴弹炮营",
    "Super Heavy Howitzer Battalion": "超重型榴弹炮营",
    "AAA Gun Battalion": "高射炮营",
    "Assault Gun Battalion": "突击炮营",
    "Hun. Assault Gun Battalion": "匈牙利突击炮营",
    "Rocket Launcher Division": "火箭炮师",
    "Gep. Panzergrenadier Battalion": "装甲掷弹兵营",
    "Gep. Panzergrenadier Regiment": "装甲掷弹兵团",
    "Border Guard Regiment": "边防团",
    "Border Guard Brigade": "边防旅",
    "Border Guard Battalion": "边防营",
    "Hun. Border Guard Regiment": "匈牙利边防团",
    "Hun. Border Guard Brigade": "匈牙利边防旅",
    "Hun. Border Guard Battalion": "匈牙利边防营",
    "Engineer GS Regiment": "通用工兵团",
    "US Engineer GS Regiment": "美国通用工兵团",
    "FKL Panzer Pioneer Battalion": "遥控装甲战斗工兵营",
    "Mot. Panzerjagd Battalion": "摩托化坦克猎歼营",
    "Mot. Volks Werfer Brigade": "摩托化国民火箭炮旅",
    "Mot. Volks Artillery Brigade": "摩托化国民炮兵旅",
    "Sep. Grenadier Regiment": "独立掷弹兵团",
    "Sep. Infantry Regiment": "独立步兵团",
    "Ital. Mot. Medium Howitzer Battalion": "意大利摩托化中型榴弹炮营",
    "Ital. Mot. Medium Gun Battalion": "意大利摩托化中型加农炮营",
}

# ---------------------------------------------------------------------------
# 四、规则
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 五、文献核对过的覆盖表（每条带出处，见 glossary/reference_overrides.json）
# ---------------------------------------------------------------------------
import json as _json
from pathlib import Path as _Path

_OVERRIDE_FILE = _Path(__file__).resolve().parent / "reference_overrides.json"
_REF: dict[str, str] = {}
_REF_NOTE: dict[str, str] = {}
if _OVERRIDE_FILE.exists():
    try:
        _data = _json.loads(_OVERRIDE_FILE.read_text(encoding="utf-8"))
        for _group in ("places", "ui", "terms"):
            for _src, _val in (_data.get(_group) or {}).items():
                if isinstance(_val, list) and len(_val) >= 1:
                    _REF[_src] = _val[0]
                    _REF_NOTE[_src] = _val[1] if len(_val) > 1 else ""
    except Exception:
        pass


def reference_fix(name: str) -> Optional[str]:
    """文献核对表里命中时返回定译，否则 None。"""
    return _REF.get(name) if isinstance(name, str) else None


def reference_note(name: str) -> str:
    return _REF_NOTE.get(name, "")


def is_fragment(s: str) -> bool:
    """纯数字 / 序数 / 罗马数字不能进词典：引擎会把表格里的数字也查表，整列会被改坏。"""
    s = s.strip()
    return bool(re.fullmatch(r"\d+", s) or re.fullmatch(r"\d+(st|nd|rd|th)", s, re.I)
                or re.fullmatch(r"[IVXLC]+", s))


def _sov_air(name: str) -> Optional[str]:
    """苏联空军番号：6 IAK PVO / 12 GIAP PVO / 11 IAP-ChF / 1 BAK Air Corps。"""
    s = name.strip()

    # 1st Air Army -> 第1航空集团军
    m = re.fullmatch(r"(\d+)(?:st|nd|rd|th)\s+Air Army", s, re.I)
    if m:
        return f"第{m.group(1)}航空集团军"

    # <N> <ABBR> [-Fleet] [PVO] [Air Corps|Air Command|Air Army]
    m = re.fullmatch(
        r"(\d+)\s+([A-Za-z]+?)(?:-([A-Za-z]+))?(?:\s+PVO)?(?:\s+Air(?:\s+(?:Corps|Command|Army))?)?",
        s)
    if not m:
        return None
    num, tok, fleet = m.group(1), m.group(2), m.group(3)
    key = tok if tok in SOV_AIR else (tok.upper() if tok.upper() in SOV_AIR else None)
    if key is None:
        return None
    body = SOV_AIR[key][2]
    pvo = bool(re.search(r"\bPVO\b", s))
    prefix = ""
    if fleet:
        f = SOV_FLEET.get(fleet)
        if not f:
            return None
        prefix = f[2]
    if pvo:
        prefix = "防空" + prefix
    # 中文序：近卫在「第N」之前；GBAP -> 近卫第12轰炸航空团，而不是第12近卫轰炸航空团
    if body.startswith("近卫"):
        return f"{prefix}近卫第{num}{body[2:]}"
    return f"{prefix}第{num}{body}"


def _german_hq(name: str) -> Optional[str]:
    """德军司令部缩写：1 AOK / 2 PAOK / 1 AOK Sturm / 5th O.T. / FBD 1 / RHG Command North。"""
    s = name.strip()

    m = re.fullmatch(r"(\d+)\s+(AOK|PAOK)(?:\s+(Sturm))?", s)
    if m:
        if m.group(3):
            # AOK Sturm = 集团军司令部编成的突击支队
            zh = "装甲集团军" if m.group(2) == "PAOK" else "集团军"
            return f"第{m.group(1)}{zh}突击支队"
        return f"第{m.group(1)}{DE_ABBR[m.group(2)][1]}"

    m = re.fullmatch(r"([A-Z][a-z]+)\s+(AOK|PAOK)(?:\s+(Sturm))?", s)
    if m and m.group(3):
        zh = "装甲集团军" if m.group(2) == "PAOK" else "集团军"
        return f"{m.group(1)}{zh}突击支队"

    # Norway AOK / AOK 等不带数字的
    m = re.fullmatch(r"([A-Z][a-z]+)\s+(AOK|PAOK)", s)
    if m:
        where = {"Norway": "挪威"}.get(m.group(1), m.group(1))
        return f"{where}{DE_ABBR[m.group(2)][1]}"

    m = re.fullmatch(r"FBD\s*(\d+)", s)
    if m:
        return f"第{m.group(1)}{DE_ABBR['FBD'][1]}"

    m = re.fullmatch(r"RHG\s+Command(?:\s+(North|South|Center|Centre))?", s)
    if m:
        where = {"North": "北方", "South": "南方", "Center": "中央", "Centre": "中央"}.get(m.group(1) or "", "")
        return f"{where}{DE_ABBR['RHG'][1]}司令部"

    m = re.fullmatch(r"(\d+)(?:st|nd|rd|th)\s+RHG\s+Command", s)
    if m:
        return f"第{m.group(1)}{DE_ABBR['RHG'][1]}司令部"

    m = re.fullmatch(r"(\d+)(?:st|nd|rd|th)\s+O\.?T\.?", s)
    if m:
        return f"{DE_ABBR['OT'][1]}第{m.group(1)}建筑营"

    return None


def _rvgk(name: str, ob_type: str) -> Optional[str]:
    """101st RVGK + 编制 -> 最高统帅部预备队第101榴弹炮团。"""
    m = re.fullmatch(r"(\d+)(?:st|nd|rd|th)\s+RVGK", name.strip())
    if not m:
        return None
    t = ob_phrase(ob_type)
    if not t:
        return None
    return f"{SOV_GROUND['RVGK'][2]}第{m.group(1)}{t}"


def ob_phrase(text: str) -> Optional[str]:
    """把 OB（编制表）里的英文编制名译成中文；认不出就返回 None。"""
    s = text.split("|")[-1].strip()
    # OB 名常带年份/批次码：41a Howitzer Regiment、44 Light SU Regiment
    s = re.sub(r"^\d{2}[a-z]?\s+", "", s).strip()
    if not s:
        return None
    # 「… Light Division」一律「…轻装师」：匈牙利/斯洛伐克的轻型师是编制概念，不是坦克口径意义上的「轻型」
    m = re.fullmatch(r"(.+?)\s+Light Division", s)
    if m:
        head = ob_phrase(m.group(1))
        if head:
            return head + "轻装师"
    if s in OB_PHRASES:
        return OB_PHRASES[s]
    # 复合名词整体识别，避免「机枪加农炮营」「高射炮炮兵连」
    s = re.sub(r"Machine Gun", "机枪", s)
    s = re.sub(r"Anti-Aircraft", "高射炮", s)
    s = re.sub(r"AA Artillery", "高射炮", s)
    s = re.sub(r"Engineer-Sapper", "工兵", s)
    s = re.sub(r"Anti-Tank|Anti-tank", "反坦克", s)
    words = s.replace("/", " ").split()
    out = []
    for w in words:
        w2 = w.rstrip(",")
        if w2 in OB_WORDS:
            out.append(OB_WORDS[w2])
        elif re.fullmatch(r"\(?\d+mm\)?|K18|Nr\.?", w2):
            out.append(w2)
        else:
            return None
    return "".join(out)


def guards_first(zh: str) -> str:
    """中文序：第6近卫步兵师 -> 近卫第6步兵师。"""
    return re.sub(r"^([^第]*?)第(\d+)(近卫)", r"\1近卫第\2", zh)


if __name__ == "__main__":
    probe = [
        ("6 IAK PVO", ""), ("12 GIAP PVO", ""), ("11 IAP-ChF", ""), ("1 BAK Air Corps", ""),
        ("310 IAD PVO", ""), ("1 AOK", ""), ("2 PAOK Sturm", ""), ("FBD 1", ""),
        ("RHG Command North", ""), ("5th O.T.", ""), ("101st RVGK", "41a | Howitzer Regiment"),
        ("1st Air Army", ""),
    ]
    for src, ob in probe:
        got = _sov_air(src) or _german_hq(src) or _rvgk(src, ob)
        print(f"{src:24s} {ob:28s} -> {got}")
