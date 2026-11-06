# -*- coding: utf-8 -*-
"""应用装备名修订表到 equipment jsonl 与 build 场景 CSV。

匹配口径（v1.9.9 第五轮起）：**只按英文原文匹配**，不再按 (来源 CSV, 原文) 匹配。
原因：同一件装备会同时出现在 Devices.csv 与 Ground.csv，旧口径只改被点名的那一张表，
jsonl 里来自另一张表的行不动 —— 于是「修了一个层，游戏里没变」。若同一原文在表里
被要求译成两个不同值，直接报错，不做猜测。
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data" / "scenario_csv" / "translations"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"
FIXES = PROJECT / "glossary" / "equipment_name_fixes.json"
CSV_NAMES = ("Ground.csv", "Aircraft.csv", "Devices.csv")


def load_fixes():
    items = json.loads(FIXES.read_text(encoding="utf-8"))
    fixes, src = {}, {}
    for x in items:
        old, new = x["old"], x["new"]
        if old in fixes and fixes[old] != new:
            raise SystemExit("equipment_name_fixes.json 冲突：%r 同时被要求译成 %r 与 %r"
                             % (old, fixes[old], new))
        fixes[old] = new
        src[old] = x
    return fixes, src


def apply_jsonl(fixes, meta):
    n = add = 0
    for name in ("equipment.zh.jsonl", "equipment.zh.qa.jsonl"):
        p = DATA / name
        if not p.exists():
            continue
        rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
        seen = set()
        for o in rows:
            key = o.get("text")
            seen.add(key)
            if key in fixes and o.get("translation") != fixes[key]:
                o["translation"] = fixes[key]
                o["qa_status"] = "ok"
                n += 1
        # 新词条：修订表里标了 add，且 jsonl 里原本没有
        if name.endswith(".qa.jsonl"):
            pass
        for key, new in fixes.items():
            if key in seen:
                continue
            m = meta.get(key, {})
            if not m.get("add"):
                continue
            row = {
                "kind": "equipment",
                "text": key,
                "source": m.get("source", "Aircraft.csv"),
                "column": m.get("column", "Name"),
                "context": "%s / 1941 Campaign / %s" % (m.get("source", "Aircraft.csv"), m.get("column", "Name")),
                "translation": new,
                "qa_status": "ok",
            }
            if name.endswith(".qa.jsonl"):
                row["issues"] = []
            rows.append(row)
            add += 1
        p.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n",
                     encoding="utf-8", newline="\n")
    return n, add


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
        if base_name not in CSV_NAMES:
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
            new = fixes.get(s[ni])
            if new and z[ni] != new:
                z[ni] = new
                n += 1
        with zh.open("w", encoding=enc, newline="") as f:
            csv.writer(f).writerows(zrows)
    return n


def main():
    fixes, meta = load_fixes()
    a, add = apply_jsonl(fixes, meta)
    b = apply_csv(fixes)
    print(f"jsonl cells: {a}; jsonl added: {add}; csv cells: {b}; fixes: {len(fixes)}")


if __name__ == "__main__":
    main()
