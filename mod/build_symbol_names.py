# -*- coding: utf-8 -*-
r"""按译名补齐师徽/机徽贴图副本（Dat\Art\Sym、Dat\Art\AirSym）。

为什么需要这一步
----------------
引擎按「单位名」拼贴图路径，EXE 里的格式串是
    //Sym//%s//%s.tga          ← 单段名（无兵种后缀的单位，如 OKH）
    //Sym//%s//%s %s.tga       ← 两段名：Units.csv 的 Name + OBs.csv 的 Suffix
    //AirSym//%s//%s.tga
    //AirSym//%s//%s_air_default.tga
英文版里 \`1st\` + \` \` + \`Panzer Division\` 正好等于原图文件名 \`1st Panzer Division.tga\`。
汉化后两段各自走词典：\`1st\`（词典无此键，保持原样）+ \` \` + \`装甲师\`
= \`1st 装甲师.tga\` —— 我们从没生成过这个名字，而 \`第1装甲师.tga\` 引擎根本不会去查，
于是陆军师徽整片消失（引擎对缺图完全静默，不报错、不写 engine.log）。
空军之所以正常：AirSym 文件名是单段整名（\`1._NAGr 1.tga\`），没有第二段可被译坏。

这一步做什么
-----------
对每个语言包，从游戏原图复制两类中文名副本：
  1) 拼装名（主修）：\`<译(Name)> <译(Suffix)>\`，如 \`1st 装甲师.tga\`
  2) 整名（兼容）：词典里整条命中时的 \`<译(整名)>\`，如 \`第1装甲师.tga\`
只新增文件：不改原图、不改 EXE、不改 .scn、不改单位名。

用法
----
    python mod\build_symbol_names.py            # 生成（在 build_variants 之后、finalize 之前）
    python mod\build_symbol_names.py --check    # 守卫：清单里的副本必须都还在
    python mod\build_symbol_names.py --audit    # 覆盖核查：逐剧本×语言包统计缺失

产出
----
    payload\overlay\Dat\Art\{Sym,AirSym}\<国>\<译名>.tga
    payload\variants\<code>\overlay\Dat\Art\{Sym,AirSym}\<国>\<译名>.tga
    audit\symbol-art.json                       # 逐语言包清单（文件名与跳过原因）
"""
from __future__ import annotations

import csv
import io
import json
import os
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


# ── 游戏目录与数据表 ──────────────────────────────────────────────────────
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
            # 安装目录里的 runtime 是游戏资源的另一份完整拷贝
            candidates.append(Path(cfg["install_path"]) / "runtime")
    for candidate in candidates:
        if (candidate / "WarInTheEast2.exe").exists():
            return candidate
    raise SystemExit(r"找不到游戏；请设置环境变量 WITE2_GAME 或在 mod\settings.local.json 写 game_path。")


def _rows(path: Path) -> list[list[str]]:
    """读游戏原生 CSV。原表不是 UTF-8（含 0xe1 单字节），必须按 latin-1 解码。"""
    text = path.read_bytes().decode("latin-1")
    return list(csv.reader(io.StringIO(text)))


def _header(row: list[str]) -> list[str]:
    # 表头首列带 UTF-8 BOM，latin-1 解出来是 "ï»¿ID"
    return [c.strip().replace("\xef\xbb\xbf", "").replace("ï»¿", "").lower() for c in row]


