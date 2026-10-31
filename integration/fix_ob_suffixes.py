# -*- coding: utf-8 -*-
"""按术语库修订编制表（OBs）译文。

两处一起改，保持一致：
  1) build/scenario_csv_zh/<剧本>/OBs.zh.csv —— Name 列（年份码+标记）与 Suffix 列（编制名）
  2) data/scenario_csv/translations/unit.zh.jsonl —— source 为 OBs.csv 的行

只改这两列，其余列、行数、BOM 原样保留。
用法： python integration/fix_ob_suffixes.py [--dry-run]
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

OB_DIR = PROJECT / "build" / "scenario_csv_zh"
UNIT_JSONL = PROJECT / "data" / "scenario_csv" / "translations" / "unit.zh.jsonl"

NAME_TAIL = {
    "": "", "SS": "党卫军", "SS Volunteer": "党卫军志愿", "SS Type 1": "党卫军1型",
    "SS Type 2": "党卫军2型", "SS Type 3": "党卫军3型",
    "GD": "大德意志", "LAH SS": "阿道夫·希特勒警卫旗队", "HG": "赫尔曼·戈林",
    "Nord SS": "北方党卫军", "Wiking SS": "维京党卫军", "Das Reich SS": "帝国党卫军",
    "Totenkopf SS": "骷髅党卫军", "1st RFSS": "党卫队全国领袖第1", "2nd RFSS": "党卫队全国领袖第2",
    "Afrika": "非洲", "Reduced": "缩编", "Reduced Shtat": "缩编编制",
    "Beute": "缴获装备", "LL": "租借", "American LL": "美援租借", "Mixed": "混编",
    "Railroad": "铁道", "Lehr": "教导", "Norway": "挪威", "West": "西线", "Far East": "远东",
    "Brandenburg": "勃兰登堡", "zbV": "特种任务", "Panzer": "装甲", "Panther": "豹式",
    "Pz-IV": "IV号坦克", "Marder": "貂鼠", "Mixed Marder": "混编貂鼠", "Jagdpanther": "猎豹",
    "Walkure II": "女武神II", "Type 2": "2型", "HQ": "司令部", "HQ Combined Arms": "合成兵种司令部",
    "Army Sturm Artillery": "集团军突击炮兵", "Ind. Mortar": "独立迫击炮",
    "PzJ-I": "坦克歼击I型", "PzJ-II": "坦克歼击II型",
    "K18": "K18", "38(t)": "38(t)", "M18": "M18", "150mm": "150毫米", "210mm": "210毫米",
}
WAVE = re.compile(r"^(\d+)(?:st|nd|rd|th)\s+Wave$")
TIER = re.compile(r"^Tier\s+(\w+)$")


def ob_name(name: str):
    """41 -> 1941年版；42a -> 1942年a版；41 Tier 1a -> 1941年版1a型；44 GD -> 1944年版大德意志。"""
    s = name.strip()
    if not s or D.is_fragment(s):
        return None
    m = re.match(r"^(\d{2})([a-z]?)\s*(.*)$", s)
    if not m:
        return None
    head = "19" + m.group(1) + ("年" + m.group(2) + "版" if m.group(2) else "年版")
    tail = m.group(3).strip()
    if tail == "":
        return head
    if tail in NAME_TAIL:
        return head + NAME_TAIL[tail]
    t = TIER.match(tail)
    if t:
        return head + t.group(1) + "型"
    w = WAVE.match(tail)
    if w:
        return head + "第" + w.group(1) + "批"
    return None


def load_csv(path: Path):
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return list(csv.reader(raw.decode(enc).splitlines(keepends=True))), enc
        except UnicodeDecodeError:
            continue
    raise RuntimeError(path)


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    game = find_game()

    # 原始 OBs.csv（各剧本内容相同，取 1941 Campaign）
    src_rows, _ = load_csv(game / "Dat" / "CSV" / "1941 Campaign" / "OBs.csv")
    sh = src_rows[0]
    id_i, nm_i, sf_i = sh.index("ID"), sh.index("Name"), sh.index("Suffix")
    ref = {r[id_i]: (r[nm_i], r[sf_i]) for r in src_rows[1:] if len(r) > sf_i}

    stats = Counter()
    samples = []
    new_pair = {}   # 原文 Name -> 新中文；原文 Suffix -> 新中文
    for scen_dir in sorted(p for p in OB_DIR.iterdir() if p.is_dir()):
        p = scen_dir / "OBs.zh.csv"
        if not p.exists():
            continue
        rows, _ = load_csv(p)
        h = rows[0]
        ni, si, ii = h.index("Name"), h.index("Suffix"), h.index("ID")
        for r in rows[1:]:
            if len(r) <= max(ni, si, ii):
                continue
            src = ref.get(r[ii])
            if not src:
                continue
            src_name, src_suf = src
            if src_name.strip():
                new = ob_name(src_name)
                if new:
                    new_pair[src_name] = new
                    if r[ni] != new:
                        stats["name"] += 1
                        if len(samples) < 20:
                            samples.append(("name", src_name, r[ni], new))
                        r[ni] = new
                elif D.is_fragment(src_name.strip()) and r[ni] != src_name:
                    # 纯数字名（41/43…）不能译，否则生成数字键污染表格数字列，恢复原文
                    r[ni] = src_name
                    stats["name-restored"] += 1
            if src_suf.strip():
                new = D.ob_phrase(src_suf)
                if new:
                    new_pair[src_suf] = new
                    if r[si] != new:
                        stats["suffix"] += 1
                        if len(samples) < 80:
                            samples.append(("suffix", src_suf, r[si], new))
                        r[si] = new
        if not args.dry_run:
            bom = p.read_bytes().startswith(b"\xef\xbb\xbf")
            with p.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(rows)

    # 同步 unit.zh.jsonl 里 source=OBs.csv 的行
    if UNIT_JSONL.exists():
        out_rows = []
        for line in UNIT_JSONL.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("source") == "OBs.csv":
                txt = (row.get("text") or "").strip()
                if D.is_fragment(txt):
                    # 纯数字名：译文改回原文，避免生成数字键
                    if row.get("translation") != txt:
                        row["translation"] = txt
                        stats["jsonl-restored"] += 1
                else:
                    new = new_pair.get(row.get("text"))
                    if new and new != row.get("translation"):
                        stats["jsonl"] += 1
                        row["translation"] = new
            out_rows.append(row)
        if not args.dry_run:
            with UNIT_JSONL.open("w", encoding="utf-8", newline="\n") as f:
                for row in out_rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = io.StringIO()
    report.write(f"stats: {dict(stats)}\n")
    for kind, a, b, c in samples:
        report.write(f"[{kind}] {a} | {b} -> {c}\n")
    out = PROJECT / "audit" / ("ob-fix-dryrun.txt" if args.dry_run else "ob-fix.txt")
    out.write_text(report.getvalue(), encoding="utf-8")
    print(f"{'dry-run' if args.dry_run else 'applied'}: {dict(stats)} -> {out}")


if __name__ == "__main__":
    main()
