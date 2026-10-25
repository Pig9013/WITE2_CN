#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic Chinese names for air operational groups (AOGs.csv)."""
from __future__ import annotations

import csv
import json
import os
import re

ROOT = r"D:\Tool\Steam\steamapps\common\Gary Grigsby's War in the East 2\Dat\CSV"
OUT = r"D:\Tool\WITE2_CN\data\scenario_csv\translations\aog.zh.jsonl"

SUFFIX = {
    "BAK": "轰炸航空军", "DBAD": "远程轰炸航空师", "GBAK": "近卫轰炸航空军",
    "GIAK": "近卫歼击航空军", "GSAK": "近卫混成航空军", "GShAK": "近卫强击航空军",
    "IAK": "歼击航空军", "SAD": "混成航空师", "SAK": "混成航空军",
    "ShAK": "强击航空军", "IAD": "歼击航空师", "NIAD": "夜间歼击航空师",
    "BAD": "轰炸航空师", "ShAD": "强击航空师",
    "AIR ARMY": "航空集团军", "AIR CORPS": "航空军",
    "FIGHTER REGIMENT": "歼击航空团", "BOMB GROUP": "轰炸机群",
    "AIR FORCE BRIGADE": "空军旅", "RECON GROUP": "侦察群",
    "TRANSPORT GROUP": "运输群",
}
COUNTRIES = {
    "GERMANY": "德国", "FINLAND": "芬兰", "HUNGARY": "匈牙利",
    "ITALY": "意大利", "RUMANIA": "罗马尼亚", "ROMANIA": "罗马尼亚",
    "SLOVAKIA": "斯洛伐克", "SOVIET UNION": "苏联", "NEUTRAL": "中立",
}


def tr_suffix(s: str) -> str | None:
    s = s.strip()
    s = re.sub(r"\s+Air Corps$", "", s, flags=re.I)
    s = re.sub(r"\s+PVO$", "", s, flags=re.I)
    key = s.upper()
    if key in SUFFIX:
        return SUFFIX[key]
    return None


def translate(s: str) -> str | None:
    s = s.strip()
    m = re.fullmatch(r"\*+\s*(.+?)\s*\*+", s)
    if m and m.group(1).upper() in COUNTRIES:
        return "**** " + COUNTRIES[m.group(1).upper()] + " ****"
    m = re.fullmatch(r"NAGr\.?\s*(\d+)", s, re.I)
    if m:
        return f"第{m.group(1)}侦察大队"
    m = re.fullmatch(r"(\d+)\.\s*Flieger-Division", s, re.I)
    if m:
        return f"第{m.group(1)}航空师"
    m = re.fullmatch(r"(\d+)(?:st|nd|rd|th)?\s+(.+)", s, re.I)
    if m:
        num, rest = m.group(1), m.group(2).strip()
        rest = re.sub(r"^Hun\.\s*", "匈牙利", rest, flags=re.I)
        rest = re.sub(r"^Rum\.\s*", "罗马尼亚", rest, flags=re.I)
        rest = re.sub(r"^Ital\.\s*", "意大利", rest, flags=re.I)
        rest = re.sub(r"^Sov\.\s*", "苏联", rest, flags=re.I)
        suffix = tr_suffix(rest)
        if suffix:
            return f"第{num}{suffix}"
        return None
    return None


def main():
    vals = set()
    for d in os.listdir(ROOT):
        p = os.path.join(ROOT, d, "AOGs.csv")
        if os.path.exists(p):
            with open(p, encoding="utf-8-sig", errors="replace", newline="") as f:
                for r in csv.DictReader(f):
                    v = (r.get("Name") or "").strip()
                    if v:
                        vals.add(v)
    out = []
    misses = []
    for v in sorted(vals):
        t = translate(v)
        if t:
            out.append({"kind": "aog", "text": v, "translation": t, "qa_status": "ok"})
        else:
            misses.append(v)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print({"total": len(vals), "translated": len(out), "misses": len(misses), "out": OUT})
    print("MISSES", misses[:40])


if __name__ == "__main__":
    main()
