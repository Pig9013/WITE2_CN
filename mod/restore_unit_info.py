# -*- coding: utf-8 -*-
r"""把游戏原版 Dat\Info 的百科表原样放回 overlay（正文列是引擎直读的单字节文本）。

为什么不再翻译这几列
--------------------
百科正文由引擎直接从 CSV 读，不走本地化查表；单字节代码页下中文无法显示
（v1.2.2 实机验证：UTF-8 / GBK 两方案均失败，见 docs/交接_v1.9.9.md:58）。
所以这几列的正确状态是「游戏原版英文」，中文正文的交付物是
docs/百科中文版_v1.6.0.md 与 docs/百科中文版_v1.0.md。

为什么必须在 overlay 里放一份
----------------------------
启动器的 overlay 覆盖是「有同名文件就盖」，删掉文件并不会撤销 runtime 里的
坏副本（mod/src/Launcher.cs:542-548 只写不删）。只有提供一份内容正确的同名文件，
下次启动才会把 runtime\Dat\Info\*.csv 修复回英文原版。

事故回顾
--------
1) unitInfo.csv：build_maps.py 原来按 (文件名, id 列) 索引 body 译文，而该表 id 列
   只有 0 / 12 两个值，于是 1,168 行正文被覆盖成同一句「约翰·汤姆林森提供」
   （93,403 字节）。见 docs/师徽显示修复_v1.9.11.md。
2) deviceInfo.csv / groundInfo.csv / leaderInfo.csv：同一机制，这三张表的 id 列全为 0，
   4 / 2 / 2 行正文各自塌成一句（Mosin M38 / KV-1 / 沙波什尼科夫）。
   见 docs/空军AI自动分配_排查_v1.9.15.md:68。v1.9.16 批次按 unitInfo 的先例一并恢复。

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

# (文件名, 正文列不同取值数下限)。少于下限说明正文列被合并成了少数几句。
FILES = (
    ("unitInfo.csv", 1000),
    ("deviceInfo.csv", 2),
    ("groundInfo.csv", 2),
    ("leaderInfo.csv", 2),
)


def rel(name: str) -> Path:
    return Path("Dat") / "Info" / name


def target(name: str) -> Path:
    return PAYLOAD / "overlay" / rel(name)


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
    """返回 (行数, 正文列不同取值数)。原表多为 cp1252，groundInfo 是 UTF-8-sig。"""
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


def variant_copies(name: str) -> list[Path]:
    return sorted((PAYLOAD / "variants").glob("*/overlay/" + rel(name).as_posix()))


def restore() -> int:
    game = find_game()
    removed = 0
    for name, min_distinct in FILES:
        source = game / rel(name)
        if not source.exists():
            raise SystemExit("游戏里没有 %s" % rel(name))
        raw = source.read_bytes()
        rows, distinct = profile(raw)
        if distinct < min_distinct:
            raise SystemExit("源头文件本身就不对：%s 有 %d 行，正文只有 %d 种（至少 %d）"
                             % (name, rows, distinct, min_distinct))
        dest = target(name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        for stale in variant_copies(name):
            stale.unlink()
            removed += 1
        print("恢复 %s：%d 字节 / %d 行 / %d 种正文 / sha256 %s"
              % (name, len(raw), rows, distinct, hashlib.sha256(raw).hexdigest()[:12]))
    if removed:
        print("删除语言包里的同名副本：%d 个（简体 overlay 对所有语言包生效）" % removed)
    return 0


def check() -> int:
    problems = []
    try:
        game = find_game()
    except SystemExit:
        game = None
        print("（找不到游戏目录，跳过与原版字节比对）")
    for name, min_distinct in FILES:
        dest = target(name)
        if not dest.exists():
            problems.append("缺少 %s（python mod\\restore_unit_info.py）" % dest.relative_to(PROJECT))
            continue
        raw = dest.read_bytes()
        rows, distinct = profile(raw)
        if distinct < min_distinct:
            problems.append("%s 正文列只有 %d 种（至少 %d）" % (name, distinct, min_distinct))
        stale = variant_copies(name)
        if stale:
            problems.append("%s 在语言包里还有同名副本 %d 个" % (name, len(stale)))
        if game is not None:
            original = (game / rel(name)).read_bytes()
            if original != raw:
                problems.append("%s 与游戏原版字节不一致（%d vs %d 字节）"
                                % (name, len(raw), len(original)))
    if problems:
        for problem in problems:
            print("FAIL " + problem)
        return 1
    print("Info guard: OK（%s 均与游戏原版逐字节一致）" % "、".join(n for n, _ in FILES))
    return 0


def main() -> int:
    return check() if "--check" in sys.argv else restore()


if __name__ == "__main__":
    raise SystemExit(main())
