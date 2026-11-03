
# -*- coding: utf-8 -*-
"""Apply curated leader-name fixes to leader jsonl and every built Leaders.zh.csv."""
from __future__ import annotations
import csv, json, os, sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data" / "scenario_csv" / "translations"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"
FIXES = PROJECT / "glossary" / "leader_name_fixes.json"


def game_path() -> Path:
    s = PROJECT / "mod" / "settings.local.json"
    if s.exists():
        p = json.loads(s.read_text(encoding="utf-8")).get("game_path")
        if p:
            return Path(p)
    raise SystemExit("settings.local.json 缺 game_path")


def load_fixes():
    items = json.loads(FIXES.read_text(encoding="utf-8"))
    return {(x["column"], x["source"]): x["new"] for x in items}


def apply_jsonl(fixes) -> int:
    n = 0
    for name in ("leader.zh.jsonl", "leader.zh.qa.jsonl"):
        p = DATA / name
        if not p.exists():
            continue
        rows, dirty = [], False
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            key = (o.get("column"), o.get("text"))
            if key in fixes and o.get("translation") != fixes[key]:
                o["translation"] = fixes[key]
                o["qa_status"] = "ok"
                dirty = True
                n += 1
            rows.append(o)
        if dirty:
            p.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n",
                         encoding="utf-8", newline="\n")
    return n


def apply_csv(fixes) -> int:
    game = game_path()
    base = game / "Dat" / "CSV"
    n = 0
    name_fix = {k[1]: v for k, v in fixes.items() if k[0] == "Name"}
    first_fix = {k[1]: v for k, v in fixes.items() if k[0] == "FirstName"}
    for zh in sorted(CSVDIR.glob("*/Leaders.zh.csv")):
        src = base / zh.parent.name / "Leaders.csv"
        if not src.exists():
            print("skip (no source):", zh)
            continue
        with src.open(encoding="utf-8-sig", errors="replace", newline="") as f:
            srows = list(csv.reader(f))
        bom = zh.read_bytes()[:3] == bytes([239, 187, 191])
        with zh.open(encoding="utf-8-sig", errors="replace", newline="") as f:
            zrows = list(csv.reader(f))
        if not srows or len(srows) != len(zrows):
            print("skip (row mismatch):", zh)
            continue
        sh, zh_h = srows[0], zrows[0]
        if len(sh) != len(zh_h):
            print("skip (column mismatch):", zh)
            continue
        # 表头可能已被翻译（名称/FirstName），按源表列序定位，不按译名找列
        for col, fmap in (("Name", name_fix), ("FirstName", first_fix)):
            if col not in sh:
                continue
            si = zi = sh.index(col)
            for s, z in zip(srows[1:], zrows[1:]):
                if len(s) <= si or len(z) <= zi:
                    continue
                new = fmap.get(s[si])
                if new and z[zi] != new:
                    z[zi] = new
                    n += 1
        with zh.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
            csv.writer(f).writerows(zrows)
    return n


def main() -> None:
    fixes = load_fixes()
    a = apply_jsonl(fixes)
    b = apply_csv(fixes)
    print(f"jsonl cells: {a}; csv cells: {b}; fixes: {len(fixes)}")


if __name__ == "__main__":
    main()
