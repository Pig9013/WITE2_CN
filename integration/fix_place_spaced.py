# -*- coding: utf-8 -*-
"""修「字母之间被拆开」的地名键（如 'M o s c o w'），以及一批明显的地区名错译。

这类键来自游戏文本里为字距排开的地名，译文质量参差：
有的照抄空格变体、有的干脆译错（Cotentin -> 诺曼底登陆、Zealand -> 新西兰、
Westphalia -> 西里西亚）。规则两条：
  1) 折叠空格后若已有同名键，直接用它的译文；
  2) 其余按 FIX 表逐条改（每条都能对到真实地名）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
PLACE = PROJECT / "data" / "scenario_csv" / "translations" / "place.zh.jsonl"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"

# 折叠后仍无同名键、且译文明显错的
FIX = {
    "Cotentin": "科唐坦半岛",
    "Grampians": "格兰扁山脉",
    "Skye": "斯凯岛",
    "Connaught": "康诺特",
    "Leinster": "伦斯特",
    "Munster": "芒斯特",
    "Ulster": "阿尔斯特",
    "Dodecanese": "十二群岛",
    "Cyclades": "基克拉泽斯群岛",
    "Muntenia": "蒙特尼亚",
    "Oltenia": "奥尔特尼亚",
    "Crisana": "克里沙纳",
    "Wartheland": "瓦尔特兰",
    "Westphalia": "威斯特法伦",
    "Zealand": "西兰岛",
    "Funen": "菲英岛",
    "Jutland": "日德兰半岛",
    "Wuerttemberg": "符腾堡",
    "Ruthenia": "鲁塞尼亚",
    "Bothnia": "博滕",
    "Attica": "阿提卡",
    "Moesia": "默西亚",
    "Carinthia": "克恩顿",
    "Styria": "施泰尔马克",
    "Dobrogea": "多布罗加",
    "Herzegovina": "黑塞哥维那",
    "Volhynia": "沃里尼亚",
    "Masuria": "马祖里",
    "Erne": "厄恩河",
    "Pfalz": "普法尔茨",
    "Massif": "山块",
    "Central": "中央",
}

SPACED = re.compile(r"(?:[A-Za-z] ){2,}[A-Za-z]")


def main() -> None:
    rows = [json.loads(l) for l in PLACE.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    plain = {(r.get("text") or "").strip(): (r.get("translation") or "") for r in rows}
    copied = fixed = 0
    for r in rows:
        t = (r.get("text") or "").strip()
        if not SPACED.fullmatch(t):
            continue
        base = t.replace(" ", "")
        if base in plain and plain[base]:
            if r.get("translation") != plain[base]:
                r["translation"] = plain[base]
                copied += 1
        elif base in FIX:
            if r.get("translation") != FIX[base]:
                r["translation"] = FIX[base]
                fixed += 1
    with PLACE.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"jsonl spaced keys copied={copied} fixed={fixed}")

    # 同名键在场景 CSV 里也有副本（build_maps 最后读 CSV，会覆盖 jsonl），一并处理
    import csv
    from fix_scenario_names import find_game, load_rows  # 同目录脚本
    game = find_game()
    base_dir = game / "Dat" / "CSV"
    csv_copied = csv_fixed = 0
    for zh in sorted(CSVDIR.rglob("*.zh.csv")):
        rel = zh.relative_to(CSVDIR)
        src_p = base_dir / rel.parent.name / rel.name.replace(".zh.csv", ".csv")
        if not src_p.exists():
            continue
        srows, _ = load_rows(src_p)
        zrows, bom = load_rows(zh)
        if len(srows) != len(zrows):
            continue
        plain_map = {}
        for s, z in zip(srows, zrows):
            for i in range(min(len(s), len(z))):
                if s[i] and s[i].strip() and not SPACED.fullmatch(s[i].strip()):
                    plain_map.setdefault(s[i].strip(), z[i])
        dirty = False
        for s, z in zip(srows, zrows):
            for i in range(min(len(s), len(z))):
                t = (s[i] or "").strip()
                if not t or not SPACED.fullmatch(t):
                    continue
                b = t.replace(" ", "")
                want = plain_map.get(b) or FIX.get(b)
                if want and z[i] != want:
                    z[i] = want
                    dirty = True
                    csv_copied += 1
        if dirty:
            with zh.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(zrows)
    print(f"csv spaced cells fixed={csv_copied}")


if __name__ == "__main__":
    main()
