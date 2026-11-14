# -*- coding: utf-8 -*-
r"""按译名补齐师徽/机徽贴图副本（Dat\Art\Sym、Dat\Art\AirSym）。

为什么需要这一步
----------------
引擎按「本地化之后的单位名」拼贴图路径：EXE 里的格式串是
    //Sym//%s//%s.tga
    //Sym//%s//%s %s.tga
    //AirSym//%s//%s.tga
    //AirSym//%s//%s_air_default.tga
词典把 1st Panzer Division 译成 第1装甲师 之后，引擎去找
    Dat\Art\Sym\GE\第1装甲师.tga
文件不存在 → 师徽静默消失（引擎不报错，也不写进 engine.log）。
美术本身没丢：runtime 的 Sym 目录与游戏原版逐国文件数完全一致，是「查不到」。

这一步做什么
------------
对每个语言包，把「英文名.tga」按该语言包的译名复制一份「中文名.tga」：
    zh-CN        → payload\overlay\Dat\Art\...
    zh-TW/HK/MO  → payload\variants\<code>\overlay\Dat\Art\...
只新增文件：不改原图、不改 EXE、不改 .scn、不改单位名。

用法
----
    python mod\build_symbol_names.py            # 生成（在 build_variants 之后、finalize 之前）
    python mod\build_symbol_names.py --check    # 守卫：清单里的副本必须都还在

产出
----
    payload\overlay\Dat\Art\{Sym,AirSym}\<国>\<译名>.tga
    payload\variants\<code>\overlay\Dat\Art\{Sym,AirSym}\<国>\<译名>.tga
    audit\symbol-art.json                       # 逐语言包清单（文件名与跳过原因）
"""
from __future__ import annotations

import json
import re
import shutil
import struct
import sys
from pathlib import Path

MOD = Path(__file__).resolve().parent
PROJECT = MOD.parent
PAYLOAD = MOD / "payload"
MANIFEST = PROJECT / "audit" / "symbol-art.json"
ART_SETS = ("Sym", "AirSym")
# 贴图文件名里出现过这三种后缀（2064 无后缀 / 6 个 " (+)" / 5 个 " (-)" / 2 个 "_Alt"）；
# 词典里只有去掉后缀的基名，所以译名要接回同样的后缀。
SUFFIXES = (" (-)", " (+)", "_Alt")
ILLEGAL = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


# ── 语言包 ────────────────────────────────────────────────────────────────
def read_bin(path: Path) -> dict:
    data = path.read_bytes()
    if data[:8] != b"W2CNMAP1":
        raise SystemExit("语言包格式错误：%s" % path)
    count = struct.unpack("<I", data[8:12])[0]
    offset, table = 12, {}
    for _ in range(count):
        a, b = struct.unpack("<II", data[offset:offset + 8])
        offset += 8
        key = data[offset:offset + a * 2].decode("utf-16le")
        offset += a * 2
        value = data[offset:offset + b * 2].decode("utf-16le")
        offset += b * 2
        table[key] = value
    if offset != len(data):
        raise SystemExit("语言包长度与条目数不符：%s" % path)
    return table


def language_packs() -> list[tuple[str, dict, Path]]:
    """返回 (语言代码, 词典, 该语言包的 overlay 根目录)。"""
    base = PAYLOAD / "translations.json"
    if not base.exists():
        raise SystemExit("缺少 mod\\payload\\translations.json；先跑 mod\\build_maps.py")
    packs = [("zh-CN", json.loads(base.read_text(encoding="utf8")), PAYLOAD / "overlay")]
    variants = PAYLOAD / "variants"
    if variants.exists():
        for folder in sorted(p for p in variants.iterdir() if p.is_dir()):
            # 启动器只在 Variant != "zh-CN" 时才覆盖 variants\<code>\overlay，
            # 简体走 payload\overlay，所以给 zh-CN 变体也生成一份纯属浪费。
            if folder.name == "zh-CN":
                continue
            blob = folder / "translations.bin"
            if not blob.exists():
                continue
            packs.append((folder.name, read_bin(blob), folder / "overlay"))
    return packs


# ── 游戏目录 ──────────────────────────────────────────────────────────────
def find_game() -> Path:
    candidates = []
    for name in ("WITE2_GAME",):
        import os
        if os.environ.get(name):
            candidates.append(Path(os.environ[name]))
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
            # 安装目录里的 runtime 是游戏资源的另一份完整拷贝
            candidates.append(Path(cfg["install_path"]) / "runtime")
    for candidate in candidates:
        if (candidate / "WarInTheEast2.exe").exists():
            return candidate
    raise SystemExit("找不到游戏；请设置环境变量 WITE2_GAME 或在 mod\\settings.local.json 写 game_path。")