def scenario_pairs(game: Path) -> set[tuple[str, str]]:
    """逐剧本取 (Units.csv Name, OBs.csv Suffix) —— 引擎拼贴图名用的就是这两段。"""
    pairs: set[tuple[str, str]] = set()
    csv_root = game / "Dat" / "CSV"
    if not csv_root.exists():
        return pairs
    for scen in sorted(p for p in csv_root.iterdir() if p.is_dir()):
        obs_path, unit_path = scen / "OBs.csv", scen / "Units.csv"
        if not (obs_path.exists() and unit_path.exists()):
            continue
        try:
            obs, units = _rows(obs_path), _rows(unit_path)
        except OSError:
            continue
        if not obs or not units:
            continue
        ho, hu = _header(obs[0]), _header(units[0])
        if not all(k in ho for k in ("id", "suffix")) or not all(k in hu for k in ("name", "type")):
            continue
        i_id, i_sfx = ho.index("id"), ho.index("suffix")
        suffix = {r[i_id]: r[i_sfx] for r in obs[1:] if len(r) > max(i_id, i_sfx)}
        i_name, i_type = hu.index("name"), hu.index("type")
        for row in units[1:]:
            if len(row) <= max(i_name, i_type):
                continue
            name, typ = row[i_name].strip(), suffix.get(row[i_type], "").strip()
            if name and typ:
                pairs.add((name, typ))
    return pairs


def art_stems(art_root: Path) -> dict[str, Path]:
    """英文贴图名 → 源文件（同一名字只取第一个国家目录）。"""
    stems: dict[str, Path] = {}
    if not art_root.exists():
        return stems
    for nat_dir in sorted(p for p in art_root.iterdir() if p.is_dir()):
        for src in sorted(nat_dir.glob("*.tga")):
            stems.setdefault(src.stem, src)
    return stems


def composed_names(game: Path, stems: dict[str, Path]) -> dict[str, list[tuple[str, str]]]:
    """{英文拼装名: [(Name, Suffix), ...]}，只保留真的有贴图的组合。

    同一张原图可能被不同剧本用不同的切分拼出来，例如
    `90th` + `Light Afrika Motorized Division` 与 `90th Light Afrika` + `Motorized Division`
    都拼成 `90th Light Afrika Motorized Division`，但两段分别查词典后译名不同
    （`90th 轻型非洲摩托化师` / `第90轻型非洲师 摩托化师`），两种都要生成。
    """
    out: dict[str, list[tuple[str, str]]] = {}
    for name, suffix in scenario_pairs(game):
        full = name + " " + suffix
        if full in stems:
            out.setdefault(full, []).append((name, suffix))
    return out


def ob_suffixes(game: Path) -> set[str]:
    """全部剧本 OBs.csv 的 Suffix 去重值 —— 引擎拼第二名时第二段只会取自这里。"""
    out: set[str] = set()
    csv_root = game / "Dat" / "CSV"
    if not csv_root.exists():
        return out
    for scen in sorted(p for p in csv_root.iterdir() if p.is_dir()):
        obs_path = scen / "OBs.csv"
        if not obs_path.exists():
            continue
        try:
            rows = _rows(obs_path)
        except OSError:
            continue
        if not rows:
            continue
        head = _header(rows[0])
        if "suffix" not in head:
            continue
        i = head.index("suffix")
        for row in rows[1:]:
            if i < len(row) and row[i].strip():
                out.add(row[i].strip())
    return out


def fallback_pairs(stems: dict[str, Path], composed: dict[str, list[tuple[str, str]]],
                   table: dict, suffixes: set[str]) -> dict[str, list[tuple[str, str]]]:
    """CSV 里没出现过的单位（DLC 专属等）按真实 Suffix 词表切分补齐。

    例：`11th SS Panzergrenadier Division` 不在 14 个基础剧本的 (Name, Suffix) 组合里，
    但引擎仍会用 `11th SS` + `Panzergrenadier Division` 拼名 → 需要 `第11党卫军 装甲掷弹兵师.tga`。
    只对「CSV 没覆盖、整名也没译」的贴图做，避免无谓放大体积。
    """
    out: dict[str, list[tuple[str, str]]] = {}
    for stem in stems:
        if stem in composed:
            continue
        if stem in table and table[stem] != stem:
            continue
        base, _tail = split_tail(stem)
        if base in composed:
            continue
        parts = stem.split(" ")
        for i in range(1, len(parts)):
            name, suffix = " ".join(parts[:i]), " ".join(parts[i:])
            if suffix in suffixes:
                out.setdefault(stem, []).append((name, suffix))
    return out


