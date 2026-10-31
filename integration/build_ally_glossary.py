# -*- coding: utf-8 -*-
"""生成 docs/仆从国番号对照表.md。"""
from __future__ import annotations

from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
CORPUS = Path(r"D:\Tool\WITE2\corpus")
OUT = PROJECT / "docs" / "仆从国番号对照表.md"

LANGS = [
    ("罗马尼亚", "ro", "Rum. / Rumanian / Romanian"),
    ("匈牙利", "hu", "Hun. / Hungarian"),
    ("意大利", "it", "Ital. / Italian / CSIR / ARMIR"),
    ("芬兰", "fi", "Fin. / Finnish"),
    ("斯洛伐克", "sk", "Slov. / Slovakian"),
    ("克罗地亚", "hr", "Croat. / Croatian"),
    ("西班牙", "es", "Span. / Spanish (Blue Division)"),
]

WORDS = {
    "ro": [("divizie", "师"), ("brigadă", "旅"), ("regiment", "团"), ("batalion", "营"),
           ("corp", "军"), ("armată", "集团军"), ("infanterie", "步兵"), ("cavalerie", "骑兵"),
           ("vânători de munte", "山地猎兵"), ("blindată", "装甲"), ("gardă", "卫队"),
           ("grăniceri", "边防"), ("artilerie", "炮兵")],
    "hu": [("hadosztály", "师"), ("dandár", "旅"), ("ezred", "团"), ("zászlóalj", "营"),
           ("hadtest", "军"), ("hadsereg", "集团军"), ("gyalogos", "步兵"), ("huszár", "骠骑兵"),
           ("hegyi", "山地"), ("páncélos", "装甲"), ("honvéd", "国防军（洪韦德）"),
           ("határőr", "边防"), ("tüzér", "炮兵")],
    "it": [("divisione", "师"), ("brigata", "旅"), ("reggimento", "团"), ("battaglione", "营"),
           ("corpo d'armata", "军"), ("armata", "集团军"), ("fanteria", "步兵"),
           ("cavalleria", "骑兵"), ("alpini", "阿尔卑斯山地兵"), ("bersaglieri", "狙击兵"),
           ("celere", "快速"), ("corazzata", "装甲"), ("CC.NN.", "黑衫军")],
    "fi": [("divisioona", "师"), ("prikaati", "旅"), ("rykmentti", "团"), ("pataljoona", "营"),
           ("armeijakunta", "军"), ("armeija", "集团军"), ("jalkaväki", "步兵"),
           ("ratsuväki", "骑兵"), ("panssari", "装甲"), ("rajajääkäri", "边防猎兵"),
           ("tykistö", "炮兵")],
    "sk": [("divízia", "师"), ("brigáda", "旅"), ("pluk", "团"), ("prápor", "营"),
           ("zbor", "军"), ("armáda", "集团军"), ("pešia", "步兵"), ("rýchla", "快速"),
           ("horská", "山地"), ("delostrelectvo", "炮兵")],
    "hr": [("divizija", "师"), ("brigada", "旅"), ("pukovnija", "团"), ("bojna", "营"),
           ("zbor", "军"), ("pješačka", "步兵"), ("gorska", "山地"), ("ustaška", "乌斯塔沙")],
    "es": [("división", "师"), ("regimiento", "团"), ("batallón", "营"),
           ("infantería", "步兵"), ("azul", "蓝色（蓝色师）")],
}

PROPER = [
    ("Pasubio", "帕苏比奥", "意大利第9摩托化师，以维琴察附近的帕苏比奥山命名"),
    ("Torino", "都灵", "意大利第52摩托化师"),
    ("Tridentina", "特里登蒂纳", "意大利第2阿尔卑斯山地师，以特伦托（Tridentum）命名"),
    ("Principe Amedeo", "阿梅代奥亲王", "意大利第3骑兵师"),
    ("Sforzesca", "斯福尔扎", "意大利第2步兵师"),
    ("Cosseria", "科塞里亚", "意大利第5步兵师"),
    ("Ravenna", "拉文纳", "意大利第3步兵师"),
    ("Cuneense", "库内奥", "意大利第1阿尔卑斯山地师"),
    ("Julia", "朱利亚", "意大利第3阿尔卑斯山地师"),
    ("Vicenza", "维琴察", "意大利第2步兵师"),
    ("Szekler", "塞凯伊", "匈牙利塞凯伊边防旅（特兰西瓦尼亚匈牙利族）"),
    ("St. Laszlo", "圣拉斯洛", "匈牙利圣拉斯洛卫队师"),
    ("Antonescu", "安东内斯库", "罗马尼亚安东内斯库集团军群"),
]

CALIB = [
    ("Hun. Light Division", "匈牙利轻型师", "匈牙利轻装师", "匈牙利轻装师是编制概念（könnyű hadosztály），与坦克的轻型无关"),
    ("Rum./Hun./Ital./Fin./Slov. 番号", "第3罗马尼亚集团军", "罗马尼亚第3集团军", "汉语国名前置，202 条统一"),
    ("3 Gennaio", "3月21日", "1月3日", "意大利黑衫军师按纪念日命名，Gennaio=1 月"),
    ("Ital. Alpina Division", "意大利阿尔卑斯师", "意大利阿尔卑斯山地师", "Alpini=阿尔卑斯山地兵，不是地名"),
]

DATE_NAMES = [
    ("3 Gennaio", "1月3日", "黑衫军师的纪念日命名"),
    ("23 Marzo", "3月23日", "1919 年 3 月 23 日法西斯战斗团成立"),
    ("21 Aprile", "4月21日", "罗马建城纪念日"),
    ("28 Ottobre", "10月28日", "1922 年向罗马进军"),
]


