#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""扫描游戏美术目录，导出「资源路径标识符」清单，供构建期守卫使用。

背景
----
本 mod 的 hook 对「引擎传给本地化函数的整条字符串」做精确、大小写敏感的整串替换。
引擎里有一批字符串既是界面文字、又是美术资源的路径成分：v1.6.4 把
CLEAR/WATER/FOREST 等地形枚举译成中文后，引擎按名字拼图块路径失败，地图大面积
变黑（CHANGELOG v1.6.5）。当时的处置只清理了「全大写、无空格」的地形名，漏掉了：

  * 带斜杠的路径令牌：MINOR//（小河图块的目录令牌）
  * 自名型图块目录名：CUSTOM、FERRY、SAND、IMPASSABLE、HVY_URBAN 等
  * 路面质量子目录：ROAD\AVERAGE、ROAD\GOOD

本脚本把「会在路径里出现」的标识符机械地扫出来，写成 glossary/art_tokens.json，
由 mod/finalize.py 在出包前拒绝收录这些键，防止同类缺陷再次混进词典。

判定规则（与美术目录的命名约定对应）
------------------------------------
1. self_named_tile_dirs：Tiles 下（含一层子目录，如 ROAD\AVERAGE）若存在
   <目录名>_<数字>.tga，说明该目录名同时是文件名前缀，正是引擎用
   //Tiles//<目录>//<目录>_%03d.tga 拼出来的 —— 目录名必须保持英文原文。
2. tile_dirs / art_dirs：所有出现在 Dat\Art 下的目录名，命中时只告警，
   因为一部分模板把目录名写死（COAST/RAIL/WEATHER/FACTORY/PORT 等）。
3. path_tokens：从 EXE 字符串池里读出来的、直接拼进路径的令牌，
   例如 MINOR//、MAJOR//M、IMPASS//I、//units// 等，属硬编码常量。

用法
----
    python mod/scan_art_tokens.py                  # 自动定位游戏目录
    python mod/scan_art_tokens.py --art D:\...\Dat\Art
    python mod/scan_art_tokens.py --check          # 只比对，不写文件（不一致则退出码 2）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(PROJECT, "glossary", "art_tokens.json")

# 从 WarInTheEast2.exe 字符串池直接读出的路径令牌。
# 引擎用法：//Tiles//RIVER//%sR%d_%3.3d.tga，%s 取 MINOR// / MAJOR//M / IMPASS//I；
# 另有 //units// 开头的整串写死图（AttacksPossible.tga 等）。
PATH_TOKENS = {
    "MINOR//": "小河图块目录令牌，拼 //Tiles//RIVER//MINOR//R0_001.tga",
    "MAJOR//M": "大河图块目录令牌，拼 //Tiles//RIVER//MAJOR//MR0_001.tga",
    "IMPASS//I": "不可通行河图块令牌，拼 //Tiles//RIVER//IMPASS//IR0_001.tga",
    "//units//": "界面上写死的 //units//*.tga 前缀",
}


def find_art_dir(explicit):
    r"""按 显式参数 → settings.local.json → settings.json → 环境变量 的顺序定位 Dat\Art。"""
    candidates = []
    if explicit:
        candidates.append(explicit)
    for name in ("settings.local.json", "settings.json"):
        for base in (os.path.join(PROJECT, "mod"), PROJECT):
            path = os.path.join(base, name)
            try:
                with open(path, encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, ValueError):
                continue
            for key in ("game_path", "install_path", "game_dir", "wite2_path"):
                value = data.get(key)
                if isinstance(value, str) and value:
                    candidates.append(os.path.join(value, "Dat", "Art"))
    for env in ("WITE2_GAME", "WITE2_DIR"):
        value = os.environ.get(env)
        if value:
            candidates.append(os.path.join(value, "Dat", "Art"))
    for path in candidates:
        if os.path.isdir(path) and os.path.isdir(os.path.join(path, "Tiles")):
            return os.path.normpath(path)
    raise SystemExit(r"找不到 Dat\Art 目录，请用 --art 指定")


def _probe_self_named(directory, name, sink):
    """目录里若存在 <目录名>_<数字>.tga，则该目录名参与拼路径。"""
    try:
        files = os.listdir(directory)
    except OSError:
        return
    pattern = re.compile(r"^" + re.escape(name) + r"_0*\d+\.tga$", re.IGNORECASE)
    sample = next((f for f in files if pattern.match(f)), None)
    if sample:
        sink[name] = sample


def scan(art_dir):
    tiles = os.path.join(art_dir, "Tiles")
    tile_dirs = set()
    self_named = {}
    for entry in sorted(os.listdir(tiles)):
        sub = os.path.join(tiles, entry)
        if not os.path.isdir(sub):
            continue
        tile_dirs.add(entry)
        for inner in sorted(os.listdir(sub)):
            inner_path = os.path.join(sub, inner)
            if os.path.isdir(inner_path):
                tile_dirs.add(inner)
                _probe_self_named(inner_path, inner, self_named)
        _probe_self_named(sub, entry, self_named)

    art_dirs = set()
    for root, dirs, _files in os.walk(art_dir):
        rel = os.path.relpath(root, art_dir)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth > 2:
            dirs[:] = []
            continue
        for name in dirs:
            art_dirs.add(name)

    return {
        "_comment": "由 mod/scan_art_tokens.py 生成；finalize.py 守卫读此文件，勿手改。",
        "art_dir": "Dat/Art",  # 只记录相对位置，避免把本机绝对路径写进仓库
        "art_dirs": sorted(art_dirs),
        "tile_dirs": sorted(tile_dirs),
        "self_named_tile_dirs": {key: self_named[key] for key in sorted(self_named)},
        "path_tokens": PATH_TOKENS,
    }


def main(argv):
    parser = argparse.ArgumentParser(description=r"扫描 Dat\Art 生成美术路径标识符清单")
    parser.add_argument("--art", help=r"Dat\Art 目录，缺省自动定位")
    parser.add_argument("--out", default=OUT_PATH, help="输出文件，默认 glossary/art_tokens.json")
    parser.add_argument("--check", action="store_true", help="只比对现有文件是否一致")
    args = parser.parse_args(argv)

    data = scan(find_art_dir(args.art))
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"

    if args.check:
        try:
            with open(args.out, encoding="utf-8") as handle:
                current = handle.read()
        except OSError:
            print("缺少 %s，请先运行本脚本" % args.out)
            return 2
        if current != payload:
            print("%s 已过期，请重新生成" % args.out)
            return 2
        print("art_tokens.json 与美术目录一致：%d 个目录、%d 个自名型" % (
            len(data["tile_dirs"]), len(data["self_named_tile_dirs"])))
        return 0

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    print("已写 %s：tile_dirs=%d self_named=%d art_dirs=%d" % (
        args.out, len(data["tile_dirs"]), len(data["self_named_tile_dirs"]), len(data["art_dirs"])))
    print("自名型：%s" % ", ".join(data["self_named_tile_dirs"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