# ── 译名 ──────────────────────────────────────────────────────────────────
def split_tail(stem: str) -> tuple[str, str]:
    for suffix in SUFFIXES:
        if stem.endswith(suffix):
            return stem[: -len(suffix)], suffix
    return stem, ""


def loc_part(text: str, table: dict) -> str:
    """单个名字段查词典；保留 " (+)" / " (-)" / "_Alt" 这类尾巴。"""
    if text in table:
        return table[text]
    base, tail = split_tail(text)
    if tail and base in table:
        return table[base] + tail
    return text


def translated(stem: str, table: dict) -> tuple[str | None, str]:
    """英文贴图名 → 译名；返回 (译名 or None, 用到的后缀)。"""
    if stem in table:
        return table[stem], ""
    base, suffix = split_tail(stem)
    if suffix and base in table:
        return table[base] + suffix, suffix
    return None, ""


def plan_set(art_root: Path, table: dict, composed: dict[str, list[tuple[str, str]]]
             ) -> tuple[list[tuple[Path, str, str]], list[dict]]:
    """枚举一个美术目录，返回 ([(源文件, 目标相对路径, 类型)], [跳过记录])。"""
    copies, skipped = [], []
    if not art_root.exists():
        return copies, skipped
    for nat_dir in sorted(p for p in art_root.iterdir() if p.is_dir()):
        nat = nat_dir.name
        existing = {p.name.lower() for p in nat_dir.iterdir() if p.is_file()}
        taken: dict[str, str] = {}
        for src in sorted(nat_dir.glob("*.tga")):
            stem = src.stem
            base, tail = split_tail(stem)
            targets: list[tuple[str, str]] = []
            # ① 两段各自译后再拼接。优先按完整名查（有些 Suffix 自带 " (+)"），再按去掉后缀的基名查。
            for key, extra in ((stem, ""), (base, tail)):
                for name, suffix in composed.get(key, ()):
                    cand = loc_part(name, table) + " " + loc_part(suffix, table) + extra
                    if cand != stem and all(cand != t for t, _ in targets):
                        targets.append((cand, "composed"))
            whole, suffix = translated(stem, table)    # ② 整名命中词典
            if whole and whole != stem and all(whole != t for t, _ in targets):
                targets.append((whole, "whole"))
            for new, kind in targets:
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
                                    "target": new + ".tga", "reason": reason,
                                    "suffix": suffix, "kind": kind})
                    continue
                taken[new.lower()] = src.name
                copies.append((src, "%s/%s/%s.tga" % (art_root.name, nat, new), kind))
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
    if not art_roots["Sym"].exists():
        raise SystemExit("找不到游戏师徽目录：%s" % art_roots["Sym"])
    stems = {name: art_stems(root) for name, root in art_roots.items()}
    composed = {name: composed_names(game, stems[name]) for name in ART_SETS}
    suffixes = ob_suffixes(game)
    packs = language_packs()
    base_table = packs[0][1]
    fallback = {}
    for name in ART_SETS:
        fb = fallback_pairs(stems[name], composed[name], base_table, suffixes)
        fallback[name] = fb
        for stem, pairs in fb.items():
            composed[name].setdefault(stem, []).extend(pairs)
        print("%s：原图 %d 个，剧本拼装名 %d 个，兜底补 %d 个（Suffix 词表 %d）"
              % (name, len(stems[name]), len(composed[name]) - len(fb), len(fb), len(suffixes)))

    clean_previous()
    locales, files = {}, []
    for code, table, overlay in packs:
        copies, skipped = [], []
        for name in ART_SETS:
            c, s = plan_set(art_roots[name], table, composed[name])
            copies += [(src, dest, name, kind) for src, dest, kind in c]
            skipped += s
        total = 0
        for src, rel, name, kind in copies:
            target = overlay / "Dat" / "Art" / Path(rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
            total += target.stat().st_size
            files.append(str(target.relative_to(MOD).as_posix()))
        per_set = {name: sum(1 for _, _, n, _ in copies if n == name) for name in ART_SETS}
        per_kind = {k: sum(1 for _, _, _, kk in copies if kk == k) for k in ("composed", "whole")}
        locales[code] = {"copied": len(copies), "bytes": total, "per_art": per_set,
                         "per_kind": per_kind, "skipped": skipped}
        print("symbol-art %-6s 复制 %4d 个（%s；%s）/ %.1f MB，跳过 %d"
              % (code, len(copies),
                 ", ".join("%s %d" % (k, v) for k, v in per_set.items()),
                 ", ".join("%s %d" % (k, v) for k, v in per_kind.items()),
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


def audit() -> int:
    """逐剧本×语言包核查：有英文师徽的单位，本地化后是否都有对应副本。"""
    game = find_game()
    stems = {name: art_stems(game / "Dat" / "Art" / name) for name in ART_SETS}
    composed = {name: composed_names(game, stems[name]) for name in ART_SETS}
    csv_root = game / "Dat" / "CSV"
    problems = 0
    for code, table, overlay in language_packs():
        units_with_art = 0
        expected: set[tuple[str, str]] = set()     # (art, 本地化贴图名)
        for scen in sorted(p for p in csv_root.iterdir() if p.is_dir()):
            obs_path, unit_path = scen / "OBs.csv", scen / "Units.csv"
            if not (obs_path.exists() and unit_path.exists()):
                continue
            obs, units = _rows(obs_path), _rows(unit_path)
            if not obs or not units:
                continue
            ho, hu = _header(obs[0]), _header(units[0])
            if not all(k in ho for k in ("id", "suffix")) or not all(k in hu for k in ("name", "type")):
                continue
            i_id, i_sfx = ho.index("id"), ho.index("suffix")
            suffix = {r[i_id]: r[i_sfx] for r in obs[1:] if len(r) > max(i_id, i_sfx)}
            i_name, i_type = hu.index("name"), hu.index("type")
            for row in units[1:]:
                if len(row) <= max(i_name, i_type):
                    continue
                name, sfx = row[i_name].strip(), suffix.get(row[i_type], "").strip()
                if not name:
                    continue
                if sfx:
                    en = name + " " + sfx
                    if en in stems["Sym"]:
                        units_with_art += 1
                        expected.add(("Sym", table.get(name, name) + " " + table.get(sfx, sfx)))
                else:
                    if name in stems["Sym"]:
                        units_with_art += 1
                        expected.add(("Sym", table.get(name, name)))
                    if name in stems["AirSym"]:
                        units_with_art += 1
                        expected.add(("AirSym", table.get(name, name)))
        have: dict[str, set[str]] = {}
        for art in ART_SETS:
            stems_have: set[str] = set()
            root = overlay / "Dat" / "Art" / art
            if root.exists():
                for nat_dir in root.iterdir():
                    if nat_dir.is_dir():
                        stems_have |= {f.stem for f in nat_dir.glob("*.tga")}
            have[art] = stems_have
        missing = sorted((art, name) for art, name in expected if name not in have[art])
        # 只有本地化后仍然等于英文名的，才直接命中游戏原图，不算缺失
        really = [(art, name) for art, name in missing if name not in stems[art]]
        problems += len(really)
        print("audit %-6s 有徽单位行 %5d / 需副本 %4d / 缺失 %d"
              % (code, units_with_art, len(expected), len(really)))
        for art, name in really[:15]:
            print("   MISSING %s/%s.tga" % (art, name))
    if problems:
        raise SystemExit("refuse: %d 个本地化贴图名没有副本" % problems)
    print("Symbol-art audit: OK")
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
    if "--check" in sys.argv:
        sys.exit(check())
    if "--audit" in sys.argv:
        sys.exit(audit())
    sys.exit(generate())
