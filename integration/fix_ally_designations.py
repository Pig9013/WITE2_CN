# -*- coding: utf-8 -*-
"""仆从国部队番号的汉语语序与专名订正。

中文惯例是「国名 + 第 N + 兵种 + 建制」（罗马尼亚第3集团军、匈牙利第2集团军），
而不是「第 N + 国名」。另修几个意大利师名（按日期/人名命名的）。
只改短名（不含句读、长度 <= 24），长篇描述不动。
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"

NAT = "罗马尼亚|匈牙利|意大利|芬兰|斯洛伐克|克罗地亚|保加利亚|西班牙"
PAT = re.compile(r"^第\s*(\d+)\s*(%s)(.*)$" % NAT)
NAME_FIX = {
    "3rd Gennaio": "1月3日",
    "23rd Marzo": "3月23日",
    "3rd Principe Amedeo": "阿梅代奥亲王第3",
    "2nd Tridentina": "特里登蒂纳第2",
    "9th Pasubio": "帕苏比奥第9",
    "52nd Torino": "都灵第52",
    "CSIR Italian Air Bde": "意大利驻俄远征军航空旅",
}


def reorder(v: str) -> str | None:
    if len(v) > 24 or re.search(r"[，。；：()（）\n]", v):
        return None
    m = PAT.match(v)
    if not m:
        return None
    return m.group(2) + "第" + m.group(1) + m.group(3)


def fix_value(src: str, v: str) -> str | None:
    if src in NAME_FIX and v != NAME_FIX[src]:
        return NAME_FIX[src]
    return reorder(v)


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
            if isinstance(src, str) and isinstance(tr, str):
                new = fix_value(src, tr)
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
                if not z[i]:
                    continue
                new = fix_value(s[i], z[i])
                if new and new != z[i]:
                    z[i] = new
                    dirty = True
                    cells += 1
        if dirty:
            with zh.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(zrows)
    # 词表类 CSV（build_maps 后读，会覆盖 jsonl）
    for rel, kc, vc in (("data/translations/unit_names_en_zh.csv", "en", "zh"),
                        ("build/translation.csv", "English Key", "Translated Text"),
                        ("mod/assets/translation.csv", "English Key", "Translated Text")):
        path = PROJECT / rel
        if not path.exists():
            continue
        raw = path.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        rows = list(csv.reader(raw.decode("utf-8-sig").splitlines(keepends=True)))
        if not rows:
            continue
        header = rows[0]
        if kc not in header or vc not in header:
            continue
        ki, vi = header.index(kc), header.index(vc)
        dirty = False
        for row in rows[1:]:
            if len(row) <= max(ki, vi):
                continue
            new = fix_value(row[ki], row[vi])
            if new and new != row[vi]:
                row[vi] = new
                dirty = True
                cells += 1
        if dirty:
            with path.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(rows)

    print(f"jsonl={n} cells={cells}")


if __name__ == "__main__":
    main()
