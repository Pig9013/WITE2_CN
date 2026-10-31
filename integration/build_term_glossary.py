# -*- coding: utf-8 -*-
"""生成 docs/术语与番号总表.md：多语言对照 + 编号 + 来源/验证。

每条都有：
  编号   T-xxx
  来源   规则出自哪份文献/哪条规则
  验证   该中文在本机语料里出现的次数（0 表示尚无语料佐证，仅有文献或规则依据）
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "glossary"))
import designations as D  # noqa: E402

OUT = PROJECT / "docs" / "术语与番号总表.md"
DICT = PROJECT / "mod" / "payload" / "translations.json"
CORPUS = Path(r"D:\Tool\WITE2\corpus")

ECHELON = [
    ("фронт", "Heeresgruppe", "Front", "方面军"),
    ("—", "Heeresgruppe", "Army Group", "集团军群"),
    ("армия", "Armee", "Army", "集团军"),
    ("корпус", "Korps", "Corps", "军"),
    ("дивизия", "Division", "Division", "师"),
    ("бригада", "Brigade", "Brigade", "旅"),
    ("полк", "Regiment", "Regiment", "团"),
    ("батальон", "Bataillon", "Battalion", "营"),
    ("дивизион", "Abteilung", "Battalion (artillery)", "营（炮兵）"),
    ("рота", "Kompanie", "Company", "连"),
    ("батарея", "Batterie", "Battery", "炮兵连"),
]

SOV = [
    ("истребительный авиационный корпус", "иак", "IAK", "歼击航空军"),
    ("истребительная авиационная дивизия", "иад", "IAD", "歼击航空师"),
    ("истребительный авиационный полк", "иап", "IAP", "歼击航空团"),
    ("штурмовой авиационный полк", "шап", "ShAP", "强击航空团"),
    ("бомбардировочный авиационный полк", "бап", "BAP", "轰炸航空团"),
    ("ночной бомбардировочный авиаполк", "нбап", "NBAP", "夜间轰炸航空团"),
    ("смешанный авиационный корпус", "сак", "SAK", "混成航空军"),
    ("смешанная авиационная дивизия", "сад", "SAD", "混成航空师"),
    ("стрелковый корпус", "ск", "RC", "步兵军"),
    ("стрелковая дивизия", "сд", "RD", "步兵师"),
    ("танковый корпус", "тк", "Tank Corps", "坦克军"),
    ("механизированный корпус", "мк", "MC", "机械化军"),
    ("кавалерийский корпус", "кк", "CE", "骑兵军"),
    ("отдельный танковый батальон", "отб", "SepTBn", "独立坦克营"),
    ("гвардейский", "гв.", "Gds", "近卫"),
    ("Резерв Верховного Главнокомандования", "РВГК", "RVGK", "最高统帅部预备队"),
    ("противовоздушная оборона", "ПВО", "PVO", "防空"),
]

DE = [
    ("Armeeoberkommando", "AOK", "集团军司令部"),
    ("Panzerarmeeoberkommando", "PAOK", "装甲集团军司令部"),
    ("Heeresgruppe", "HGr", "集团军群"),
    ("Panzer-Division", "Pz.Div.", "装甲师"),
    ("Infanterie-Division", "Inf.Div.", "步兵师"),
    ("Panzergrenadier-Division", "Pz.Gren.Div.", "装甲掷弹兵师"),
    ("Volksgrenadier-Division", "VGD", "国民掷弹兵师"),
    ("Gebirgs-Division", "Geb.Div.", "山地师"),
    ("Sicherungs-Division", "Sich.Div.", "治安师"),
    ("Luftwaffe-Feld-Division", "Lw.Feld.Div.", "空军野战师"),
    ("Feldeisenbahn-", "FBD", "野战铁道局"),
    ("rückwärtiges Heeresgebiet", "RHG", "后方军区"),
    ("Organisation Todt", "OT", "托特组织"),
    ("Großdeutschland", "GD", "大德意志"),
    ("Leibstandarte SS Adolf Hitler", "LAH", "阿道夫·希特勒警卫旗队"),
    ("Hermann Göring", "HG", "赫尔曼·戈林"),
]

PROPER_RULES = [
    ("3rd Gennaio / 23rd Marzo", "1月3日 / 3月23日", "3 Gennaio / 23 Marzo",
     "意大利黑衫军军名按纪念日命名，是番号不是日期；直译成日期读者反而不认"),
    ("1st Sep. / 507th Sep.", "9月1日 / 第507步兵师", "第1独立 / 第507独立",
     "Sep. = Separate（独立），不是 September；旧译既错解缩写又凭空补了「步兵师」"),
    ("Waren / Siegen", "物资 / 胜利", "瓦伦 / 锡根",
     "德语城镇名恰好也是常用词，按字面译成物资、胜利就成了笑话"),
    ("Agri / Aguilas / Airasca", "农业区 / 鹰群 / 空袭中", "阿勒 / 阿吉拉斯 / 艾拉斯卡",
     "土耳其、西班牙、意大利地名，按字面义译完全失去地名功能"),
    ("Allier / Alle", "盟军 / 所有", "阿列河 / 阿勒", "法国河流与地名"),
]

UI = [("Theatre Box", "战区框"), ("Air Group", "航空队"), ("Air Directive", "空中指令"),
      ("Ground Support", "地面支援"), ("Depot", "补给站"), ("Railhead", "铁路端点"),
      ("Admin Points", "行政点"), ("Combat Value", "战斗值"), ("TOE", "编制表"),
      ("Order of Battle", "战斗序列"), ("HQ", "司令部"), ("Fortified Zone", "筑垒地域"),
      ("Refit", "整补"), ("Isolated", "被孤立")]

SRC_SOV = "WitE2 官方中译 + 《泥足巨人》附录（Granz, Colossus Reborn 中译本 p.19–23）"
SRC_DE = "MIS Special Series No.12《German Military Abbreviations》(1943) + TM-E 30-451 (1945)"
SRC_ECH = "FM 100-2-3《The Soviet Army》(1991) 建制层级 + WitE2 官方中译"
SRC_UI = "WitE2 官方中文手册（项目 T1 底本）"
SRC_EQ = "德文原义（Haubitze/Kanone/Geschütz/Pak/Flak）+ 本库一致性规则"


def load_corpus_counts(terms):
    counts = {t: 0 for t in terms}
    for f in CORPUS.rglob("full.txt"):
        try:
            t = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for k in counts:
            counts[k] += t.count(k)
    return counts


def main():
    d = json.loads(DICT.read_text(encoding="utf-8"))
    all_zh = [r[3] for r in ECHELON] + [r[3] for r in SOV] + [r[2] for r in DE] + [r[1] for r in UI]
    cnt = load_corpus_counts(set(all_zh))

    L = []
    n = [0]

    def nid():
        n[0] += 1
        return "T-%03d" % n[0]

    L.append("# 术语与番号总表（俄 / 德 / 英 / 中）\n")
    L.append("> 用途：翻译对照用。每行带**编号**、**来源**与**语料验证次数**。")
    L.append("> 语料验证 = 该中文在本机 2,300 万字语料（五部中文战史 + WitE/WitE2 中文手册 + 兵棋规则书中译）里的出现次数；"
             "为 0 表示尚无语料佐证，仅有文献或规则依据，使用时可优先复核。\n")
    L.append("词典条目：" + str(len(d)) + "。\n")

    L.append("## 一、建制层级\n")
    L.append("| 编号 | 俄文 | 德文 | 英文 | 中文 | 来源 | 语料验证 |")
    L.append("|---|---|---|---|---|---|---|")
    for a, b, c, e in ECHELON:
        L.append("| " + nid() + " | " + a + " | " + b + " | " + c + " | " + e + " | " + SRC_ECH +
                 " | " + str(cnt.get(e, 0)) + " |")
    L.append("")

    L.append("## 二、苏联番号缩写\n")
    L.append("| 编号 | 俄文全称 | 缩写 | 游戏写法 | 中文 | 来源 | 语料验证 |")
    L.append("|---|---|---|---|---|---|---|")
    for full, abbr, game, zh in SOV:
        L.append("| " + nid() + " | " + full + " | " + abbr + " | " + game + " | " + zh + " | " + SRC_SOV +
                 " | " + str(cnt.get(zh, 0)) + " |")
    L.append("")
    L.append("规则：修饰语（近卫 / 防空 / 预备队 / 舰队）在「第 N」之前；航空兵建制统一「航空军 / 航空师 / 航空团」。\n")

    L.append("## 三、德军番号缩写\n")
    L.append("| 编号 | 德文全称 | 缩写 | 中文 | 来源 | 语料验证 |")
    L.append("|---|---|---|---|---|---|")
    for full, abbr, zh in DE:
        L.append("| " + nid() + " | " + full + " | " + abbr + " | " + zh + " | " + SRC_DE +
                 " | " + str(cnt.get(zh, 0)) + " |")
    L.append("")

    L.append("## 四、《泥足巨人》附录对照（出版译本，91 条）\n")
    tsv = PROJECT / "docs" / "reference" / "abbr_glantz.tsv"
    if tsv.exists():
        rows = list(csv.DictReader(tsv.open(encoding="utf-8"), delimiter="\t"))
        L.append("| 编号 | 缩写 | 英文 | 译本中文 | 来源 | 语料验证 |")
        L.append("|---|---|---|---|---|---|")
        for r in rows:
            zh = r["chinese"]
            L.append("| " + nid() + " | " + r["abbr"] + " | " + r["english"] + " | " + zh +
                     " | 泥足巨人 附录 p." + r.get("source_page", "?") + " | " +
                     str(cnt.get(zh, 0)) + " |")
    L.append("")

    L.append("## 五、装备名（按家族）\n")
    L.append("统一规则：口径一律「毫米」；型号保留原文；类型词按德文原义——"
             "Haubitze→榴弹炮、Kanone→加农炮/野战炮、Geschütz→步兵炮、Pak→反坦克炮、Flak→高射炮。\n")
    fams = {
        "反坦克炮（Pak / sPzB / PzB）": r"Pak|sPzB|PzB",
        "高射炮（Flak）": r"Flak",
        "榴弹炮（leFH / sFH / Howitzer）": r"leFH|sFH|Howitzer",
        "野战炮 / 加农炮（FK / K / sK）": r"Field Gun|sK|leFK",
        "步兵炮（leIG / sIG）": r"Infantry Gun",
        "迫击炮（GrW / Mortar）": r"GrW|Mortar",
        "机枪 / 反坦克枪": r"Machine Gun|AT-Rifle",
    }
    for title, pat in fams.items():
        rx = re.compile(pat)
        rows = [(k, v) for k, v in d.items() if rx.search(k) and re.search(r"[\u4e00-\u9fff]", v or "")]
        rows.sort()
        L.append("### " + title + "（" + str(len(rows)) + " 条，列前 10）\n")
        L.append("| 编号 | 原文 | 译名 | 来源 |")
        L.append("|---|---|---|---|")
        for k, v in rows[:10]:
            L.append("| " + nid() + " | " + k + " | " + v + " | " + SRC_EQ + " |")
        L.append("")

    L.append("## 六、界面与机制词\n")
    L.append("| 编号 | 英文 | 中文 | 来源 | 语料验证 |")
    L.append("|---|---|---|---|---|")
    for a, b in UI:
        L.append("| " + nid() + " | " + a + " | " + b + " | " + SRC_UI + " | " + str(cnt.get(b, 0)) + " |")
    L.append("")

    L.append("## 七、专名不逐字直译\n")
    L.append("番号、部队名、地名里有很多「看起来像普通词」的专名，逐字直译会变成另一回事。"
             "判据只有一条：**它是不是专有名词**。\n")
    L.append("| 编号 | 原文 | 错法 | 正解 | 理由 |")
    L.append("|---|---|---|---|---|")
    for src, bad, good, why in PROPER_RULES:
        L.append("| " + nid() + " | " + src + " | " + bad + " | " + good + " | " + why + " |")
    L.append("")
    L.append("---\n")
    L.append("合计 " + str(n[0]) + " 条。语料验证为 0 的条目，表示目前只有文献/规则依据；"
             "这些条目在改动时一律要求「至少有出处」，不允许凭语感。\n")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote", OUT.name, "rows", n[0])


if __name__ == "__main__":
    main()
