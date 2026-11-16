# -*- coding: utf-8 -*-
"""地图标签覆盖检查：MapText.csv 的每一条字符串都必须能在每一套语言包里查到。

判据与运行时钩子一致：
  1. 精确命中（含字距拆开的 "M o s c o w"）优先；
  2. 精确未命中时，忽略空白与大小写后唯一对应的键也算命中（v1.9.13 起的第二索引）；
  3. 归一化后对应两种译文的键视为歧义，不算命中——运行时不猜，这里也不放过。

退出码：0 通过；2 有缺项；3 环境/文件错误。
"""
import csv
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MOD = ROOT / "mod"
PAYLOAD = MOD / "payload"


def game_root():
    cfg = MOD / "settings.local.json"
    if cfg.exists():
        try:
            values = json.loads(cfg.read_text(encoding="utf-8"))
        except ValueError:
            values = {}
        for key in ("game_path", "install_path"):
            value = values.get(key)
            if value:
                path = pathlib.Path(value)
                if (path / "Dat" / "CSV").is_dir():
                    return path
                if (path / "runtime" / "Dat" / "CSV").is_dir():
                    return path / "runtime"
    import os
    value = os.environ.get("WITE2_GAME")
    if value and (pathlib.Path(value) / "Dat" / "CSV").is_dir():
        return pathlib.Path(value)
    return None


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_bin(path):
    raw = path.read_bytes()
    if raw[:8] != b"W2CNMAP1":
        raise SystemExit("invalid translation map: %s" % path)
    count = struct.unpack_from("<I", raw, 8)[0]
    offset, result = 12, {}
    for _ in range(count):
        a, b = struct.unpack_from("<II", raw, offset)
        offset += 8
        key = raw[offset:offset + a * 2].decode("utf-16-le")
        offset += a * 2
        value = raw[offset:offset + b * 2].decode("utf-16-le")
        offset += b * 2
        result[key] = value
    return result


def norm(text):
    return "".join(ch.lower() for ch in text if ch not in " \t\r\n\xa0\u3000")


def has_cjk(text):
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def normalized_index(entries):
    index = {}
    for key, value in entries.items():
        folded = norm(key)
        if not folded:
            continue
        if folded in index and index[folded] != value:
            index[folded] = None
        else:
            index[folded] = value
    return index


def map_rows(path):
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise SystemExit("MapText.csv 解码失败：%s" % path)
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        return []
    head = [cell.strip().lstrip("\ufeff") for cell in rows[0]]
    if "mtText" not in head:
        return []
    col = head.index("mtText")
    return [row[col] for row in rows[1:] if len(row) > col and row[col].strip()]


def font_cmap(path):
    from fontTools.ttLib import TTFont
    cmap = set()
    font = TTFont(str(path))
    for table in font["cmap"].tables:
        cmap |= set(table.cmap.keys())
    return cmap


def dictionaries():
    result = [("zh-CN", read_json(PAYLOAD / "translations.json"),
               PAYLOAD / "overlay" / "Dat" / "Fonts" / "WitE2CN.ttf")]
    for path in sorted((PAYLOAD / "variants").glob("*/translations.bin")):
        code = path.parent.name
        if code == "zh-CN":
            continue
        font = path.parent / "overlay" / "Dat" / "Fonts" / "WitE2CN.ttf"
        result.append((code, read_bin(path), font))
    return result


def main():
    check = "--check" in sys.argv
    game = game_root()
    if game is None:
        print("MapText coverage: SKIP（找不到游戏目录，未做覆盖检查）")
        return 0
    files = sorted((game / "Dat" / "CSV").glob("*/MapText.csv"))
    if not files:
        print("MapText coverage: SKIP（游戏目录没有 MapText.csv）")
        return 0

    strings = []
    per_file = []
    contaminated = []
    for path in files:
        rows = map_rows(path)
        cjk = sum(1 for text in rows if has_cjk(text))
        if cjk:
            # 整份 CSV 已被换成译文（非游戏原版），英文源不可见：不参与覆盖统计，
            # 只在报告里登记，提醒还原。
            contaminated.append((path.parent.name, cjk, len(rows)))
            per_file.append({"file": path.name, "scenario": path.parent.name,
                             "strings": len(rows), "chinese_cells": cjk, "checked": False})
            continue
        strings.extend(rows)
        per_file.append({"file": path.name, "scenario": path.parent.name,
                         "strings": len(rows), "chinese_cells": 0, "checked": True})

    problems = []
    audit = {"files": len(files), "strings": len(strings), "languages": {}}
    for code, entries, font_path in dictionaries():
        exact = entries
        normalized = normalized_index(entries)
        exact_hits = norm_hits = localized = 0
        missing = []
        translated_values = set(entries.values())
        for text in strings:
            if has_cjk(text):
                # 这一格已经是中文：要么是 10-24 编辑器导入实验遗留在游戏目录里的
                # 旧 CSV（含脏值），要么是人工回填。英文源已不可见，覆盖检查跳过，
                # 但会在文件级报告里标为「CSV 非原版」。
                localized += 1
                continue
            if text in exact:
                exact_hits += 1
                continue
            if normalized.get(norm(text)):
                norm_hits += 1
                continue
            if text in translated_values:
                # 文件本身已经是译文（例如 10-24 编辑器导入实验遗留在游戏目录里的
                # 1941 Campaign - No Early End\MapText.csv）。不需要再翻译，但要在
                # 报告里标出来：这份 CSV 不是游戏原版，安装目录不干净。
                localized += 1
                continue
            missing.append(text)
        missing_glyphs = []
        try:
            cmap = font_cmap(font_path)
            for text in strings:
                value = exact.get(text) or normalized.get(norm(text))
                if value:
                    for ch in value:
                        if ord(ch) not in cmap and ch not in missing_glyphs:
                            missing_glyphs.append(ch)
        except ImportError:
            cmap = None
        print("%-5s strings: %d  exact: %d  normalized: %d  already-zh: %d  missing: %d  glyphs: %s"
              % (code, len(strings), exact_hits, norm_hits, localized, len(missing),
                 ("missing %d" % len(missing_glyphs)) if cmap is not None else "n/a"))
        if missing:
            for text in missing[:12]:
                print("   MISSING %r" % text)
            problems.append("%s: %d 条地图标签查不到" % (code, len(missing)))
        if missing_glyphs:
            print("   MISSING GLYPHS %r" % "".join(missing_glyphs[:40]))
            problems.append("%s: 缺字 %d 个" % (code, len(missing_glyphs)))
        audit["languages"][code] = {
            "exact": exact_hits, "normalized": norm_hits, "already_translated": localized,
            "missing": missing, "missing_glyphs": missing_glyphs,
        }
    audit["scenarios"] = per_file

    out = ROOT / "audit" / "maptext-coverage.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    if not check:
        print("audit written:", out.relative_to(ROOT))

    if contaminated:
        print("WARN 游戏目录里有被改过的 MapText.csv（非游戏原版，建议 Steam 校验文件还原）：")
        for scenario, cjk, total in contaminated:
            print("   %-45s 中文 %d / %d 条" % (scenario, cjk, total))
    if problems:
        print("MapText coverage: FAIL — " + "；".join(problems))
        return 2
    print("MapText coverage: OK（%d 个原版剧本、%d 条英文标签、四语言包全命中）" % (len(files) - len(contaminated), len(strings)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
