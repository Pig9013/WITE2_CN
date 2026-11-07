# -*- coding: utf-8 -*-
r"""修正 AirGroups / AirGroupRenames 场景表里的「Staffel 误作大队」。

背景（2026-11-07，v1.9.10）：Luftwaffe 番号 N./JG 51 是 Staffel（中队），
I./JG 51 是 Gruppe（大队）。语料层 data/scenario_csv/translations/airgroup.zh.jsonl
区分正确（第1中队 / 第I大队），但场景表 build/scenario_csv_zh/*/AirGroups.zh.csv 与
AirGroupRenames.zh.csv 把阿拉伯数字 Staffel 也写成「第N大队」，于是 1./JG 51 与
I./JG 51 在中文化后撞名。旧生成器已失传（integration/apply_scenario_translations.py
依赖已不存在的 name_rules 模块），因此只能就地对场景表做规则化订正：

    源单元格 ^(\d+)\./... 且译单元格以「第<同一数字>大队」结尾  ->  末尾「大队」改「中队」

只改译单元格，不动英文列；写回时保留原文件的 BOM 与 CRLF（本仓库 zh CSV 是
「UTF-8 BOM + 正文 'ï»¿'」的双 BOM 形态）。未命中的行必须字节级 round-trip 一致。

用法：
    python integration/fix_airgroup_staffel.py --check   # 只报告，仍有待改则 exit 2
    python integration/fix_airgroup_staffel.py           # 写入
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
CSV_DIR = PROJECT / "build" / "scenario_csv_zh"
BOM = b"\xef\xbb\xbf"
RE_STAFFEL = re.compile(r"^(\d+)\./")
RE_ZH_GROUP = re.compile(r"第(\d+)大队$")


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

    pending, changed_files, skipped = 0, [], []
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
        baseline = dump([row[:] for row in zrows], prefix, lineterm)
        if baseline != zh.read_bytes():
            raise SystemExit("序列化不能字节还原，拒写：%s" % zh)
        n = 0
        for s, z in zip(srows, zrows):
            for i, cell in enumerate(s):
                m = RE_STAFFEL.match(cell.strip())
                if not m or i >= len(z):
                    continue
                zh_cell = z[i]
                mm = RE_ZH_GROUP.search(zh_cell.strip())
                if not mm or mm.group(1) != m.group(1):
                    continue
                z[i] = zh_cell.replace("大队", "中队")
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
        print("  %-60s %d" % (zh.relative_to(PROJECT), n))
    if skipped:
        print("  跳过 %d 个文件（源表缺失或形状不符）" % len(skipped))
    verb = "待改" if args.check else "已改"
    print("Staffel->中队: %s %d 格 / %d 文件" % (verb, pending, len(changed_files)))
    if args.check:
        return 2 if pending else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
