#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit translated scenario CSVs against the editor-exported originals."""
from __future__ import annotations

import csv
import json
import os
import sys

GAME = r"D:\Tool\Steam\steamapps\common\Gary Grigsby's War in the East 2\Dat\CSV"
ZH = r"D:\Tool\WITE2_CN\build\scenario_csv_zh"
SPEC = {
    "GameEvents.csv": {"title", "text"},
    "MapText.csv": {"mtText"},
    "Locations.csv": {"Name"},
    "Leaders.csv": {"Name", "FirstName"},
    "Units.csv": {"Name"},
    "OBs.csv": {"Name", "Suffix"},
    "AOGs.csv": {"Name"},
    "AirGroups.csv": {"Name"},
    "UnitRenames.csv": {"newName", "origName"},
    "AirGroupRenames.csv": {"newName", "origName"},
    "Ground.csv": {"Name"},
    "Devices.csv": {"Name"},
    "Aircraft.csv": {"Name"},
    "Nations.csv": {"Name"},
    "GroundTypes.csv": {"Name"},
}


def read_raw(path):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        raw.decode("utf-8-sig" if bom else "utf-8")
        enc = "utf-8"
    except UnicodeDecodeError:
        enc = "cp1252"
    with open(path, encoding=("utf-8-sig" if bom else "utf-8") if enc == "utf-8" else "cp1252",
              errors="strict", newline="") as f:
        rows = list(csv.reader(f))
    return raw, bom, enc, rows


def main():
    failures = []
    warnings = []
    files = 0
    rows_total = 0
    for scen in sorted(os.listdir(ZH)):
        sp = os.path.join(ZH, scen)
        if not os.path.isdir(sp):
            continue
        for outname in sorted(os.listdir(sp)):
            if not outname.endswith(".zh.csv"):
                continue
            base = outname[:-7] + ".csv"
            if base not in SPEC:
                continue
            op = os.path.join(GAME, scen, base)
            zp = os.path.join(sp, outname)
            if not os.path.exists(op):
                failures.append((scen, base, "original missing"))
                continue
            files += 1
            try:
                oraw, obom, oenc, orows = read_raw(op)
                zraw, zbom, zenc, zrows = read_raw(zp)
            except Exception as e:
                failures.append((scen, base, "parse error: " + repr(e)))
                continue
            if obom != zbom:
                failures.append((scen, base, f"BOM mismatch {obom}->{zbom}"))
            if oenc != zenc:
                warnings.append((scen, base, f"encoding normalized {oenc}->{zenc}"))
            if len(orows) != len(zrows):
                failures.append((scen, base, f"row count {len(orows)}->{len(zrows)}"))
                continue
            if orows[0] != zrows[0]:
                failures.append((scen, base, "header changed"))
            changed_cols = SPEC[base]
            for ri, (a, b) in enumerate(zip(orows[1:], zrows[1:])):
                rows_total += 1
                if len(a) != len(b):
                    failures.append((scen, base, f"row {ri} field count {len(a)}->{len(b)}"))
                    break
                for ci, (x, y) in enumerate(zip(a, b)):
                    col = orows[0][ci] if ci < len(orows[0]) else f"extra{ci}"
                    if col in changed_cols:
                        continue
                    if x != y:
                        failures.append((scen, base, f"row {ri} col {ci} ({col!r}) changed unexpectedly"))
                        break
                else:
                    continue
                break
            # U+FFFD / NUL in output
            ztext = zraw.decode("utf-8-sig" if zbom else "utf-8", errors="replace")
            if "\ufffd" in ztext:
                failures.append((scen, base, "replacement char U+FFFD in output"))
            if "\x00" in ztext:
                failures.append((scen, base, "NUL in output"))
    print(json.dumps({"files": files, "rows": rows_total, "failures": len(failures),
                      "warnings": len(warnings)}, ensure_ascii=False))
    for f in failures[:80]:
        print("FAIL", f)
    for w in warnings[:20]:
        print("WARN", w)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