# ── 译名 ──────────────────────────────────────────────────────────────────
def translated(stem: str, table: dict) -> tuple[str | None, str]:
    """英文贴图名 → 译名；返回 (译名 or None, 用到的后缀)。"""
    if stem in table:
        return table[stem], ""
    for suffix in SUFFIXES:
        if stem.endswith(suffix):
            base = stem[: -len(suffix)]
            if base in table:
                return table[base] + suffix, suffix
    return None, ""


def plan_set(art_root: Path, table: dict) -> tuple[list[tuple[Path, str]], list[dict]]:
    """枚举一个美术目录，返回 ([(源文件, 目标相对路径)], [跳过记录])。"""
    copies, skipped = [], []
    if not art_root.exists():
        return copies, skipped
    for nat_dir in sorted(p for p in art_root.iterdir() if p.is_dir()):
        nat = nat_dir.name
        existing = {p.name.lower() for p in nat_dir.iterdir() if p.is_file()}
        taken: dict[str, str] = {}
        for src in sorted(nat_dir.glob("*.tga")):
            stem = src.stem
            new, suffix = translated(stem, table)
            if not new or new == stem:
                continue
            reason = ""
            if ILLEGAL.search(new):
                reason = "译名含非法文件名字符"
            elif new != new.strip() or new.startswith("."):
                reason = "译名首尾有空格或以点开头"
            elif len(new) > 120:
                reason = "译名过长"
            elif (new + ".tga").lower() in existing:
                reason = "目标名已被原版贴图占用"
            elif new.lower() in taken:
                reason = "译名与 %s 撞名" % taken[new.lower()]
            if reason:
                skipped.append({"art": art_root.name, "nation": nat, "source": src.name,
                                "target": new + ".tga", "reason": reason, "suffix": suffix})
                continue
            taken[new.lower()] = src.name
            copies.append((src, "%s/%s/%s.tga" % (art_root.name, nat, new)))
    return copies, skipped


# ── 主流程 ────────────────────────────────────────────────────────────────
def clean_previous() -> list[str]:
    """删掉上一轮生成的中文名副本，避免改了译名后留下孤儿文件。"""
    if not MANIFEST.exists():
        return []
    old = json.loads(MANIFEST.read_text(encoding="utf-8"))
    removed = 0
    for rel in old.get("files", []):
        target = (MOD / rel).resolve()
        if not str(target).startswith(str(MOD.resolve())):
            continue
        if target.is_file():
            target.unlink()
            removed += 1
    if removed:
        print("清理上一轮副本：%d 个" % removed)
    return old.get("files", [])


def generate() -> int:
    game = find_game()
    art_roots = {name: game / "Dat" / "Art" / name for name in ART_SETS}
    missing = [name for name, root in art_roots.items() if not root.exists()]
    if "Sym" in missing:
        raise SystemExit("找不到游戏师徽目录：%s" % art_roots["Sym"])

    clean_previous()
    locales, files = {}, []
    for code, table, overlay in language_packs():
        copies, skipped = [], []
        for name in ART_SETS:
            c, s = plan_set(art_roots[name], table)
            copies += [(src, dest, name) for src, dest in c]
            skipped += s
        total = 0
        for src, rel, name in copies:
            target = overlay / "Dat" / "Art" / Path(rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
            total += target.stat().st_size
            files.append(str(target.relative_to(MOD).as_posix()))
        per_set = {name: sum(1 for _, _, n in copies if n == name) for name in ART_SETS}
        locales[code] = {"copied": len(copies), "bytes": total, "per_art": per_set,
                         "skipped": skipped}
        print("symbol-art %-6s 复制 %3d 个（%s）/ %.1f MB，跳过 %d"
              % (code, len(copies), ", ".join("%s %d" % (k, v) for k, v in per_set.items()),
                 total / 1048576.0, len(skipped)))
        for item in skipped:
            print("   SKIP %s/%s/%s → %s（%s）"
                  % (item["art"], item["nation"], item["source"], item["target"], item["reason"]))

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({"game": str(game), "files": sorted(files),
                                    "locales": locales}, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print("清单：%s（%d 个文件）" % (MANIFEST.relative_to(PROJECT), len(files)))
    return 0


def check() -> int:
    if not MANIFEST.exists():
        raise SystemExit("缺少 audit/symbol-art.json；先跑 python mod/build_symbol_names.py")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing = [rel for rel in manifest.get("files", []) if not (MOD / rel).is_file()]
    if missing:
        for rel in missing[:10]:
            print("  MISSING %s" % rel)
        raise SystemExit("refuse: %d 个师徽副本缺失（python mod/build_symbol_names.py 重生成）" % len(missing))
    total = sum(manifest["locales"][code]["copied"] for code in manifest["locales"])
    print("Symbol-art guard: OK (%d 个副本 / %d 个语言包)" % (total, len(manifest["locales"])))
    return 0


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv else generate())