def corpus_count(term):
    n = 0
    for f in CORPUS.rglob("full.txt"):
        try:
            t = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        n += t.count(term)
    return n


def main():
    L = []
    n = [0]

    def nid():
        n[0] += 1
        return "P-%03d" % n[0]

    L.append("# 仆从国番号对照表（本国语言 / 英文 / 中文）\n")
    L.append("> 起因：游戏里仆从国部队一律用英文缩写（Rum. / Hun. / Ital. / Fin. / Slov.），")
    L.append("> 但它们本来有自己的番号体系，直接按英文转手会丢掉「师/旅/军」的真实层级。")
    L.append("> 本表给出本国语言建制词 → 中文，以及专名（师名）与日期命名师的处置。\n")
    L.append("编号 P-xxx；语料验证 = 该中文在本机语料中的出现次数。\n")

    L.append("## 一、参战国与语言\n")
    L.append("| 编号 | 国家 | 语言代码 | 游戏内写法 |")
    L.append("|---|---|---|---|")
    for zh, code, game in LANGS:
        L.append("| " + nid() + " | " + zh + " | " + code + " | " + game + " |")
    L.append("")

    L.append("## 二、文献依据\n")
    L.append("本轮仆从国文献（已转成文本，可直接检索；路径为 mod 仓库外的文献库）：\n")
    L.append("| 编号 | 文献 | 语种 | 覆盖 | 本地文件 |")
    L.append("|---|---|---|---|---|")
    L.append("| " + nid() + " | Hurri J. Finnish TO&E 1941–1944: from divisions to platoons. Rev. 0.83, 2002. | 英文（含芬兰语术语） | 芬兰：师/旅/团/营编制、Jääkäri、Panssari | 04_仆从国\\Finnish_TOE_1941-1944.pdf |")
    L.append("| " + nid() + " | Falk V A. Of Fire, Iron and Blood, Vol. 1: A Short History of the Royal Hungarian Honvéd Army in the Second World War. | 英文 | 匈牙利：Honvéd 军制、集团军战斗序列 | 04_仆从国\\Falk_Hungarian_Honved_Army.pdf |")
    L.append("| " + nid() + " | United States. War Department. Order of Battle of the Italian Army. 1943. | 英文（含意大利语番号） | 意大利：Divisione / Reggimento / Battaglione、Bersaglieri、Alpini | 02_德军编制\\USWarDept_1943_OrderOfBattleItalianArmy.pdf |")
    L.append("| " + nid() + " | Vojenská história 1/2007. Vojenský historický ústav Bratislava. | 斯洛伐克文 | 斯洛伐克：divízia / pluk / prápor / zbor | 04_仆从国\\SK_VHU_boj_za_slobodu.pdf |")
    L.append("")
    L.append("未能下载（需自行获取）：罗马尼亚国防部档案 rft.forter.ro（502）、File din istoria militară 期刊 biblioteca-digitala.ro（403）。")
    L.append("")
    L.append("## 三、建制词（本国语言 → 中文）\n")
    for zh, code, _ in LANGS:
        if code not in WORDS:
            continue
        L.append("### " + zh + "（" + code + "）\n")
        L.append("| 编号 | 本国语言 | 中文 | 语料验证 |")
        L.append("|---|---|---|---|")
        for nat, cn in WORDS[code]:
            L.append("| " + nid() + " | " + nat + " | " + cn + " | " + str(corpus_count(cn)) + " |")
        L.append("")

    L.append("## 四、师名（专名，音译）\n")
    L.append("| 编号 | 原名 | 中文 | 说明 |")
    L.append("|---|---|---|---|")
    for nat, cn, note in PROPER:
        L.append("| " + nid() + " | " + nat + " | " + cn + " | " + note + " |")
    L.append("")

    L.append("## 五、按日期命名的意大利师\n")
    L.append("意大利黑衫军师用纪念日命名，不能按字面拆成「第 23 三月」：\n")
    L.append("| 编号 | 原名 | 中文 | 说明 |")
    L.append("|---|---|---|---|")
    for nat, cn, note in DATE_NAMES:
        L.append("| " + nid() + " | " + nat + " | " + cn + " | " + note + " |")
    L.append("")

    L.append("## 六、汉语语序\n")
    L.append("仆从国部队一律国名在前：罗马尼亚第3集团军、匈牙利第2集团军、意大利第8集团军、")
    L.append("芬兰第2军、斯洛伐克快速师。原来的「第3罗马尼亚集团军」式写法已全部改为国名前置")
    L.append("（202 条，脚本 integration/fix_ally_designations.py）。\n")

    L.append("## 七、本轮据此校准的条目\n")
    L.append("| 编号 | 原文 | 旧译 | 现译 | 依据 |")
    L.append("|---|---|---|---|---|")
    for src, old, new, why in CALIB:
        L.append("| " + nid() + " | " + src + " | " + old + " | " + new + " | " + why + " |")
    L.append("")
    L.append("## 八、尚未解决\n")
    L.append("- 罗马尼亚 vânători de munte（山地猎兵）、匈牙利 honvéd 等民族性军语，")
    L.append("  中文文献译法不统一（山地猎兵 / 山地兵；洪韦德 / 国防军），本表取描述性译法。")
    L.append("- 芬兰 ryhmä（战斗群）、osasto（支队）等临时编组名，语料里没有稳定译法。")
    L.append("- 克罗地亚乌斯塔沙部队的建制名尚未逐条核对。\n")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote", OUT.name, "rows", n[0])


if __name__ == "__main__":
    main()
