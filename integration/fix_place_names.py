# -*- coding: utf-8 -*-
"""地名同词多译的定点裁决（v1.9.10 批次六）。

audit/semantic-unresolved.csv 里 262 条 place 语义冲突，多数不是音译分歧而是
**LLM 把地名当普通词意译**：Bougie→灯芯绒、Guestrow→来宾行、Charmy Down→夏缅陷落、
Erbenschwang→继承权纷争、Drope→滴落、Kuusiku→四月、Metato→元太、Tors→榴弹炮……

权威优先级（本表取值依据，写在 glossary/place_name_canon.csv 的 source 列）：
  1. 中文维基百科**同名同地**条目（wiki）：122/262 条可查；
  2. 新华社译音表/通行音译规则（rule）；
  3. 语义误译、错地、拉丁残片的定点纠正（fix）；
  4. 各层已一致且无误（consensus）。

**不整表照搬维基**：维基标题多为现行官方名，与 1941 年语境冲突——Chuguev 作丘胡伊夫
（乌方名）而非丘古耶夫、Dnepropetrovsk 作第聂伯罗而非第聂伯罗彼得罗夫斯克、
Allenstein 作奥尔什丁而非阿伦施泰因、Tarnopol 作捷尔诺波尔而非塔尔诺波尔。
凡游戏用德文/俄文/匈文旧名的，一律按该语种译名，不做「现代化」。

写法：同一英文键在 jsonl 与场景 CSV 两层必须一致；CSV 按**英文源表同一行列**定位。
--check 只报不写，仍有残留返回 2。
"""
from __future__ import annotations

import argparse
import csv
import glob
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "glossary" / "place_name_canon.csv"


def load_canon():
    table = {}
    with open(CANON, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            en, zh = row["en"], row["zh"]
            if not en or not zh:
                raise SystemExit("place_name_canon.csv 有空行：%r" % row)
            if en in table and table[en] != zh:
                raise SystemExit("place_name_canon.csv 自相矛盾：%s" % en)
            table[en] = zh
    if len(table) < 200:
        raise SystemExit("place_name_canon.csv 条目过少（%d），疑似被截断" % len(table))
    return table


def _find_game() -> Path:
    candidates = []
    env = os.environ.get("WITE2_GAME")
    if env:
        candidates.append(Path(env))
    for name in ("settings.json", "settings.local.json"):
        p = ROOT / "mod" / name
        if p.exists():
            try:
                value = json.loads(p.read_text(encoding="utf-8")).get("game_path")
                if value:
                    candidates.append(Path(value))
            except Exception:
                pass
    for c in candidates:
        if (c / "WarInTheEast2.exe").exists():
            return c
    raise SystemExit("找不到游戏目录：设置 WITE2_GAME 或在 mod/settings.json 填 game_path")


def _load(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    bom = b""
    if raw.startswith(b"\xef\xbb\xbf"):
        bom, raw = raw[:3], raw[3:]
    newline = "\r\n" if b"\r\n" in raw[:4000] else "\n"
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline="")))
    return bom, newline, rows


def _dump(path, bom, newline, rows):
    buf = io.StringIO(newline="")
    csv.writer(buf, lineterminator=newline).writerows(rows)
    with open(path, "wb") as fh:
        fh.write(bom + buf.getvalue().encode("utf-8"))


def fix_jsonl(table, check):
    files = cells = 0
    # data/extracted/ 是 EXE/CSV 抽出的**原文证据**，不是译文层。
    targets = []
    for sub in ("data/scenario_csv/translations", "data/translations"):
        targets += sorted(glob.glob(str(ROOT / sub / "*.jsonl")))
    for path in targets:
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
        out, touched = [], 0
        for line in lines:
            s = line.strip()
            if not s:
                out.append(line)
                continue
            try:
                rec = json.loads(s)
            except ValueError:
                out.append(line)
                continue
            text = rec.get("text")
            if isinstance(text, str) and text in table and rec.get("translation") != table[text]:
                rec["translation"] = table[text]
                touched += 1
                out.append(json.dumps(rec, ensure_ascii=False) + ("\n" if line.endswith("\n") else ""))
            else:
                out.append(line)
        if touched:
            files += 1
            cells += touched
            if not check:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.writelines(out)
    return files, cells


# 只改「显示名列」。GameEvents.zh.csv 是宽参数表，同名英文格是事件脚本参数。
DISPLAY_FILES = {"Units.zh.csv", "Locations.zh.csv", "MapText.zh.csv"}
DISPLAY_COLUMNS = {"Name", "newName", "mtText"}


def fix_csv(game, table, check):
    files = cells = 0
    for zh_path in sorted((ROOT / "build" / "scenario_csv_zh").glob("*/*.zh.csv")):
        if zh_path.name not in DISPLAY_FILES:
            continue
        scenario = zh_path.parent.name
        name = zh_path.name.replace(".zh.csv", ".csv")
        source = game / "Dat" / "CSV" / scenario / name
        if not source.exists():
            source = ROOT / "csv_swap_backup" / scenario / name
        if not source.exists():
            continue
        try:
            src_rows = list(csv.reader(source.read_bytes().decode("utf-8-sig").splitlines(keepends=True)))
        except UnicodeDecodeError:
            src_rows = list(csv.reader(source.read_bytes().decode("cp1252").lstrip("\ufeff").splitlines(keepends=True)))
        bom, newline, rows = _load(zh_path)
        if len(src_rows) != len(rows):
            raise SystemExit("结构不一致：%s" % zh_path)
        header = rows[0]
        cols = [j for j, col in enumerate(header) if col in DISPLAY_COLUMNS]
        if not cols:
            raise SystemExit("找不到显示名列：%s" % zh_path)
        touched = 0
        for i, (src_row, row) in enumerate(zip(src_rows, rows)):
            if i == 0:
                continue
            if len(src_row) != len(row):
                raise SystemExit("列数不一致：%s 行 %d" % (zh_path, i + 1))
            for j in cols:
                if j >= len(src_row):
                    continue
                src = src_row[j]
                if src in table and row[j] != table[src] and row[j]:
                    row[j] = table[src]
                    touched += 1
        if touched:
            files += 1
            cells += touched
            if not check:
                _dump(zh_path, bom, newline, rows)
                back = _load(zh_path)
                if back[0] != bom or back[1] != newline or back[2] != rows:
                    raise SystemExit("写回后往返不一致，拒写：%s" % zh_path)
    return files, cells


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    table = load_canon()
    files, cells = fix_jsonl(table, args.check)
    cf, cc = fix_csv(_find_game(), table, args.check)
    print("place canon: %d keys" % len(table))
    print("jsonl: %d files / %d cells" % (files, cells))
    print("scenario csv: %d files / %d cells" % (cf, cc))
    if args.check and (cells or cc):
        print("PLACE-FIX: FAIL")
        return 2
    print("PLACE-FIX: %s" % ("CHECK OK" if args.check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
