#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic Chinese name builder for WitE2 unit / air-group names.

Structured formation names should not be left to an LLM: the same pattern must
always produce the same Chinese name.  This module handles the common patterns
and returns None for anything it cannot prove, so the caller can queue it for
review instead of inventing a translation.
"""
from __future__ import annotations

import re
from typing import Optional

ROMAN = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
    "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
    "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20, "XXI": 21,
    "XXII": 22, "XXIII": 23, "XXIV": 24, "XXV": 25, "XXVI": 26, "XXVII": 27,
    "XXVIII": 28, "XXIX": 29, "XXX": 30, "XXXI": 31, "XXXII": 32,
    "XXXIII": 33, "XXXIV": 34, "XXXV": 35, "XXXVI": 36, "XXXVII": 37,
    "XXXVIII": 38, "XXXIX": 39, "XL": 40, "XLI": 41, "XLII": 42,
    "XLIII": 43, "XLIV": 44, "XLV": 45, "XLVI": 46, "XLVII": 47,
    "XLVIII": 48, "XLIX": 49, "L": 50, "LI": 51, "LII": 52, "LIII": 53,
    "LIV": 54, "LV": 55, "LVI": 56, "LVII": 57, "LVIII": 58, "LIX": 59,
    "LX": 60, "LXI": 61, "LXII": 62, "LXIII": 63, "LXIV": 64, "LXV": 65,
    "LXVI": 66, "LXVII": 67, "LXVIII": 68, "LXIX": 69, "LXX": 70,
    # Non-standard additive forms used by the game data.
    "XXXX": 40, "XXXXI": 41, "XXXXII": 42, "XXXXIII": 43, "XXXXIV": 44,
    "XXXXV": 45, "XXXXVI": 46, "XXXXVII": 47, "XXXXVIII": 48, "XXXXIX": 49,
}

# Token-level vocabulary.  Keys are lower-case, punctuation-normalised tokens.
TOKEN_MAP = {
    # branches / modifiers
    "guards": "近卫", "guard": "近卫", "gds": "近卫",
    "rifle": "步兵", "infantry": "步兵", "inf": "步兵",
    "tank": "坦克", "armored": "装甲", "armoured": "装甲",
    "panzer": "装甲", "pz": "装甲", "pz.": "装甲",
    "panzergrenadier": "装甲掷弹兵", "pzrgrn": "装甲掷弹兵",
    "grenadier": "掷弹兵", "volksgrenadier": "国民掷弹兵",
    "cavalry": "骑兵", "cav": "骑兵",
    "mechanized": "机械化", "mechanised": "机械化", "mech": "机械化",
    "motorized": "摩托化", "motorised": "摩托化", "motor": "摩托化", "mot.": "摩托化",
    "airborne": "空降", "parachute": "伞兵", "fallschirm": "伞兵",
    "mountain": "山地", "alpini": "阿尔卑斯山地兵",
    "security": "治安", "static": "静态", "reserve": "预备",
    "light": "轻装", "shock": "突击", "assault": "突击",
    "artillery": "炮兵", "rocket": "火箭",
    "engineer": "工兵", "pioneer": "战斗工兵",
    "reconnaissance": "侦察", "recon": "侦察",
    "penal": "惩戒", "militia": "民兵", "partisan": "游击队",
    "naval": "海军", "marine": "海军陆战", "coastal": "滨海",
    "ski": "滑雪", "cossack": "哥萨克",
    "air": "空军", "ss": "党卫军", "military": "",
    "training": "训练", "replacement": "补充", "field": "野战",
    "special": "特种", "breakthrough": "突破", "landing": "机降",
    "fortress": "要塞", "frontier": "边防", "expeditionary": "远征",
    "volunteer": "志愿", "vlntr": "志愿", "sturm": "突击",
    "red": "红", "banner": "旗",
    # nationality / theatre
    "hun.": "匈牙利", "hungarian": "匈牙利", "hung.": "匈牙利",
    "rum.": "罗马尼亚", "rumanian": "罗马尼亚", "romanian": "罗马尼亚", "rom.": "罗马尼亚",
    "ital.": "意大利", "italian": "意大利", "it.": "意大利",
    "fin.": "芬兰", "finnish": "芬兰",
    "slovak": "斯洛伐克", "slovakian": "斯洛伐克", "slov.": "斯洛伐克",
    "croat.": "克罗地亚", "croatian": "克罗地亚",
    "span.": "西班牙", "spanish": "西班牙", "spanische": "西班牙",
    "russian": "俄罗斯", "ukrainian": "乌克兰", "estonian": "爱沙尼亚",
    "baltic": "波罗的海", "belorussian": "白俄罗斯", "byelorussian": "白俄罗斯",
    "caucasus": "高加索", "crimean": "克里米亚", "don": "顿河",
    "donbass": "顿巴斯", "karelian": "卡累利阿", "carpathian": "喀尔巴阡",
    "north": "北方", "south": "南方", "center": "中央", "centre": "中央",
    "east": "东方", "west": "西方",
    "northwestern": "西北", "southwestern": "西南", "southeastern": "东南",
    "northeastern": "东北", "southern": "南方", "northern": "北方",
    "western": "西方", "eastern": "东方", "central": "中央",
    "urals": "乌拉尔", "volga": "伏尔加", "donbass": "顿巴斯",
    "leningrad": "列宁格勒", "moscow": "莫斯科", "kiev": "基辅",
    "kharkov": "哈尔科夫", "kursk": "库尔斯克", "bryansk": "布良斯克",
    "kalinin": "加里宁", "odessa": "敖德萨", "orel": "奥廖尔",
    "stalingrad": "斯大林格勒", "voronezh": "沃罗涅日", "steppe": "草原",
    "volkhov": "沃尔霍夫", "crimean": "克里米亚", "caucasus": "高加索",
    "transcaucasus": "外高加索", "southeastern": "东南",
    # formation nouns
    "division": "师", "divison": "师", "divisiion": "师", "div.": "师",
    "corps": "军", "army": "集团军", "brigade": "旅", "regiment": "团",
    "battalion": "营", "company": "连", "group": "集群", "front": "方面军",
    "district": "军区", "luftflotte": "航空队", "fliegerkorps": "航空军",
    "korps": "军", "armee": "集团军", "heeresgruppe": "集团军群",
    "panzerarmee": "装甲集团军", "panzergruppe": "装甲集群",
    "oberkommando": "总司令部", "kommando": "司令部",
    # proper names
    "grossdeutschland": "大德意志", "feldherrnhalle": "统帅堂", "felderrnhalle": "统帅堂",
    "totenkopf": "骷髅", "wiking": "维京", "brandenburg": "勃兰登堡",
    "polizei": "警察", "hermann": "赫尔曼", "goring": "戈林", "göring": "戈林",
    "gring": "戈林", "das": "", "reich": "帝国", "nederland": "荷兰",
    "blue": "蓝色", "szekler": "塞凯伊", "berlin": "柏林", "doeberitz": "多贝里茨",
    "l.a.h.": "阿道夫·希特勒警卫旗队", "lah": "阿道夫·希特勒警卫旗队",
    "batskelevich": "巴茨克列维奇", "dovator": "多瓦托尔", "kuliev": "库利耶夫",
    "mishulin": "米舒林", "vicenza": "维琴察", "julia": "朱利亚",
    "principe": "亲王", "amedeo": "阿梅代奥", "celere": "快速",
    "ravenna": "拉文纳", "cuneense": "库内奥", "torino": "都灵",
    "cosseria": "科塞里亚", "pasubio": "帕苏比奥", "tridentina": "特里登蒂纳",
    "sforzesca": "斯福尔扎", "isthmus": "地峡", "karelian": "卡累利阿",
    "antonescu": "安东内斯库", "ostmark": "东马克", "courland": "库尔兰",
    "vistula": "维斯瓦", "north": "北方", "south": "南方",
}

# Whole-name overrides (case-insensitive, punctuation-normalised).
FULL_MAP = {
    "okh": "陆军总司令部",
    "okl": "空军总司令部",
    "army group a": "A集团军群",
    "army group b": "B集团军群",
    "army group c": "C集团军群",
    "army group center": "中央集团军群",
    "army group centre": "中央集团军群",
    "army group north": "北方集团军群",
    "army group south": "南方集团军群",
    "army group don": "顿河集团军群",
    "army group e": "E集团军群",
    "army group north ukraine": "北乌克兰集团军群",
    "army group south ukraine": "南乌克兰集团军群",
    "army group courland": "库尔兰集团军群",
    "army group ostmark": "东马克集团军群",
    "army group vistula": "维斯瓦集团军群",
    "army group antonescu": "安东内斯库集团军群",
    "oberkommando der luftwaffe(okl)": "空军总司令部（OKL）",
    "oberkommando des heeres(okh)": "陆军总司令部（OKH）",
    "oberkommando des heeres": "陆军总司令部（OKH）",
    "stavka": "最高统帅部大本营",
    "aok": "集团军司令部",
    "armir": "意大利驻俄集团军",
    "csir": "意大利驻俄远征军",
    "gyorshadtest": "匈牙利快速军",
    "the army of the isthmus": "地峡集团军",
    "coastal army": "滨海集团军",
    "karelian army": "卡累利阿集团军",
    "carpathian group": "喀尔巴阡集群",
    "hg fallschirm panzer corps": "赫尔曼·戈林伞兵装甲军",
    "grossdeutschland panzer corps": "大德意志装甲军",
    "feldherrnhalle panzer corps": "统帅堂装甲军",
    "felderrnhalle panzer corps": "统帅堂装甲军",
    "brandenburg panzergrenadier division": "勃兰登堡装甲掷弹兵师",
    "polizei ss infantry division": "警察党卫军步兵师",
    "totenkopf ss motorized division": "骷髅党卫军摩托化师",
    "st. laszlo hungarian guard division": "圣拉斯洛匈牙利卫队师",
    "slovak security division": "斯洛伐克治安师",
    "slovakian corps": "斯洛伐克军",
    "alpini ital. corps": "意大利阿尔卑斯山地军",
    "expeditionary ital. corps": "意大利远征军",
    "cavalry rumanian corps": "罗马尼亚骑兵军",
    "mountain rum. corps": "罗马尼亚山地军",
    "mountain rumanian corps": "罗马尼亚山地军",
    "frontier rumanian infantry division": "罗马尼亚边防步兵师",
}

AIR_UNITS = {
    "jg": "战斗机联队", "jagdgeschwader": "战斗机联队",
    "kg": "轰炸机联队", "kampfgeschwader": "轰炸机联队",
    "stg": "俯冲轰炸机联队", "stukageschwader": "俯冲轰炸机联队",
    "sg": "对地攻击联队", "schlachtgeschwader": "对地攻击联队",
    "tg": "运输机联队", "transportgeschwader": "运输机联队",
    "njg": "夜间战斗机联队", "nachtjagdgeschwader": "夜间战斗机联队",
    "zg": "重型战斗机联队", "zerstörergeschwader": "重型战斗机联队",
    "lg": "教导联队", "lehrgeschwader": "教导联队",
    "kgzbv": "特种运输联队",
}

TYPO = {
    "divison": "division",
    "divisiion": "division",
    "rile": "rifle",
    "volksgrenadierdivision": "volksgrenadier division",
    "felderrnhalle": "feldherrnhalle",
    "apini": "alpini",
    "gring": "goring",
}


def norm(s: str) -> str:
    s = s.lower().strip()
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*\(\s*", "(", s)
    s = re.sub(r"\s*\)\s*", ")", s)
    return s


def roman_to_int(s: str) -> Optional[int]:
    return ROMAN.get(s.upper())


def _translate_tokens(text: str) -> Optional[str]:
    """Translate a phrase token-by-token; return None if any token is unknown."""
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = re.sub(r"'s\b", "", text, flags=re.I)  # Dovator's -> Dovator
    text = re.sub(r"[*\"'\u201c\u201d\u2018\u2019]", " ", text)
    text = re.sub(r"[()]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = re.findall(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9.\-]*", text)
    out = []
    for tok in tokens:
        if re.fullmatch(r"\d+", tok):
            out.append(tok)
            continue
        low = tok.lower().strip(".")
        low = TYPO.get(low, low)
        val = TOKEN_MAP.get(low)
        if val is None:
            val = TOKEN_MAP.get(low + ".")  # Hun. / Rum. / Mot. / L.A.H.
        if val is None:
            return None
        if val:
            out.append(val)
    if not out:
        return None
    return "".join(out)


def translate_airgroup(name: str) -> Optional[str]:
    s = name.strip()
    m = re.fullmatch(r"(Stab)\s*/\s*([A-Za-z]+)\s*(\d+)", s, re.I)
    if m:
        unit = AIR_UNITS.get(m.group(2).lower())
        return f"第{m.group(3)}{unit}指挥部" if unit else None
    m = re.fullmatch(r"([IVX]+)\.\s*/\s*([A-Za-z]+)\s*(\d+)", s, re.I)
    if m:
        unit = AIR_UNITS.get(m.group(2).lower())
        grp = roman_to_int(m.group(1))
        return f"第{m.group(3)}{unit}第{grp}大队" if unit and grp else None
    m = re.fullmatch(r"(\d+)\.\s*/\s*([A-Za-z]+)\s*(\d+)", s)
    if m:
        unit = AIR_UNITS.get(m.group(2).lower())
        return f"第{m.group(3)}{unit}第{m.group(1)}大队" if unit else None
    m = re.fullmatch(r"NAGr\.?\s*(\d+)", s, re.I)
    if m:
        return f"第{m.group(1)}侦察大队"
    return None


def translate_unit_name(name: str) -> Optional[str]:
    """Return a deterministic Chinese name, or None if uncertain."""
    raw = name.strip()
    raw = re.sub(r"\s+", " ", raw)
    key = norm(raw)
    key = TYPO.get(key, key)
    if key in FULL_MAP:
        return FULL_MAP[key]

    air = translate_airgroup(raw)
    if air:
        return air

    # Combined alternative designations: "A:B" and "A/B".
    for sep, joiner in ((":", "；"), ("/", "／")):
        if sep in raw:
            parts = [p.strip() for p in raw.split(sep) if p.strip()]
            if len(parts) > 1:
                got = [translate_unit_name(p) for p in parts]
                if all(got):
                    return joiner.join(got)

    # Fix missing spaces before formation nouns (VolksgrenadierDivision).
    raw = re.sub(r"(?<=[a-z])(Division|Corps|Army|Brigade|Regiment|District)\b", r" \1", raw)
    raw = re.sub(r"\s+", " ", raw).strip()

    # "Feldherrnhalle Nr.1 Panzer Division" -> prefix + number + rest.
    m = re.match(r"^(.+?)\s+Nr\.?\s*(\d+)\s+(.+)$", raw, re.I)
    if m:
        prefix = _translate_tokens(m.group(1))
        rest = _translate_tokens(m.group(3))
        return f"{prefix}第{m.group(2)}{rest}" if prefix and rest else None

    # Luftflotte N / Fliegerkorps N (noun before number)
    m = re.fullmatch(r"(Luftflotte|Fliegerkorps|Luftwaffenkommando)\s+([IVX]+|\d+)", raw, re.I)
    if m:
        num = int(m.group(2)) if m.group(2).isdigit() else roman_to_int(m.group(2))
        noun = {"luftflotte": "航空队", "fliegerkorps": "航空军", "luftwaffenkommando": "空军司令部"}[m.group(1).lower()]
        return f"第{num}{noun}" if num else None

    # Remove trailing markers and parenthetical abbreviations.
    core = re.sub(r"\s*\([A-Za-z.]{2,8}\)\s*$", "", raw).strip()
    core = re.sub(r"\s*\*+\s*$", "", core).strip()

    # Number prefix: 100th, 4th, 1st, 2nd, 3rd, 10.
    m = re.match(r"^(\d+)(?:st|nd|rd|th)?\s+(.+)$", core, re.I)
    if m:
        rest = _translate_tokens(m.group(2))
        return f"第{m.group(1)}{rest}" if rest else None

    # Roman prefix: LVI Motorized Corps, IV Corps, XXXXVI Motorized Corps.
    m = re.match(r"^([IVXLCDM]+)\s+(.+)$", core)
    if m:
        num = roman_to_int(m.group(1))
        rest = _translate_tokens(m.group(2))
        return f"第{num}{rest}" if num and rest else None

    # No number: translate the phrase as-is.
    return _translate_tokens(core)


def translate_leader_rank(rank: str) -> Optional[str]:
    """Translate a rank string only; leader names stay in the source script."""
    from_glossary = {
        "generalfeldmarschall": "元帅", "generaloberst": "大将",
        "general der infanterie": "步兵上将", "general der panzertruppe": "装甲兵上将",
        "general der artillerie": "炮兵上将", "generalleutnant": "中将",
        "generalmajor": "少将", "oberst": "上校", "oberstleutnant": "中校",
        "major": "少校", "hauptmann": "上尉", "oberleutnant": "中尉",
        "leutnant": "少尉", "feldwebel": "中士", "unteroffizier": "下士",
        "gefreiter": "上等兵", "soldat": "列兵",
    }
    return from_glossary.get(norm(rank))


if __name__ == "__main__":
    samples = [
        "100th Guards Rifle Division", "10th Hun. Infantry Brigade", "4th Rum. Army",
        "1st Panzer Division", "LVI Motorized Corps", "Army Group North",
        "Luftflotte 4", "Stab/JG 1", "II./JG 1", "Grossdeutschland Panzer Corps",
        "Feldherrnhalle Nr.1 Panzer Division", "The Army of the Isthmus",
        "Bryansk Front", "104th Tank Divison",
    ]
    for s in samples:
        print(f"{s:50s} -> {translate_unit_name(s)}")
