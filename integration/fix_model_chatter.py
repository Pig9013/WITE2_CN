# -*- coding: utf-8 -*-
"""清掉译文里混入的模型自述文字（「注：…」「没有提供…」「正确译文如下」等）。

这些是早期本地模型把「思考过程」写进输出留下的，会直接显示在游戏里。
判定：含自述标记的行整行丢弃；剩下的若只有一段，就用它。
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"

MARK = re.compile(r"注[:：]|请使用|没有提供|MemoryWarning|正确译文|译文[:：]|术语表|建议|备注[:：]|由于")
PAREN = re.compile(r"[（(][^（()）]*?(?:没有提供|术语表|无法|建议)[^（()）]*?[）)]")


MANUAL = {
    "Axis Vehicle Repair Rate": "轴心国车辆维修率",
    "5 LockIn gScen.game IN": "锁定游戏场景",
    "On Turn": "第几回合",
}


def clean(v: str, src: str) -> str | None:
    if src in MANUAL:
        return MANUAL[src] if v != MANUAL[src] else None
    if not re.search(r"注[:：]|请使用|没有提供|MemoryWarning|正确译文|译文[:：]", v):
        return None
    v2 = PAREN.sub("", v)
    lines = [ln.strip() for ln in v2.splitlines()]
    keep = [ln for ln in lines if ln and not MARK.search(ln)]
    if not keep:
        return src
    # 取最后一段（模型往往在末尾给出修正后的译文）
    out = keep[-1]
    out = re.sub(r"\s{2,}", " ", out).strip(" 　-—·")
    return out or src


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
            tr, src = row.get("translation"), row.get("text")
            if isinstance(tr, str) and isinstance(src, str):
                new = clean(tr, src)
                if new is not None and new != tr:
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
                if not z[i]:
                    continue
                new = clean(z[i], s[i])
                if new is not None and new != z[i]:
                    z[i] = new
                    dirty = True
                    cells += 1
        if dirty:
            with zh.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(zrows)
    print(f"jsonl fixed={n} csv_cells={cells}")


if __name__ == "__main__":
    main()
