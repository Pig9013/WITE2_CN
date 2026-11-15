# -*- coding: utf-8 -*-
"""Build the compact localized-unit-name to original-crest-name table."""
import csv
import json
import os
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def game_root():
    cfg = ROOT / "settings.local.json"
    if cfg.exists():
        values = json.loads(cfg.read_text(encoding="utf-8"))
        for key in ("game_path", "install_path"):
            value = values.get(key)
            if value:
                path = pathlib.Path(value)
                if (path / "WarInTheEast2.exe").exists():
                    return path
                if (path / "runtime" / "WarInTheEast2.exe").exists():
                    return path / "runtime"
    value = os.environ.get("WITE2_GAME")
    if value and (pathlib.Path(value) / "WarInTheEast2.exe").exists():
        return pathlib.Path(value)
    raise SystemExit("找不到游戏目录：设置 WITE2_GAME 或 mod\\settings.local.json")


def read_table(path):
    raw = path.read_bytes()
    if raw[:8] != b"W2CNMAP1":
        raise SystemExit("invalid translation map: " + str(path))
    count, = struct.unpack_from("<I", raw, 8)
    offset, result = 12, {}
    for _ in range(count):
        a, b = struct.unpack_from("<II", raw, offset)
        offset += 8
        if not a or not b or offset + (a + b) * 2 > len(raw):
            raise SystemExit("truncated translation map: " + str(path))
        key = raw[offset:offset + a * 2].decode("utf-16le")
        offset += a * 2
        value = raw[offset:offset + b * 2].decode("utf-16le")
        offset += b * 2
        result[key] = value
    if offset != len(raw):
        raise SystemExit("trailing data in translation map: " + str(path))
    return result


def csv_rows(path):
    with path.open("r", encoding="cp1252", newline="", errors="replace") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return [], []
    head = [v.strip().lstrip("\ufeffï»¿") for v in rows[0]]
    return head, rows[1:]


def main():
    game = game_root()
    payload = ROOT / "payload"
    dictionaries = [json.loads((payload / "translations.json").read_text(encoding="utf-8"))]
    for code in ("zh-TW", "zh-HK", "zh-MO"):
        dictionaries.append(read_table(payload / "variants" / code / "translations.bin"))

    sym_root = game / "Dat" / "Art" / "Sym"
    stems = {p.stem for nation in sym_root.iterdir() if nation.is_dir() for p in nation.glob("*.tga")}
    pairs = set()
    for scenario in (game / "Dat" / "CSV").iterdir():
        if not scenario.is_dir():
            continue
        units, obs = scenario / "Units.csv", scenario / "OBs.csv"
        if not units.exists() or not obs.exists():
            continue
        uh, ur = csv_rows(units)
        oh, obr = csv_rows(obs)
        try:
            ni, ti = uh.index("Name"), uh.index("Type")
            oi, si = oh.index("ID"), oh.index("Suffix")
        except ValueError:
            continue
        suffixes = {r[oi].strip(): r[si].strip() for r in obr if len(r) > max(oi, si)}
        for row in ur:
            if len(row) <= max(ni, ti):
                continue
            name = row[ni].strip()
            if name:
                pairs.add((name, suffixes.get(row[ti].strip(), "")))
    print("Sym stems:", len(stems), "unit pairs:", len(pairs))

    mapping, collisions = {}, {}
    for name, suffix in pairs:
        english = name + (" " + suffix if suffix else "")
        if english not in stems:
            continue
        for dictionary in dictionaries:
            localized_name = dictionary.get(name, name)
            localized_suffix = dictionary.get(suffix, suffix) if suffix else ""
            localized = localized_name + (" " + localized_suffix if localized_suffix else "")
            if localized == english:
                continue
            previous = mapping.get(localized)
            if previous is not None and previous != english:
                collisions.setdefault(localized, {previous}).add(english)
            else:
                mapping[localized] = english
    for key in collisions:
        mapping.pop(key, None)
    print("candidate mappings:", len(mapping), "ambiguous names:", len(collisions))
    if collisions:
        for key, values in sorted(collisions.items()):
            print("  skipped ambiguous name:", repr(key), "->", repr(sorted(values)))

    items = sorted(mapping.items())
    blob = bytearray(b"W2CNCR1\0" + struct.pack("<I", len(items)))
    for key, value in items:
        a, b = key.encode("utf-16le"), value.encode("utf-16le")
        blob += struct.pack("<II", len(a) // 2, len(b) // 2) + a + b
    out = payload / "crest_names.bin"
    encoded = bytes(blob)
    if "--check" in sys.argv:
        if out.exists() and out.read_bytes() == encoded:
            print("Crest-name map: OK (%d entries, %d bytes)" % (len(items), len(encoded)))
            return 0
        print("Crest-name map: STALE; run python mod/build_crest_map.py")
        return 1
    out.write_bytes(encoded)
    print("Crest-name map: %d entries, %d bytes" % (len(items), len(encoded)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
