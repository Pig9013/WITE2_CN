# -*- coding: utf-8 -*-
r"""单位名里的 ASCII 双引号修复：第185步兵师"闪电" → 第185步兵师“闪电”。

缺陷
----
部队名的译文会被引擎当成文件名拼进 Dat\Art\Sym\<国>\<名>.tga，
而 Windows 文件名不允许 ASCII 双引号 "：
  * 这类名字在任何以名字查表的美术资源上（含 Dat\Art\Sym）都会失效。
185th Folgore 曾是唯一一处（也是师徽覆盖审计里唯一的缺口）。

口径
----
mod 昵称惯例是全角引号：II 'Folgore' → 第二“闪电”师、P-38G/H Lightning → P-38G/H “闪电”。
本文件把 ASCII " 成对换成 “ ”，并把结果写回所有层。

源头
----
  data/scenario_csv/translations/unit.zh.jsonl      1 行
  data/scenario_csv/translations/unit.zh.qa.jsonl   1 行
  build/scenario_csv_zh/<剧本>/Units.zh.csv        11 行（每个剧本 1 格）
  payload/translations.json                         1 键
  payload/variants/<code>/translations.bin          4 个语言包 × 1 键

用法
----
    python integration/fix_unit_name_quotes.py            # 写入
    python integration/fix_unit_name_quotes.py --check    # 只报不写，有残留返回 2
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "mod"
PAYLOAD = MOD / "payload"
JSONL = ROOT / "data" / "scenario_csv" / "translations" / "unit.zh.jsonl"
JSONL_QA = ROOT / "data" / "scenario_csv" / "translations" / "unit.zh.qa.jsonl"
SCEN_ZH = ROOT / "build" / "scenario_csv_zh"

KEY = "185th Folgore"
BROKEN = {
    "zh-CN": '第185步兵师"闪电"',
    "zh-TW": '第185步兵師"閃電"',
    "zh-HK": '第185步兵師"閃電"',
    "zh-MO": '第185步兵師"閃電"',
}
FIXED = {
    "zh-CN": "第185步兵师“闪电”",
    "zh-TW": "第185步兵師“閃電”",
    "zh-HK": "第185步兵師“閃電”",
    "zh-MO": "第185步兵師“閃電”",
}


def smart_quotes(text: str) -> str:
    out, opening = [], True
    for ch in text:
        if ch == '"':
            out.append("“" if opening else "”")
            opening = not opening
        else:
            out.append(ch)
    return "".join(out)


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


def fix_jsonl(path: Path, check: bool) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    problems, changed = [], 0
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        rec = json.loads(line)
        value = rec.get("translation") or ""
        if '"' not in value:
            continue
        problems.append("%s:%d %r" % (path.name, i + 1, value))
        if not check:
            rec["translation"] = smart_quotes(value)
            lines[i] = json.dumps(rec, ensure_ascii=False) + "\n"
            changed += 1
    if not check and changed:
        path.write_text("".join(lines), encoding="utf-8")
    return problems


def fix_csv(check: bool) -> list[str]:
    problems = []
    old = '"' + BROKEN["zh-CN"].replace('"', '""') + '"'
    new = FIXED["zh-CN"]
    for path in sorted(SCEN_ZH.glob("*/Units.zh.csv")):
        text = path.read_text(encoding="utf-8-sig")
        hits = text.count(old)
        if not hits:
            continue
        problems.append("%s Units.zh.csv：%d 格" % (path.parent.name, hits))
        if not check:
            path.write_text(text.replace(old, new), encoding="utf-8-sig")
    return problems


def fix_json_dict(check: bool) -> list[str]:
    path = PAYLOAD / "translations.json"
    table = json.loads(path.read_text(encoding="utf-8"))
    value = table.get(KEY)
    if value not in BROKEN.values():
        return []
    if not check:
        table[KEY] = FIXED["zh-TW" if "閃" in value else "zh-CN"]
        path.write_text(json.dumps(table, ensure_ascii=False), encoding="utf-8")
    return ["translations.json %s = %r" % (KEY, value)]


def fix_bins(check: bool) -> list[str]:
    problems = []
    for code in ("zh-CN", "zh-TW", "zh-HK", "zh-MO"):
        path = PAYLOAD / "variants" / code / "translations.bin"
        count, items = read_bin(path)
        changed = False
        for idx, (key, value) in enumerate(items):
            if key != KEY or value not in BROKEN.values():
                continue
            problems.append("%s %s = %r" % (code, key, value))
            if not check:
                items[idx] = (key, FIXED[code])
                changed = True
        if changed:
            write_bin(path, items)
            count2, _ = read_bin(path)
            if count2 != count:
                raise SystemExit("写回条目数变化：%s" % path)
    return problems


def fix_glossary(check: bool) -> list[str]:
    """glossary 里的两处权威表（master_overrides 是 {key: value}，reference_overrides 是 {key: [value, note]}）。

    这两张表是全仓库的排版基准，改动必须**逐字节外科式**：只换那一处的引号，
    不重新 dump（重新 dump 会把 5,650 行的缩进全部改写）。
    """
    problems = []
    pairs = []
    for code, text in BROKEN.items():
        pairs.append((text.replace('"', '\\"'), FIXED[code]))
    for name in ("master_overrides.json", "reference_overrides.json"):
        path = ROOT / "glossary" / name
        body = path.read_text(encoding="utf-8")
        hits = 0
        for old, new in pairs:
            hits += body.count(old)
        if not hits:
            continue
        problems.append("glossary/%s：%d 处" % (name, hits))
        if not check:
            for old, new in pairs:
                body = body.replace(old, new)
            path.write_text(body, encoding="utf-8")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    problems = []
    problems += fix_jsonl(JSONL, args.check)
    problems += fix_jsonl(JSONL_QA, args.check)
    problems += fix_csv(args.check)
    problems += fix_json_dict(args.check)
    problems += fix_bins(args.check)
    problems += fix_glossary(args.check)
    if args.check:
        if problems:
            print("单位名仍有 %d 处 ASCII 双引号：" % len(problems))
            for item in problems[:40]:
                print("  " + item)
            return 2
        print("Unit-name quote guard: OK")
        return 0
    print("单位名 ASCII 引号：已修正 %d 处" % len(problems))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
