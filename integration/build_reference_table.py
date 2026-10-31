# -*- coding: utf-8 -*-
"""生成 docs/权威对照表.md：把「文献附录 + 语料统计 + 游戏内现有译法」并排列出。"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
CORPUS = Path(r"D:\Tool\WITE2\corpus")
OUT = PROJECT / "docs" / "权威对照表.md"
TSV = PROJECT / "docs" / "reference" / "abbr_glantz.tsv"

TOK = ["航空兵团", "航空团", "航空兵师", "航空师", "航空兵军", "航空军",
       "集团军群", "方面军", "集团军", "近卫", "防空军", "防空师", "最高统帅部预备队", "统帅部预备队"]


def corpus_stats():
    cnt = Counter()
    files = 0
    chars = 0
    for f in CORPUS.rglob("full.txt"):
        try:
            t = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        files += 1
        chars += len(t)
        for k in TOK:
            cnt[k] += t.count(k)
        cnt["近卫第N"] += len(re.findall(r"近卫\s*第\s*\d+", t))
        cnt["第N近卫"] += len(re.findall(r"第\s*\d+\s*近卫", t))
        cnt["防空第N"] += len(re.findall(r"防空\s*第\s*\d+", t))
        cnt["第N防空"] += len(re.findall(r"第\s*\d+\s*防空", t))
    return cnt, files, chars


AMBIG = [("Coo", "科斯岛"), ("Ana", "阿纳"), ("Pec", "佩奇"), ("Barcellona", "巴切洛纳"),
         ("Radom", "拉多姆"), ("Ostrow", "奥斯特鲁夫"), ("Komotau", "霍穆托夫"),
         ("Ladozhskaya", "拉多加站"), ("Agadyr", "阿加德尔"), ("Athenry", "阿森赖"),
         ("Meaux", "莫城"), ("Orda", "奥尔达"), ("Ordu", "奥尔杜"), ("Gluboky", "格卢博基")]


def coord_table(project: Path) -> str:
    import csv
    import math
    settings = project / "mod" / "settings.local.json"
    try:
        game = json.loads(settings.read_text(encoding="utf-8"))["game_path"]
    except Exception:
        return "_（找不到游戏目录，跳过坐标验证）_"
    path = Path(game) / "Dat" / "CSV" / "1941 Campaign" / "Locations.csv"
    if not path.exists():
        return "_（Locations.csv 不存在）_"
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    rows = list(csv.reader(text.splitlines(keepends=True)))
    h = rows[0]
    ni, xi, yi = h.index("Name"), h.index("X"), h.index("Y")
    pts = []
    for r in rows[1:]:
        if len(r) <= max(ni, xi, yi):
            continue
        try:
            pts.append((r[ni], int(r[xi]), int(r[yi])))
        except ValueError:
            continue
    byname = {n: (x, y) for n, x, y in pts}
    out = ["| 地名 | 定译 | 地图坐标 | 最近的城镇（距离） |", "|---|---|---|---|"]
    for name, zh in AMBIG:
        if name not in byname:
            continue
        x, y = byname[name]
        near = sorted(pts, key=lambda q: (q[1] - x) ** 2 + (q[2] - y) ** 2)[1:6]
        txt = "、".join(f"{n}({math.sqrt((a-x)**2+(b-y)**2):.0f})" for n, a, b in near)
        out.append(f"| {name} | {zh} | ({x},{y}) | {txt} |")
    return "\n".join(out)


def main():
    rows = list(csv.DictReader(TSV.open(encoding="utf-8"), delimiter="\t"))
    cnt, files, chars = corpus_stats()

    L = []
    L.append("# 权威对照表（文献核对）\n")
    L.append("> 本表把三类证据并排：**出版译本附录**（原语→中文的定译）、"
             "**语料用法统计**（中文文献里怎么用）、**游戏内现有译法**。")
    L.append("> 最终采用哪个写在「备注」列，并说明理由。\n")

    L.append("## 一、苏军番号缩写（来源：格兰茨《泥足巨人》中译本 附录「缩写语表」）\n")
    L.append(f"文件：{TSV.relative_to(PROJECT)}，OCR 自纸本第 19–23 页；共 {len(rows)} 条。\n")
    L.append("| 缩写 | 英文 | 译本中文 | 采用说明 |")
    L.append("|---|---|---|---|")
    for r in rows:
        zh = r["chinese"].strip()
        abbr = r["abbr"].strip()
        en = r["english"].strip()
        note = ""
        if abbr == "PVOC":
            note = "「防空」只作隶属前缀，不作建制名"
        elif abbr in ("PVOD", "PVOB"):
            note = "防空师 / 防空旅，可用"
        elif abbr in ("FAD", "FAR,PVO", "FAD,PVO"):
            note = "防空＋歼击航空兵，与「防空第6歼击航空军」同构"
        elif abbr == "Gds":
            note = "近卫，置于「第N」之前"
        elif abbr == "RGK":
            note = "统帅部预备队；РВГК 本级作「最高统帅部预备队」"
        elif zh and "航空兵" in zh:
            note = "本书用「航空兵X」；游戏官方中译用「航空X」，已按游戏统一"
        L.append("| " + abbr + " | " + en + " | " + zh + " | " + note + " |")

    L.append("")
    L.append("## 二、正式出版物单列统计\n")
    L.append("把「书」和「兵棋规则书/游戏手册」分开看，结论会清楚很多。下表只统计五部中文战史"
             "（《泥足巨人》《东线》《斯大林格勒三部曲》《焦土》《地图上的二战·东线战场》）。\n")
    L.append("| 书 | 字数 | 近卫第N | 第N近卫 | 防空第… | 第N防空… |")
    L.append("|---|---|---|---|---|---|")
    book_dirs = ["泥足巨人", "东线", "斯大林格勒1上", "焦土", "地图上的东线"]
    ta = tc = 0
    for b in book_dirs:
        f = CORPUS / b / "full.txt"
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        a = len(re.findall(r"近卫\s*第\s*\d+", t))
        c = len(re.findall(r"第\s*\d+\s*近卫", t))
        ta += a
        tc += c
        L.append("| " + b + " | " + format(len(t) / 1e4, ".0f") + " 万 | " + str(a) + " | " + str(c) +
                 " | " + str(len(re.findall(r"防空\s*第", t))) + " | " +
                 str(len(re.findall(r"第\s*\d+\s*防空", t))) + " |")
    L.append("| **合计** | | **" + str(ta) + "** | **" + str(tc) + "** | | |")
    L.append("")
    L.append("读法：按**书**算，三比一——《焦土》《斯大林格勒三部曲》《地图上的二战·东线战场》"
             "一律「近卫第 N」；朱世巍《东线》全书统一「第 N 近卫」。按**次数**算反过来，"
             "因为《东线》一本就占了四百多次。"
             "本 Mod 取「近卫第 N」，与多数出版物一致；若要与游戏手册写法统一，"
             "把 designations.guards_first 反向跑一次即可。")
    L.append("")
    L.append("## 三、全部语料（含规则书与游戏手册）用法统计\n")
    L.append("语料：" + str(files) + " 份文本、约 " + format(chars / 1e4, ".0f") +
             " 万字（中英混合，含 WitE/WitE2 中文手册、战史与兵棋规则书中文版）。\n")
    L.append("| 说法 | 出现次数 |")
    L.append("|---|---|")
    for k in ["近卫第N", "第N近卫", "防空第N", "第N防空", "航空兵团", "航空团", "航空兵师", "航空师",
              "航空兵军", "航空军", "集团军群", "方面军", "防空军", "防空师",
              "最高统帅部预备队", "统帅部预备队"]:
        L.append("| " + k + " | " + str(cnt.get(k, 0)) + " |")
    L.append("")
    L.append("结论：")
    L.append("- **语序**：证据并不一致，必须按来源分开看——")
    L.append("  - 正式出版物：见上表，焦土/斯大林格勒/地图上的东线用「近卫第 N」，朱世巍《东线》用「第 N 近卫」。")
    L.append("  - WitE2 官方中文手册：「第 N 近卫步兵师」这一类写法更多。")
    L.append("  - 本 Mod 取「近卫第 N」，与正式出版物一致；若要与游戏手册完全统一，"
             "只需把 designations.guards_first 反向运行一次。")
    L.append("- **航空兵 vs 航空**：出版译本用「歼击航空兵师/团」；WitE2 官方中文手册用「歼击航空师/团」。"
             "游戏内显示取后者，长度也更适合计数器。")
    L.append("- **防空**：语料里「第 N 防空」多为英美防空营/集团军；苏军 ПВО 单位在《泥足巨人》附录里写作"
             "「防空歼击航空兵团/防空师/防空旅」——即「防空」作前缀。故「防空第6歼击航空军」与原书构造一致。")

    L.append("")
    L.append("## 三、经文献核对后改动的条目\n")
    ov = json.loads((PROJECT / "glossary" / "reference_overrides.json").read_text(encoding="utf-8"))
    ov_n = [0]
    for group, title in (("places", "地名"), ("ui", "界面词"), ("terms", "术语")):
        items = ov.get(group) or {}
        if not items:
            continue
        L.append("### " + title + "\n")
        L.append("| 编号 | 原文 | 定译 | 依据 |")
        L.append("|---|---|---|---|")
        for src, val in items.items():
            ov_n[0] += 1
            L.append("| R-%03d | " % ov_n[0] + src + " | " + val[0] + " | " +
                     (val[1] if len(val) > 1 else "") + " |")
        L.append("")

    L.append("## 四、坐标验证（对有争议的地名）\n")
    L.append("有些地名光看英文名分不清是哪个城（Barcellona 是西西里小镇还是巴塞罗那？"
             "Coo 是爱琴海科斯岛还是别的？）。做法：取 Locations.csv 的 X/Y，"
             "找最近的 8 个城镇，看它落在哪个国家/地区。\n")
    L.append(coord_table(PROJECT))
    L.append("")
    L.append("## 五、存疑与未决\n")
    L.append("- FBD 的德文全称两说（Baudirektion / Betriebsdirektion），暂用中性「野战铁道局」。")
    L.append("- RHG 严格义为「集团军群后方地域」，作为番号前缀取简「后方军区」。")
    L.append("- 罗马尼亚/匈牙利/意大利等仆从国部队，游戏内一律用英文缩写（Rum./Hun./Ital.），"
             "其本国语言番号（Divizia / hadosztály 等）尚未系统核对。")
    L.append("- 后续：把《焦土》《东线》《斯大林格勒三部曲》OCR 跑完后，"
             "再对地名词表做一次全量交叉核对（目前只逐个确认了已发现的错译）。")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote", OUT.name, "rows", len(rows), "files", files, "chars", chars)


if __name__ == "__main__":
    main()
