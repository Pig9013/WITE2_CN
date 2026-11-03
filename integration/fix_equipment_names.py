
# -*- coding: utf-8 -*-
"""应用装备名修订表到 equipment jsonl 与 build 场景 CSV。"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data" / "scenario_csv" / "translations"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"
FIXES = PROJECT / "glossary" / "equipment_name_fixes.json"


def load_fixes():
    items = json.loads(FIXES.read_text(encoding="utf-8"))
    return {(x["source"], x["old"]): x["new"] for x in items}


def apply_jsonl(fixes):
    n = 0
    for name in ("equipment.zh.jsonl", "equipment.zh.qa.jsonl"):
        p = DATA / name
        if not p.exists():
            continue
        rows, dirty = [], False
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            key = (o.get("source"), o.get("text"))
            if key in fixes and o.get("translation") != fixes[key]:
                o["translation"] = fixes[key]
                dirty = True
                n += 1
            rows.append(o)
        if dirty:
            p.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n",
                         encoding="utf-8", newline="\n")
    return n


def load(path):
    raw = path.read_bytes()
    bom = raw[:3] == bytes([239, 187, 191])
    enc = "utf-8-sig" if bom else "utf-8"
    try:
        text = raw.decode(enc)
    except UnicodeDecodeError:
        enc = "cp1252"
        text = raw.decode(enc)
    return list(csv.reader(text.splitlines(keepends=True))), bom, enc


def apply_csv(fixes):
    game = json.loads((PROJECT / "mod" / "settings.local.json").read_text(encoding="utf-8"))["game_path"]
    base = Path(game) / "Dat" / "CSV"
    n = 0
    for zh in sorted(CSVDIR.glob("*/*.zh.csv")):
        base_name = zh.name[:-7] + ".csv"
        if base_name not in ("Ground.csv", "Aircraft.csv", "Devices.csv"):
            continue
        src = base / zh.parent.name / base_name
        if not src.exists():
            continue
        srows, _, _ = load(src)
        zrows, bom, enc = load(zh)
        if not srows or len(srows) != len(zrows):
            continue
        if "Name" not in srows[0] or len(srows[0]) != len(zrows[0]):
            continue
        ni = srows[0].index("Name")
        for s, z in zip(srows[1:], zrows[1:]):
            if ni >= len(s) or ni >= len(z):
                continue
            new = fixes.get((base_name, s[ni]))
            if new and z[ni] != new:
                z[ni] = new
                n += 1
        with zh.open("w", encoding=enc, newline="") as f:
            csv.writer(f).writerows(zrows)
    return n


def main():
    fixes = load_fixes()
    a = apply_jsonl(fixes)
    b = apply_csv(fixes)
    print(f"jsonl cells: {a}; csv cells: {b}; fixes: {len(fixes)}")


if __name__ == "__main__":
    main()
