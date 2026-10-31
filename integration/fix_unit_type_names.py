# -*- coding: utf-8 -*-
"""修正「名称里的类型词与编制不符」的部队名。

游戏里单位面板显示「名称 + 编制类型」，名称里再自带一个类型就重复；
若两者矛盾（如名称写「师」而编制是营），就是硬伤。

处理两类：
  1) 纯「…第N师/旅/团/营/军」→ 去掉类型词，交给编制类型显示；
  2) 「第N师/第M师」这种双编号子单位 → 改成「第N/第M」。
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
PLAN = Path(r"D:\Tool\WITE2\_work\type_strip.json")
DATA = PROJECT / "data"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"


def main() -> None:
    plan = {x["name"]: x["new"] for x in json.loads(PLAN.read_text(encoding="utf-8"))}
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
            r = json.loads(line)
            src = r.get("text")
            if isinstance(src, str) and src in plan and r.get("translation") != plan[src]:
                r["translation"] = plan[src]
                dirty = True
                n += 1
            rows.append(r)
        if dirty:
            with path.open("w", encoding="utf-8", newline="\n") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

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
                if s[i] in plan and z[i] != plan[s[i]]:
                    z[i] = plan[s[i]]
                    dirty = True
                    cells += 1
        if dirty:
            with zh.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(zrows)
    print(f"jsonl={n} csv_cells={cells}")


if __name__ == "__main__":
    main()
