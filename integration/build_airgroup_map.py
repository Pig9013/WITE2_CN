#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic, conservative names for AirGroups.csv (and renames)."""
from __future__ import annotations

import csv
import json
import os
import re

ROOT = r"D:\Tool\Steam\steamapps\common\Gary Grigsby's War in the East 2\Dat\CSV"
OUT = r"D:\Tool\WITE2_CN\data\scenario_csv\translations\airgroup.zh.jsonl"

UNIT = {
    "jg": "战斗机联队", "kg": "轰炸机联队", "stg": "俯冲轰炸机联队",
    "njg": "夜间战斗机联队", "zg": "重型战斗机联队", "sg": "对地攻击联队",
    "tg": "运输机联队", "nagr": "侦察大队", "fagr": "远程侦察大队",
    "aufklargr": "侦察大队", "lg": "教导联队",
    "iap": "歼击航空团", "shap": "强击航空团", "bap": "轰炸航空团",
    "nbap": "夜间轰炸航空团", "gbap": "近卫轰炸航空团",
}


def tr(s: str):
    x = s.strip()
    m = re.fullmatch(r"Stab\s*/\s*([A-Za-z]+)\s*(\d+)", x, re.I)
    if m:
        u = UNIT.get(m.group(1).lower())
        return f"第{m.group(2)}{u}指挥部" if u else None
    m = re.fullmatch(r"([IVX]+)\.\s*/\s*([A-Za-z]+)\s*(\d+)", x, re.I)
    if m:
        u = UNIT.get(m.group(2).lower())
        return f"第{m.group(3)}{u}第{m.group(1)}大队" if u else None
    m = re.fullmatch(r"(\d+)\.\s*/\s*([A-Za-z]+)\s*(\d+)", x, re.I)
    if m:
        u = UNIT.get(m.group(2).lower())
        return f"第{m.group(3)}{u}第{m.group(1)}中队" if u else None
    m = re.fullmatch(r"(\d+)\.\s*\(\s*H\s*\)\s*/\s*([A-Za-z]+)\s*(\d+)", x, re.I)
    if m:
        u = UNIT.get(m.group(2).lower())
        return f"第{m.group(3)}{u}第{m.group(1)}（陆军）中队" if u else None
    m = re.fullmatch(r"(\d+)\.\s*\(\s*H\s*\)\s*/\s*AufklarGr\s*(\d+)", x, re.I)
    if m:
        return f"第{m.group(2)}侦察大队第{m.group(1)}（陆军）中队"
    m = re.fullmatch(r"(?:Stab\s*/\s*)?NAGr\.?\s*(\d+)", x, re.I)
    if m:
        return f"第{m.group(1)}侦察大队"
    m = re.fullmatch(r"(\d+)\s+(IAP|ShAP|BAP|NBAP|GBAP)(?:-.*)?", x, re.I)
    if m:
        u = UNIT.get(m.group(2).lower())
        return f"第{m.group(1)}{u}" if u else None
    return None


def main():
    vals = set()
    for d in os.listdir(ROOT):
        p = os.path.join(ROOT, d, "AirGroups.csv")
        if os.path.exists(p):
            with open(p, encoding="utf-8-sig", errors="replace", newline="") as f:
                for r in csv.DictReader(f):
                    v = (r.get("Name") or "").strip()
                    if v:
                        vals.add(v)
    out = []
    misses = []
    for v in sorted(vals):
        t = tr(v)
        if t:
            out.append({"kind": "airgroup", "text": v, "translation": t, "qa_status": "ok"})
        else:
            misses.append(v)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print({"total": len(vals), "translated": len(out), "misses": len(misses), "out": OUT})
    print("MISSES", misses[:30])


if __name__ == "__main__":
    main()
