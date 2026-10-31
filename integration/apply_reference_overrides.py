# -*- coding: utf-8 -*-
"""把 glossary/reference_overrides.json 里经过文献核对定译的词条写回数据源。

只做精确匹配替换（源文完全一致才换），不碰别的。
覆盖 data/**/*.jsonl 与 build/scenario_csv_zh/**/*.zh.csv。
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "glossary"))
import designations as D  # noqa: E402

DATA = PROJECT / "data"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"


def main() -> None:
    changed = 0
    hit_files = set()
    for path in sorted(DATA.rglob("*.jsonl")):
        if "extracted" in path.parts:      # 原始抽取语料，不是译文，不能写 translation
            continue
        text = path.read_text(encoding="utf-8-sig")
        if not text.strip():
            continue
        rows, dirty = [], False
        for line in text.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            src = row.get("text")
            new = D.reference_fix(src) if isinstance(src, str) else None
            if new and row.get("translation") != new:
                row["translation"] = new
                dirty = True
                changed += 1
            rows.append(row)
        if dirty:
            hit_files.add(path.name)
            with path.open("w", encoding="utf-8", newline="\n") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # 场景 CSV：需要原文列做对照
    from fix_scenario_names import find_game, load_rows
    game = find_game()
    base = game / "Dat" / "CSV"
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
                new = D.reference_fix(s[i])
                if new and z[i] != new:
                    z[i] = new
                    dirty = True
                    changed += 1
        if dirty:
            hit_files.add(zh.name)
            with zh.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(zrows)

    # 词表类 CSV（键在前、译文在后），一并处理，否则 build_maps 后读会覆盖
    for rel, key_col, val_col in (("build/translation.csv", "English Key", "Translated Text"),
                                  ("mod/assets/translation.csv", "English Key", "Translated Text"),
                                  ("glossary/ui_en_zh.csv", "en", "zh"),
                                  ("glossary/ui_extra.csv", "en", "zh")):
        path = PROJECT / rel
        if not path.exists():
            continue
        raw = path.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        rows = list(csv.reader(raw.decode("utf-8-sig").splitlines(keepends=True)))
        if not rows:
            continue
        header = rows[0]
        if key_col not in header or val_col not in header:
            continue
        ki, vi = header.index(key_col), header.index(val_col)
        dirty = False
        for row in rows[1:]:
            if len(row) <= max(ki, vi):
                continue
            new = D.reference_fix(row[ki])
            if new and row[vi] != new:
                row[vi] = new
                dirty = True
                changed += 1
        if dirty:
            hit_files.add(path.name)
            with path.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(rows)

    print(f"changed cells: {changed}")
    print("files:", ", ".join(sorted(hit_files)))


if __name__ == "__main__":
    main()
