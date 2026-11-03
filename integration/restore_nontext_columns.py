
# -*- coding: utf-8 -*-
"""把场景 CSV 中“非文本列”（事件脚本参数、ID、数值等）恢复为源文件原值。

审计口径：只有 SPEC 允许的文本列可以不同；其余列必须与源文件逐字节一致。
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
CSVDIR = PROJECT / "build" / "scenario_csv_zh"
SPEC = {
    "GameEvents.csv": ("title", "text"),
    "MapText.csv": ("mtText",),
    "Locations.csv": ("Name",),
    "Leaders.csv": ("Name", "FirstName"),
    "Units.csv": ("Name",),
    "OBs.csv": ("Name", "Suffix"),
    "AOGs.csv": ("Name",),
    "AirGroups.csv": ("Name",),
    "UnitRenames.csv": ("newName", "origName"),
    "AirGroupRenames.csv": ("newName", "origName"),
    "Ground.csv": ("Name",),
    "Devices.csv": ("Name",),
    "Aircraft.csv": ("Name",),
    "Nations.csv": ("Name",),
    "GroundTypes.csv": ("Name",),
}


def game_path() -> Path:
    p = PROJECT / "mod" / "settings.local.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    return Path(data["game_path"])


def load(path: Path):
    raw = path.read_bytes()
    bom = raw[:3] == bytes([239, 187, 191])
    enc = "utf-8-sig" if bom else "utf-8"
    try:
        text = raw.decode(enc)
    except UnicodeDecodeError:
        enc = "cp1252"
        text = raw.decode(enc)
    return list(csv.reader(text.splitlines(keepends=True))), bom, enc


def main() -> None:
    base = game_path() / "Dat" / "CSV"
    changed = 0
    files = 0
    for zh in sorted(CSVDIR.rglob("*.zh.csv")):
        name = zh.name[:-7] + ".csv"
        if name not in SPEC:
            continue
        src = base / zh.parent.name / name
        if not src.exists():
            continue
        srows, _, _ = load(src)
        zrows, bom, enc = load(zh)
        if len(srows) != len(zrows) or not srows:
            print("skip row mismatch", zh)
            continue
        allowed = {srows[0].index(c) for c in SPEC[name] if c in srows[0]}
        dirty = False
        # 表头整行恢复
        if zrows[0] != srows[0]:
            zrows[0] = list(srows[0])
            dirty = True
            changed += len(srows[0])
        for s, z in zip(srows[1:], zrows[1:]):
            for j in range(min(len(s), len(z))):
                if j in allowed:
                    continue
                if z[j] != s[j]:
                    z[j] = s[j]
                    dirty = True
                    changed += 1
        if dirty:
            with zh.open("w", encoding=enc, newline="") as f:
                csv.writer(f).writerows(zrows)
            files += 1
    print(f"restored cells: {changed}; files: {files}")


if __name__ == "__main__":
    main()
