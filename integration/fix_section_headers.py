
# -*- coding: utf-8 -*-
"""修复带星号装饰的分组标题行（OBs / Locations / Ground / Aircraft ...）。

规则：
  1) 原文（游戏 Dat\CSV 的源单元格）以 *** 开头时，译文必须保留「开头 3 个以上星号」；
     原文**结尾**也有星号时，译文结尾也必须保留 3 个以上星号（数量不必与原文完全相等，
     引擎只是把它当文本显示，星号是视觉分隔）。
  2) 译文里混进去的重复片段、尾随注记（【注】等）一并清掉。
  3) 同步 data/scenario_csv/translations/*.jsonl 里对应行，避免下次 apply 又写回旧值。

只改文本列，其余列、行数、BOM、编码原样保留。
用法： python integration/fix_section_headers.py [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "mod"))
from build_maps import find_game  # noqa: E402

CSVDIR = PROJECT / "build" / "scenario_csv_zh"
DATA = PROJECT / "data" / "scenario_csv" / "translations"
AUDIT = PROJECT / "audit" / "section-header-fix.txt"

STAR_LEAD = re.compile(r"^\*+")
STAR_TAIL = re.compile(r"\*+$")
ANNOT = re.compile(r"^[【\[（(][^】\]）)]{0,14}[】\]）)]$")


def stars(text: str):
    s = text.strip()
    lead = len(STAR_LEAD.match(s).group(0)) if STAR_LEAD.match(s) else 0
    trail = len(STAR_TAIL.search(s).group(0)) if STAR_TAIL.search(s) else 0
    return lead, trail


def clean_body(value: str) -> str:
    s = value.strip()
    s = STAR_LEAD.sub("", s)
    tail = STAR_TAIL.search(s)
    if tail:
        s = s[: tail.start()]
    else:
        runs = list(re.finditer(r"\*{3,}", s))
        if runs:
            s = s[: runs[-1].start()]
    s = re.sub(r"\*+", " ", s)
    toks = s.split()
    while toks and ANNOT.fullmatch(toks[-1]):
        toks.pop()
    out = []
    for t in toks:
        if out and out[-1] == t:
            continue
        out.append(t)
    return "".join(out)


def rebuild(value: str, src: str) -> str:
    lead, trail = stars(src)
    body = clean_body(value)
    if not body:
        return value
    new = "*" * lead + " " + body
    if trail:
        new += " " + "*" * trail
    return new


def needs_fix(value: str, src: str) -> bool:
    lead, trail = stars(src)
    v_lead, v_trail = stars(value)
    if v_lead < 3:
        return True
    if trail and v_trail < 3:
        return True
    return False


def load_csv(path: Path):
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return list(csv.reader(raw.decode(enc).splitlines(keepends=True))), enc
        except UnicodeDecodeError:
            continue
    raise RuntimeError(path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    game = find_game()

    stats = Counter()
    samples = []
    pairs = []          # (csv_name, src_text, new_text)
    for zh in sorted(CSVDIR.glob("*/*.zh.csv")):
        csv_name = zh.name[:-7] + ".csv"
        src = game / "Dat" / "CSV" / zh.parent.name / csv_name
        if not src.exists():
            alt = PROJECT / "csv_swap_backup" / zh.parent.name / csv_name
            if alt.exists():
                src = alt
            else:
                continue
        srows, _ = load_csv(src)
        zrows, enc = load_csv(zh)
        if not srows or len(srows) != len(zrows):
            continue
        head = srows[0]
        if head != zrows[0]:
            continue
        dirty = False
        for s, z in zip(srows[1:], zrows[1:]):
            for i, (a, b) in enumerate(zip(s, z)):
                if len(a.strip()) < 3 or stars(a)[0] < 3:
                    continue
                if needs_fix(b, a):
                    new = rebuild(b, a)
                    if new != b:
                        stats["cell"] += 1
                        if len(samples) < 40:
                            samples.append((csv_name, b, new))
                        z[i] = new
                        pairs.append((csv_name, a, new))
                        dirty = True
        if dirty and not args.dry_run:
            bom = zh.read_bytes().startswith(b"\xef\xbb\xbf")
            with zh.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(zrows)
            stats["file"] += 1

    # 同步 jsonl（含 .qa 副本）
    if pairs and not args.dry_run:
        fix = {(c, t): n for c, t, n in pairs}
        for p in sorted(DATA.glob("*.jsonl")):
            rows, dirty = [], False
            for line in p.read_text(encoding="utf-8-sig").splitlines():
                if not line.strip():
                    continue
                o = json.loads(line)
                key = (o.get("source"), o.get("text"))
                if key in fix and o.get("translation") != fix[key]:
                    o["translation"] = fix[key]
                    dirty = True
                    stats["jsonl"] += 1
                rows.append(o)
            if dirty:
                with p.open("w", encoding="utf-8", newline="\n") as f:
                    for o in rows:
                        f.write(json.dumps(o, ensure_ascii=False) + "\n")

    lines = [f"stats: {dict(stats)}", f"pairs: {len(pairs)}", ""]
    for c, old, new in samples:
        lines.append(f"[{c}] {old!r} -> {new!r}")
    if not args.dry_run:
        AUDIT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
