# -*- coding: utf-8 -*-
r"""修正场景表里被截断的苏军「大队/团」两级番号（第2/第15）。

背景（2026-11-18，v1.9.19）：AirGroups.csv 里有一批苏军两级番号写作
`2/15 IAP`（= 第15歼击航空团第2大队）。旧生成器把斜杠两侧直接拼成
`第2/第15`，兵种词整段丢失，游戏里显示为无意义的两段数字。语料层
data/scenario_csv/translations/airgroup.zh.jsonl 没有这些键，无法靠重建修好，
只能在场景表上按英文源单元格就地订正：

    源单元格 ^(\d+)/(\d+) <兵种> 且译单元格 ^第<同左>/第<同右>$  ->  glossary/air_designations.py 生成

只改译单元格，不动英文列；写回保留 BOM 与行尾。未命中的行必须字节级 round-trip 一致。

用法：
    python integration/fix_airgroup_slash.py --check   # 只报告，仍有待改则 exit 2
    python integration/fix_airgroup_slash.py           # 写入
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "glossary"))
import air_designations as A  # noqa: E402

CSV_DIR = PROJECT / "build" / "scenario_csv_zh"
BOM = b"\xef\xbb\xbf"
RE_SRC = re.compile(r"^(\d+)/(\d+)\s+[A-Z]")
RE_ZH = re.compile(r"^第(\d+)/第(\d+)$")


def settings_dir() -> Path:
    for name in ("settings.local.json", "settings.json"):
        p = PROJECT / "mod" / name
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        for key in ("game_path", "game_dir", "wite2_path", "install_path"):
            if data.get(key):
                q = Path(data[key])
                if (q / "Dat" / "CSV").exists():
                    return q / "Dat" / "CSV"
    raise SystemExit("找不到 Dat/CSV：请在 mod/settings.local.json 填 game_path")


def load(path: Path):
    raw = path.read_bytes()
    prefix = b""
    if raw.startswith(BOM):
        prefix = BOM
        raw = raw[len(BOM):]
    lineterm = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    return rows, prefix, lineterm


def dump(rows, prefix: bytes, lineterm: str) -> bytes:
    out = io.StringIO()
    csv.writer(out, lineterminator=lineterm).writerows(rows)
    text = out.getvalue()
    if text and not text.endswith(lineterm):
        text += lineterm
    return prefix + text.encode("utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    base = settings_dir()

    pending, changed_files, skipped, unresolved = 0, [], [], []
    for zh in sorted(CSV_DIR.glob("*/*.zh.csv")):
        if zh.name.split(".")[0] not in ("AirGroups", "AirGroupRenames"):
            continue
        src = base / zh.parent.name / (zh.name[:-7] + ".csv")
        if not src.exists():
            skipped.append(str(zh))
            continue
        srows, _, _ = load(src)
        zrows, prefix, lineterm = load(zh)
        if not srows or not zrows or len(srows[0]) != len(zrows[0]) or len(srows) != len(zrows):
            skipped.append(str(zh))
            continue
        if dump([row[:] for row in zrows], prefix, lineterm) != zh.read_bytes():
            raise SystemExit("序列化不能字节还原，拒写：%s" % zh)
        n = 0
        for s, z in zip(srows, zrows):
            for i, cell in enumerate(s):
                m = RE_SRC.match(cell.strip())
                if not m or i >= len(z):
                    continue
                mm = RE_ZH.match(z[i].strip())
                if not mm or mm.group(1) != m.group(1) or mm.group(2) != m.group(2):
                    continue
                new = A.translate_airgroup(cell.strip())
                if not new:
                    unresolved.append((zh.relative_to(PROJECT).as_posix(), cell.strip()))
                    continue
                z[i] = new
                n += 1
        if not n:
            continue
        pending += n
        changed_files.append((zh, n))
        if not args.check:
            raw0 = zh.read_bytes()
            new = dump(zrows, prefix, lineterm)
            if new.count(lineterm.encode()) != raw0.count(lineterm.encode()):
                raise SystemExit("行数变化，拒写：%s" % zh)
            zh.write_bytes(new)

    for zh, n in changed_files:
        print("  %-64s %d" % (zh.relative_to(PROJECT), n))
    if skipped:
        print("  跳过 %d 个文件（源表缺失或形状不符）" % len(skipped))
    for path, name in unresolved[:20]:
        print("  未解析 %s : %s" % (path, name))
    verb = "待改" if args.check else "已改"
    print("两级番号: %s %d 格 / %d 文件" % (verb, pending, len(changed_files)))
    if args.check:
        return 2 if pending or unresolved else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
