
# -*- coding: utf-8 -*-
"""部队名同词多译的定点裁决（v1.9.10 批次七）。

audit/semantic-unresolved.csv 里 103 条 family=unit 的语义冲突，实际不是「两种译法」，
而是**层间漂移 + 同键多值**：

  * jsonl 写全名/带英文残渣/罗马数字算错：156th维琴察师、41st 爱沙尼亚步兵师、
    第三巴尔蒂克军、第四库奈斯师、第五十四海军部队、第二索弗雷扎团、空降师 I、
    第四帝国大厅、1/S. 柏林家乡、Luft舰队、Kuliev骑兵、Mishulin的骑兵；
  * 场景 CSV 是短名：第156维琴察、第41爱沙尼亚、第3波罗的海、第4库内奥、第54海军、
    第2斯福尔扎、第1空降、第4统帅堂。

口径（本表）：**沿用场景表已有的短名制**「第N+名称」，不补英文里没有的编制词
（师/军/旅/团），近卫写「近卫第N」。英文原文多为短名，UI 宽度有限，95% 场景
单元格已是此制。已知限制：苏军方面军标准写法是「白俄罗斯第1方面军」「波罗的海
沿岸第1方面军」，本批保留「第1白俄罗斯」「第1波罗的海」，语序另案处理。

三条假阳性不本批处理（同串不同实体）：
  Ferdinand（equipment 斐迪南坦克歼击车 vs leader 费迪南德）、
  Rifle Squad（equipment 步枪小队 vs GroundTypes 步兵班）、
  Neame（leader 人名，unit 层无值）。

写法：jsonl 与场景表两层同写；CSV 按**英文源表同一行列**定位，只碰显示列。
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
CANON = ROOT / "glossary" / "unit_name_canon.csv"


def load_canon():
    table = {}
    with open(CANON, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            en, zh = row["en"], row["zh"]
            if not en or not zh or zh == "-":
                raise SystemExit("unit_name_canon.csv 有空行：%r" % row)
            if en in table and table[en] != zh:
                raise SystemExit("unit_name_canon.csv 自相矛盾：%s" % en)
            table[en] = zh
    if len(table) < 80:
        raise SystemExit("unit_name_canon.csv 条目过少（%d），疑似被截断" % len(table))
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


# 只改三张部队表的显示列；GameEvents 等宽参数表的同名格是脚本参数，绝不能碰。
DISPLAY_FILES = {"Units.zh.csv", "UnitRenames.zh.csv", "OBs.zh.csv"}
# OBs.zh.csv 的番号在 Suffix 列（Name 列多半是空或指挥层名），只改 Name/newName 会漏掉一半——
# 2026-11-07 实测：Rum. Frontier Guard Division 的旧值就藏在 OBs 的 Suffix 里。
DISPLAY_COLUMNS = {"Name", "newName", "ShortName", "Suffix"}


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
    print("unit canon: %d keys" % len(table))
    print("jsonl: %d files / %d cells" % (files, cells))
    print("scenario csv: %d files / %d cells" % (cf, cc))
    if args.check and (cells or cc):
        print("UNIT-NAME-FIX: FAIL")
        return 2
    print("UNIT-NAME-FIX: %s" % ("CHECK OK" if args.check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
