# -*- coding: utf-8 -*-
r"""Army Group F/G/H 译名修复：把丢字母的「集团军群」改回「F集团军群」。

缺陷
----
词典里 Army Group F / G / H 三个键的译文都是「集团军群」（字母被吃掉），
后果有二：
  * 三个集团军群在 UI 上同名，玩家无法区分；
  * Dat\Art\Sym\GE\ 下只能存在一张「集团军群.tga」→ 三个单位共用一张师徽，
    另外两张被 build_symbol_names.py 判为撞名跳过。

源头
----
  data/scenario_csv/translations/unit.zh.jsonl   3 行：集团军群G / 集团军群H / 集团军群F
  build/scenario_csv_zh/<剧本>/Units.zh.csv      33 行：集团军群（11 个剧本 × 3）
  payload/translations.json                      3 键
  payload/variants/<code>/translations.bin       4 个语言包 × 3 键

口径
----
与 glossary/unit_name_canon.csv 第 45-50 行既有的 A/B/C/E 制一致：字母在前。

用法
----
    python integration/fix_army_group_names.py            # 写入
    python integration/fix_army_group_names.py --check    # 只报不写，有残留返回 2
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "mod"
PAYLOAD = MOD / "payload"
JSONL = ROOT / "data" / "scenario_csv" / "translations" / "unit.zh.jsonl"
SCEN_ZH = ROOT / "build" / "scenario_csv_zh"

NAMES = {"Army Group F": "F", "Army Group G": "G", "Army Group H": "H"}
BROKEN = "集团军群"
TRAD = {
    "zh-CN": "集团军群",
    "zh-TW": "集團軍群",
    "zh-HK": "集團軍羣",
    "zh-MO": "集團軍羣",
}


def read_bin(path: Path) -> tuple[int, list[tuple[str, str]]]:
    data = path.read_bytes()
    if data[:8] != b"W2CNMAP1":
        raise SystemExit("语言包格式错误：%s" % path)
    count = struct.unpack("<I", data[8:12])[0]
    offset, items = 12, []
    for _ in range(count):
        a, b = struct.unpack("<II", data[offset:offset + 8])
        offset += 8
        key = data[offset:offset + a * 2].decode("utf-16le")
        offset += a * 2
        value = data[offset:offset + b * 2].decode("utf-16le")
        offset += b * 2
        items.append((key, value))
    if offset != len(data):
        raise SystemExit("语言包长度与条目数不符：%s" % path)
    return count, items


def write_bin(path: Path, items: list[tuple[str, str]]) -> None:
    out = bytearray(b"W2CNMAP1")
    out += struct.pack("<I", len(items))
    for key, value in items:
        out += struct.pack("<II", len(key), len(value))
        out += key.encode("utf-16le")
        out += value.encode("utf-16le")
    path.write_bytes(bytes(out))


def fix_jsonl(check: bool) -> list[str]:
    lines = JSONL.read_text(encoding="utf-8").splitlines(keepends=True)
    problems = []
    changed = 0
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        rec = json.loads(line)
        en = rec.get("text")
        if en not in NAMES:
            continue
        want = NAMES[en] + BROKEN
        if rec.get("translation") != want:
            problems.append("jsonl:%d %s = %r" % (i + 1, en, rec.get("translation")))
            if not check:
                rec["translation"] = want
                lines[i] = json.dumps(rec, ensure_ascii=False) + "\n"
                changed += 1
    if not check and changed:
        JSONL.write_text("".join(lines), encoding="utf-8")
    return problems


def game_root() -> Path:
    for name in ("settings.local.json", "settings.json"):
        path = MOD / name
        if not path.exists():
            continue
        value = json.loads(path.read_text(encoding="utf-8")).get("game_path")
        if value:
            return Path(value)
    raise SystemExit("找不到游戏目录：请在 mod/settings.local.json 里写 game_path")


def fix_csv(check: bool) -> list[str]:
    csv_root = game_root() / "Dat" / "CSV"
    problems = []
    total = 0
    for zh_path in sorted(SCEN_ZH.glob("*/Units.zh.csv")):
        game_path = csv_root / zh_path.parent.name / "Units.csv"
        if not game_path.exists():
            problems.append("缺失原表：%s" % game_path)
            continue
        zh = zh_path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        # 原版表不是 UTF-8（含 0xe1 等单字节），按 latin-1 逐字节解码即可比较 ASCII 名单
        en = game_path.read_text(encoding="latin-1").splitlines(keepends=True)
        changed = False
        for i in range(1, min(len(zh), len(en))):
            zrow = zh[i]
            erow = en[i]
            zi = zrow.find(",")
            zi2 = zrow.find(",", zi + 1)
            ei = erow.find(",")
            ei2 = erow.find(",", ei + 1)
            if min(zi, zi2, ei, ei2) < 0:
                continue
            cell = zrow[zi + 1:zi2]
            ename = erow[ei + 1:ei2]
            if ename not in NAMES:
                continue
            want = NAMES[ename] + BROKEN
            if cell != want:
                problems.append("%s:%d %s = %r" % (zh_path.parent.name, i + 1, ename, cell))
                if not check:
                    zh[i] = zrow[:zi + 1] + want + zrow[zi2:]
                    changed = True
                total += 1
        if changed:
            zh_path.write_text("".join(zh), encoding="utf-8-sig")
    return problems


def fix_json_dict(check: bool) -> list[str]:
    path = PAYLOAD / "translations.json"
    table = json.loads(path.read_text(encoding="utf-8"))
    problems, changed = [], False
    for en, letter in NAMES.items():
        want = letter + BROKEN
        if table.get(en) != want:
            problems.append("translations.json %s = %r" % (en, table.get(en)))
            if not check:
                table[en] = want
                changed = True
    if changed:
        path.write_text(json.dumps(table, ensure_ascii=False), encoding="utf-8")
    return problems


def fix_bins(check: bool) -> list[str]:
    problems = []
    for code, base in TRAD.items():
        path = PAYLOAD / "variants" / code / "translations.bin"
        count, items = read_bin(path)
        changed = False
        for idx, (key, value) in enumerate(items):
            if key not in NAMES:
                continue
            want = NAMES[key] + base
            if value != want:
                problems.append("%s %s = %r" % (code, key, value))
                if not check:
                    items[idx] = (key, want)
                    changed = True
        if changed:
            write_bin(path, items)
            count2, _ = read_bin(path)
            if count2 != count:
                raise SystemExit("写回条目数变化：%s" % path)
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    problems = []
    problems += fix_jsonl(args.check)
    problems += fix_csv(args.check)
    problems += fix_json_dict(args.check)
    problems += fix_bins(args.check)
    if args.check:
        if problems:
            print("Army Group F/G/H 仍有 %d 处残留：" % len(problems))
            for item in problems[:40]:
                print("  " + item)
            return 2
        print("Army Group F/G/H 名称：一致")
        return 0
    print("Army Group F/G/H 名称：已修正 %d 处" % len(problems))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
