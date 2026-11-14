# -*- coding: utf-8 -*-
r"""把游戏原版 Dat\Info\unitInfo.csv 原样放回 overlay（单位百科正文）。

为什么不再翻译这一列
--------------------
百科正文由引擎直接从 CSV 读，不走本地化查表；单字节代码页下中文无法显示
（v1.2.2 实机验证：UTF-8 / GBK 两方案均失败，见 docs/交接_v1.9.9.md:58）。
所以这一列的正确状态是「游戏原版英文」，中文正文的交付物是
docs/百科中文版_v1.6.0.md 与 docs/百科中文版_v1.0.md。

为什么必须在 overlay 里放一份
-----------------------------
启动器的 overlay 覆盖是「有同名文件就盖」，删掉文件并不会撤销 runtime 里的
坏副本（mod/src/Launcher.cs:542-548 只写不删）。只有提供一份内容正确的同名文件，
下次启动才会把 runtime\Dat\Info\unitInfo.csv 修复回英文原版。
先例：v1.2.2 的 deviceInfo.csv 就是这么修的（CHANGELOG.md:1349）。

事故回顾
--------
build_maps.py 原来按 (文件名, id 列) 索引 body 译文，而 unitInfo.csv 的 id 列
只有 0 / 12 两个值，于是 1,168 行的正文被同一个键覆盖成同一句
「约翰·汤姆林森提供」（93,403 字节）。见 docs/师徽显示修复_v1.9.11.md。

用法
----
    python mod\restore_unit_info.py            # 恢复（在 build_variants 之后、finalize 之前）
    python mod\restore_unit_info.py --check    # 守卫：必须是游戏原版字节，正文列不能退化
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sys
from pathlib import Path

MOD = Path(__file__).resolve().parent
PROJECT = MOD.parent
PAYLOAD = MOD / "payload"
REL = Path("Dat") / "Info" / "unitInfo.csv"
TARGET = PAYLOAD / "overlay" / REL
# 少于这个数就说明正文列被合并成了少数几句（坏副本只有 1 句）。
MIN_DISTINCT = 1000


def find_game() -> Path:
    candidates = []
    if os.environ.get("WITE2_GAME"):
        candidates.append(Path(os.environ["WITE2_GAME"]))
    for settings in ("settings.local.json", "settings.json"):
        path = MOD / settings
        if not path.exists():
            continue
        try:
            cfg = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for key in ("game_path", "install_path"):
            if cfg.get(key):
                candidates.append(Path(cfg[key]))
        if cfg.get("install_path"):
            candidates.append(Path(cfg["install_path"]) / "runtime")
    for candidate in candidates:
        if (candidate / "WarInTheEast2.exe").exists():
            return candidate
    raise SystemExit("找不到游戏；请设置环境变量 WITE2_GAME 或在 mod\\settings.local.json 写 game_path。")


def profile(raw: bytes) -> tuple[int, int]:
    """返回 (行数, 正文列不同取值数)。原表是 cp1252，UTF-8 会解码失败。"""
    for encoding in ("cp1252", "utf-8-sig"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        rows = list(csv.reader(io.StringIO(text, newline="")))
        if not rows or "text" not in rows[0]:
            return 0, 0
        ti = rows[0].index("text")
        texts = {row[ti] for row in rows[1:] if len(row) > ti and row[ti].strip()}
        return len(rows) - 1, len(texts)
    return 0, 0


def variant_copies() -> list[Path]:
    return sorted((PAYLOAD / "variants").glob("*/overlay/" + str(REL)))


def restore() -> int:
    game = find_game()
    source = game / REL
    if not source.exists():
        raise SystemExit("游戏里没有 %s" % REL)
    raw = source.read_bytes()
    rows, distinct = profile(raw)
    if distinct < MIN_DISTINCT:
        raise SystemExit("源头文件本身就不对：%s 行只有 %d 种正文" % (rows, distinct))
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(raw)
    removed = 0
    for stale in variant_copies():
        stale.unlink()
        removed += 1
    print("恢复 unitInfo.csv：%d 字节 / %d 行 / %d 种正文 / sha256 %s"
          % (len(raw), rows, distinct, hashlib.sha256(raw).hexdigest()[:12]))
    if removed:
        print("删除语言包里的同名副本：%d 个（简体 overlay 对所有语言包生效）" % removed)
    return 0


def check() -> int:
    if not TARGET.exists():
        print("FAIL 缺少 %s（python mod\\restore_unit_info.py）" % TARGET.relative_to(PROJECT))
        return 1
    raw = TARGET.read_bytes()
    rows, distinct = profile(raw)
    problems = []
    if distinct < MIN_DISTINCT:
        problems.append("正文列只有 %d 种（至少 %d）" % (distinct, MIN_DISTINCT))
    stale = variant_copies()
    if stale:
        problems.append("语言包里还有同名副本 %d 个" % len(stale))
    try:
        game = find_game()
    except SystemExit:
        game = None
        print("（找不到游戏目录，跳过与原版字节比对）")
    if game is not None:
        original = (game / REL).read_bytes()
        if original != raw:
            problems.append("与游戏原版字节不一致（%d vs %d 字节）" % (len(raw), len(original)))
    if problems:
        for problem in problems:
            print("FAIL " + problem)
        return 1
    print("unitInfo guard: OK（%d 字节 / %d 行 / %d 种正文，与游戏原版一致）"
          % (len(raw), rows, distinct))
    return 0


def main() -> int:
    return check() if "--check" in sys.argv else restore()


if __name__ == "__main__":
    raise SystemExit(main())
