# -*- coding: utf-8 -*-
"""修正国名缩写被误译的番号：Bul.（保加利亚）曾译成「布良斯克」、Pol.（波兰）译成「波军」或丢失。

规则：
  Bul. <兵种编制>  → 保加利亚<兵种编制>
  <N> Pol.         → 波兰第 N
  <N> SS Est.      → 爱沙尼亚党卫军第 N
  Pol. <兵种>      → 波兰<兵种>
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

DATA = PROJECT / "data"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"

PREFIX = {"Bul.": "保加利亚", "Pol.": "波兰", "Est.": "爱沙尼亚",
          "Latv.": "拉脱维亚", "Lit.": "立陶宛", "Ukr.": "乌克兰"}


def fix(src: str) -> str | None:
    s = src.strip()
    m = re.fullmatch(r"(\d+)(?:st|nd|rd|th)?\s+Pol\.", s)
    if m:
        return "波兰第" + m.group(1)
    m = re.fullmatch(r"(\d+)(?:st|nd|rd|th)?\s+SS\s+Est\.", s)
    if m:
        return "爱沙尼亚党卫军第" + m.group(1)
    m = re.fullmatch(r"(\d+)/(\d+)(?:st|nd|rd|th)?\s+SS\s+Est\.", s)
    if m:
        return "爱沙尼亚党卫军第%s/%s" % (m.group(1), m.group(2))
    m = re.fullmatch(r"(\d+)(?:st|nd|rd|th)?\s+Bul\.", s)
    if m:
        return "保加利亚第" + m.group(1)
    for abbr, zh in PREFIX.items():
        if s.startswith(abbr + " "):
            rest = s[len(abbr) + 1:]
            tail = D.ob_phrase(rest) or rest
            return zh + tail
    return None


def main() -> None:
    n = 0
    for path in sorted(DATA.rglob("*.jsonl")):
        if "extracted" in path.parts:
            continue
        text = path.read_text(encoding="utf-8-sig")
        if not text.strip():
            continue
        rows, dirty = [], False
        for line in text.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            src, tr = row.get("text"), row.get("translation")
            if isinstance(src, str):
                new = fix(src)
                if new and new != tr:
                    row["translation"] = new
                    dirty = True
                    n += 1
            rows.append(row)
        if dirty:
            with path.open("w", encoding="utf-8", newline="\n") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

    from fix_scenario_names import find_game, load_rows
    game = find_game()
    base = game / "Dat" / "CSV"
    cells = 0
    for zh in sorted(CSVDIR.rglob("*.zh.csv")):
        rel = zh.relative_to(CSVDIR)
        src_p = base / rel.parent.name / rel.name.replace(".zh.csv", ".csv")
        if not src_p.exists():
            continue
        srows, _ = load_rows(src_p)
        zrows, bom = load_rows(zh)
        if len(srows) != len(zrows):
            continue
        dirty = False
        for s, z in zip(srows, zrows):
            for i in range(min(len(s), len(z))):
                new = fix(s[i])
                if new and z[i] != new:
                    z[i] = new
                    dirty = True
                    cells += 1
        if dirty:
            with zh.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(zrows)
    print(f"jsonl={n} csv_cells={cells}")


if __name__ == "__main__":
    main()
