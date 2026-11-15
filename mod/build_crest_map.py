# -*- coding: utf-8 -*-
"""生成「本地化单位名 → 英文原名」映射（payload/crest_names.bin）。

引擎拼师徽路径：//Sym//<国码>//<本地化 Name> <本地化 Suffix>.tga
汉化后名字变中文 → 引擎内部的宽字符转窄字符（按字符数拷贝）在非 ASCII 处失效
→ 打不开文件 → 详情页师徽空白（引擎静默）。
本脚本把每个 (Name, Suffix) 组合按词典算出汉化后的拼装名，映射回英文拼装名，
DLL 在调用贴图加载前用这张表把路径改写回英文，等价于英文版的原始行为。
"""
import csv, io, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent


def find_game() -> pathlib.Path:
    import os
    env = os.environ.get("WITE2_GAME")
    if env and pathlib.Path(env).is_dir():
        return pathlib.Path(env)
    local = ROOT / "settings.local.json"
    if local.exists():
        data = json.loads(local.read_text(encoding="utf-8"))
        for key in ("game_path", "install_path"):
            p = data.get(key)
            if p and pathlib.Path(p).is_dir():
                g = pathlib.Path(p)
                if (g / "WarInTheEast2.exe").exists():
                    return g
                if (g / "runtime" / "WarInTheEast2.exe").exists():
                    return g / "runtime"
    raise SystemExit(r"找不到游戏目录：设置 WITE2_GAME 或 mod\settings.local.json")


def rows(path: pathlib.Path, enc: str):
    with open(path, "r", encoding=enc, newline="", errors="replace") as fh:
        data = list(csv.reader(fh))
    if not data:
        return [], []
    head = [h.replace("\ufeff", "").lstrip("\xef\xbb\xbf").strip() for h in data[0]]
    return head, data[1:]


def main() -> int:
    game = find_game()
    table = json.loads((ROOT / "payload" / "translations.json").read_text(encoding="utf-8"))
    stems = set()
    for d in sorted((game / "Dat" / "Art" / "Sym").iterdir()):
        if d.is_dir():
            for f in d.glob("*.tga"):
                stems.add(f.stem)
    print("Sym stems:", len(stems))

    pairs = set()
    scen_dirs = sorted(p for p in (game / "Dat" / "CSV").iterdir() if p.is_dir())
    for sd in scen_dirs:
        up = sd / "Units.csv"
        op = sd / "OBs.csv"
        if not (up.exists() and op.exists()):
            continue
        uh, ur = rows(up, "latin-1")
        oh, orow = rows(op, "latin-1")
        try:
            ni, ti = uh.index("Name"), uh.index("Type")
            oi, si = oh.index("ID"), oh.index("Suffix")
        except ValueError:
            continue
        suffix = {}
        for r in orow:
            if len(r) > max(oi, si):
                suffix[r[oi].strip()] = r[si].strip()
        for r in ur:
            if len(r) <= max(ni, ti):
                continue
            name = r[ni].strip()
            suf = suffix.get(r[ti].strip(), "")
            if name:
                pairs.add((name, suf))
    print("scenarios:", len(scen_dirs), "unique (Name,Suffix):", len(pairs))

    mapping, collisions, no_stem, same = {}, {}, 0, 0
    for name, suf in sorted(pairs):
        eng = name + (" " + suf if suf else "")
        loc_name = table.get(name, name)
        loc_suf = table.get(suf, suf) if suf else ""
        loc = loc_name + (" " + loc_suf if loc_suf else "")
        if loc == eng:
            same += 1
            continue
        if eng not in stems:
            no_stem += 1
            continue
        if loc in mapping and mapping[loc] != eng:
            collisions.setdefault(loc, [mapping[loc]]).append(eng)
            continue
        mapping[loc] = eng
    print("map entries:", len(mapping), "collisions:", len(collisions),
          "no-crest-file:", no_stem, "unchanged:", same)
    for k, v in list(collisions.items())[:6]:
        print("  collide:", k, "->", v)

    out = ROOT / "payload" / "crest_names.bin"
    items = sorted(mapping.items())
    body = bytearray(b"W2CNCR1\x00")   # 8 字节头，与 DLL 的读取偏移一致
    body += len(items).to_bytes(4, "little")
    for loc, eng in items:
        a = loc.encode("utf-16-le")
        b = eng.encode("utf-16-le")
        # 长度按 UTF-16 码元数（不是字节数），与 translations.bin 的约定一致
        body += (len(a) // 2).to_bytes(4, "little") + (len(b) // 2).to_bytes(4, "little") + a + b
    blob = bytes(body)
    existing = out.read_bytes() if out.exists() else b""
    if "--check" in sys.argv:
        if existing == blob:
            print("crest map: OK（%d 条 / %d 字节）" % (len(items), len(blob)))
            return 0
        print("crest map: STALE（词典/剧本/美术有变动）→ python mod/build_crest_map.py")
        return 1
    out.write_bytes(blob)
    print("wrote", out, len(blob), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
