# -*- coding: utf-8 -*-
"""按德文/英文字面规范，统一装备名译法。

只做四类有把握的改动，全部以「英文原文 + 现有译文」为依据：
  1) Howitzer 必须是「榴弹炮」——原译里混进了「加农炮」
  2) AT-Rifle 必须是「反坦克枪」——原译有「反坦克武器」
  3) Field Gun 统一「野战炮」——原译「野炮 / 野战火炮」并存
  4) Flak 误译成「密集阵」的改回「高射炮」
另外把口径里的 cm 换算成毫米（8.8cm -> 88毫米）。
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
EQ = PROJECT / "data" / "scenario_csv" / "translations" / "equipment.zh.jsonl"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"

CM = re.compile(r"(\d+(?:\.\d+)?)\s*cm\b")


def norm_cm(src: str, zh: str) -> str:
    m = CM.search(src)
    if not m:
        return zh
    val = float(m.group(1)) * 10
    mm = str(int(val)) if abs(val - round(val)) < 1e-6 else str(round(val, 1))
    return re.sub(r"\d+(?:\.\d+)?\s*(?:cm|厘米)", mm + "毫米", zh, count=1)


def fix(src: str, zh: str) -> str:
    if not zh:
        return zh
    s, z = src, zh
    if "Howitzer" in s and "榴弹炮" not in z:
        z = z.replace("骡马炮", "驮载榴弹炮")
        z = re.sub(r"(迫击炮|加农炮|均衡炮|野炮|火炮|炮)$", "榴弹炮", z)
    if "AT-Rifle" in s:
        if "反坦克枪" not in z:
            z = re.sub(r"反坦克(?:武器|步枪|枪)?", "反坦克枪", z)
            if "反坦克枪" not in z:
                z = z + "反坦克枪"
    if "Field Gun" in s and "野战炮" not in z:
        z = re.sub(r"(榴弹炮|野炮|野战火炮|火炮|炮)$", "野战炮", z)
    if "Flak" in s:
        z = z.replace("密集阵", "高射炮")
    z = norm_cm(s, z)
    return z


def main() -> None:
    rows = [json.loads(l) for l in EQ.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    n = 0
    for r in rows:
        src = r.get("text") or ""
        old = r.get("translation") or ""
        new = fix(src, old)
        if new != old:
            r["translation"] = new
            n += 1
    with EQ.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("equipment jsonl fixed:", n)

    from fix_scenario_names import find_game, load_rows
    game = find_game()
    base = game / "Dat" / "CSV"
    cells = 0
    for zhf in sorted(CSVDIR.rglob("*.zh.csv")):
        rel = zhf.relative_to(CSVDIR)
        src_p = base / rel.parent.name / rel.name.replace(".zh.csv", ".csv")
        if not src_p.exists():
            continue
        srows, _ = load_rows(src_p)
        zrows, bom = load_rows(zhf)
        if len(srows) != len(zrows):
            continue
        dirty = False
        for s, z in zip(srows, zrows):
            for i in range(min(len(s), len(z))):
                if not s[i] or not z[i]:
                    continue
                if not re.search(r"Howitzer|AT-Rifle|Field Gun|Flak|\dcm", s[i]):
                    continue
                new = fix(s[i], z[i])
                if new != z[i]:
                    z[i] = new
                    dirty = True
                    cells += 1
        if dirty:
            with zhf.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(zrows)
    print("csv cells fixed:", cells)


if __name__ == "__main__":
    main()
