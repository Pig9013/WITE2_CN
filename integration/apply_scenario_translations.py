#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply translated scenario maps to every exported CSV and write *.zh.csv."""
from __future__ import annotations

import csv
import json
import os
import re
import sys

sys.path.insert(0, r"D:\Tool\WITE2_CN\pipeline")
from name_rules import translate_unit_name, translate_airgroup

ROOT = r"D:\Tool\Steam\steamapps\common\Gary Grigsby's War in the East 2\Dat\CSV"
TR = r"D:\Tool\WITE2_CN\data\scenario_csv\translations"
OUT = r"D:\Tool\WITE2_CN\build\scenario_csv_zh"

SPEC = {
    "GameEvents.csv": [("event", ["title", "text"])],
    "MapText.csv": [("place", ["mtText"])],
    "Locations.csv": [("place", ["Name"])],
    "Leaders.csv": [("leader", ["Name", "FirstName"])],
    "Units.csv": [("unit", ["Name"])],
    "OBs.csv": [("unit", ["Name", "Suffix"])],
    "AOGs.csv": [("aog", ["Name"])],
    "AirGroups.csv": [("airgroup", ["Name"])],
    "UnitRenames.csv": [("unit", ["newName", "origName"])],
    "AirGroupRenames.csv": [("airgroup", ["newName", "origName"])],
    "Ground.csv": [("equipment", ["Name"])],
    "Devices.csv": [("equipment", ["Name"])],
    "Aircraft.csv": [("equipment", ["Name"])],
    "Nations.csv": [("equipment", ["Name"])],
    "GroundTypes.csv": [("equipment", ["Name"])],
}


ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman_to_int(s: str):
    total = 0
    prev = 0
    for ch in reversed(s.upper()):
        v = ROMAN.get(ch)
        if not v:
            return None
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def normalize_unit(src: str, dst: str) -> str:
    s = src.strip()
    m = re.fullmatch(r"(\d+)(?:st|nd|rd|th)?", s, re.I)
    if m:
        return "第" + m.group(1)
    if re.fullmatch(r"[IVXLCDM]+", s):
        n = roman_to_int(s)
        if n:
            return "第" + str(n)
    rule = translate_unit_name(src)
    if rule:
        return rule
    return dst


def load_maps():
    maps = {}
    for kind in ("event", "place", "leader", "unit", "airgroup", "aog", "equipment"):
        p = os.path.join(TR, kind + ".zh.jsonl")
        m = {}
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("qa_status") == "blocked":
                    continue
                src = (r.get("text") or "").strip()
                dst = (r.get("translation") or "").strip()
                if kind == "event":
                    dst = dst.replace("\\n", "<cr>").replace("\\r", "")
                    dst = dst.replace("\r", "").replace("\n", "<cr>")
                else:
                    dst = dst.replace("\\n", " ").replace("\\r", " ")
                    dst = dst.replace("\r", " ").replace("\n", " ")
                dst = dst.replace("\\t", " ").strip()
                dst = re.sub(r"@@PH\\d+@@", "", dst)
                for marker in ("备注：", "备注:", "注：", "注:", "译注", "（注"):
                    if marker not in src:
                        dst = dst.split(marker)[0].strip()
                if kind == "unit":
                    dst = normalize_unit(src, dst)
                elif kind == "airgroup":
                    rule = translate_airgroup(src)
                    if rule:
                        dst = rule
                if src and dst and src != dst:
                    m[src] = dst
        maps[kind] = m
    return maps


def main():
    maps = load_maps()
    os.makedirs(OUT, exist_ok=True)
    report = {}
    for d in sorted(os.listdir(ROOT)):
        dp = os.path.join(ROOT, d)
        if not os.path.isdir(dp):
            continue
        od = os.path.join(OUT, d)
        for fn, specs in SPEC.items():
            srcp = os.path.join(dp, fn)
            if not os.path.exists(srcp):
                continue
            with open(srcp, "rb") as bf:
                raw_bytes = bf.read()
            has_bom = raw_bytes.startswith(b"\xef\xbb\xbf")
            if has_bom:
                try:
                    raw_bytes.decode("utf-8-sig")
                    in_enc = "utf-8-sig"
                except UnicodeDecodeError:
                    in_enc = "cp1252"
            else:
                try:
                    raw_bytes.decode("utf-8")
                    in_enc = "utf-8"
                except UnicodeDecodeError:
                    in_enc = "cp1252"
            with open(srcp, encoding=in_enc, newline="") as f:
                rows = list(csv.reader(f))
            if not rows:
                continue
            header = rows[0]
            idx = {name: i for i, name in enumerate(header)}
            changed = 0
            for row in rows[1:]:
                for kind, cols in specs:
                    for c in cols:
                        i = idx.get(c)
                        if i is None or i >= len(row):
                            continue
                        v = (row[i] or "").strip()
                        if v and v in maps[kind]:
                            row[i] = maps[kind][v]
                            changed += 1
            if changed:
                os.makedirs(od, exist_ok=True)
                outp = os.path.join(od, fn.replace(".csv", ".zh.csv"))
                out_enc = "utf-8-sig" if has_bom else "utf-8"
                with open(outp, "w", encoding=out_enc, newline="") as f:
                    w = csv.writer(f)
                    w.writerows(rows)
                report.setdefault(d, {})[fn] = changed
    with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as f:
        json.dump({"maps": {k: len(v) for k, v in maps.items()}, "files": report},
                  f, ensure_ascii=False, indent=2)
    print(json.dumps({"maps": {k: len(v) for k, v in maps.items()},
                      "scenarios": len(report), "out": OUT}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
