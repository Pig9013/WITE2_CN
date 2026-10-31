# -*- coding: utf-8 -*-
"""按术语库修订剧本 CSV 里的部队番号（Units / AOGs / AirGroups 的 Name 列）。

这是最终生效的一层：build_maps.py 最后读取这些 CSV，它们会覆盖前面 jsonl 的译文。
只改 Name 列，其余列、行数、编码、BOM 一律原样保留。
用法： python integration/fix_scenario_names.py [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "glossary"))
import designations as D  # noqa: E402

ZH_DIR = PROJECT / "build" / "scenario_csv_zh"
TARGETS = ("Units.csv", "AOGs.csv", "AirGroups.csv", "UnitRenames.csv", "AirGroupRenames.csv")


def find_game() -> Path:
    env = os.environ.get("WITE2_GAME")
    if env:
        return Path(env)
    for name in ("settings.local.json", "settings.json"):
        p = PROJECT / "mod" / name
        if p.exists():
            try:
                gp = json.loads(p.read_text(encoding="utf-8")).get("game_path")
                if gp:
                    return Path(gp)
            except Exception:
                pass
    raise SystemExit("找不到游戏目录")


def load_rows(path: Path):
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return list(csv.reader(raw.decode(enc).splitlines(keepends=True))), raw.startswith(b"\xef\xbb\xbf")
        except UnicodeDecodeError:
            continue
    raise RuntimeError(path)


def translate(name: str, ob: str) -> str | None:
    return D.reference_fix(name) or D._sov_air(name) or D._german_hq(name) or D._rvgk(name, ob)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    game = find_game()
    base = game / "Dat" / "CSV"

    stats = Counter()
    samples = []
    for scen_dir in sorted(p for p in ZH_DIR.iterdir() if p.is_dir()):
        scen = scen_dir.name
        src_dir = base / scen
        if not src_dir.exists():
            print("no source scenario:", scen)
            continue
        # 该剧本的 OB 表：Type -> 编制名
        ob_map = {}
        obs_p = src_dir / "OBs.csv"
        if obs_p.exists():
            rows, _ = load_rows(obs_p)
            h = rows[0]
            id_i, nm_i, sf_i = h.index("ID"), h.index("Name"), h.index("Suffix")
            for r in rows[1:]:
                if len(r) > sf_i:
                    ob_map[r[id_i]] = (r[nm_i] + " " + r[sf_i]).strip()

        for fn in TARGETS:
            src_p = src_dir / fn
            zh_p = scen_dir / fn.replace(".csv", ".zh.csv")
            if not (src_p.exists() and zh_p.exists()):
                continue
            srows, _ = load_rows(src_p)
            zrows, bom = load_rows(zh_p)
            if len(srows) != len(zrows) or srows[0][:3] != zrows[0][:3]:
                print("STRUCTURE MISMATCH", scen, fn)
                continue
            h = srows[0]
            name_col = "Name" if "Name" in h else ("newName" if "newName" in h else None)
            if name_col is None:
                continue
            ni = h.index(name_col)
            ti = h.index("Type") if "Type" in h else None
            for s, z in zip(srows[1:], zrows[1:]):
                if len(s) <= ni or len(z) <= ni:
                    continue
                src = s[ni]
                if not src.strip():
                    continue
                if D.is_fragment(src.strip()):
                    # 纯序数/数字不能做词典键（引擎会连表格数字一起查表），恢复原文
                    if z[ni] != src:
                        z[ni] = src
                        stats["fragment-restored"] += 1
                    continue
                ob = ob_map.get(s[ti], "") if ti is not None and len(s) > ti else ""
                new = translate(src, ob)
                if new is None:
                    # 仅统一「第N近卫」-> 「近卫第N」
                    if z[ni].startswith("第") and "近卫" in z[ni]:
                        fixed = D.guards_first(z[ni])
                        if fixed != z[ni]:
                            z[ni] = fixed
                            stats["guards-order"] += 1
                    continue
                if new != z[ni]:
                    stats[fn] += 1
                    if len(samples) < 40:
                        samples.append((scen, fn, src, z[ni], new))
                    z[ni] = new
            if not args.dry_run:
                with zh_p.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                    csv.writer(f).writerows(zrows)

    report = io.StringIO()
    report.write(f"stats: {dict(stats)}\n")
    for s in samples:
        report.write(f"[{s[0]} / {s[1]}] {s[2]} | {s[3]} -> {s[4]}\n")
    out = PROJECT / "audit" / ("scenario-name-dryrun.txt" if args.dry_run else "scenario-name-fix.txt")
    out.write_text(report.getvalue(), encoding="utf-8")
    print(f"{'dry-run' if args.dry_run else 'applied'}: {dict(stats)} -> {out}")


if __name__ == "__main__":
    main()
