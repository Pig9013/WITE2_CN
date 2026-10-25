#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a CJK subset font for WitE2 and optionally patch GuiFonts.json.

The engine enumerates the font's Unicode ranges and pre-rasterizes glyphs, so a
full 20k-glyph CJK font would create an enormous atlas.  We include exactly the
characters used by the translation plus ASCII/punctuation.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil

from fontTools.ttLib import TTFont
from fontTools.subset import Options, Subsetter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PUNCT = "，。！？；：、“”‘’（）《》〈〉—…·【】〔〕％＋－×÷＝／＼～　"
ASCII = "".join(chr(i) for i in range(0x20, 0x7F))
EXTRA = "@#&*()[]{}<>%$+-=/_\\|'~^:;,.!?0123456789"


def collect_chars() -> str:
    chars = set(ASCII) | set(PUNCT) | set(EXTRA) | set("\u00a0\u2013\u2014\u2026\u00b7")
    for pattern in (
        os.path.join(ROOT, "data", "translations", "*.jsonl"),
        os.path.join(ROOT, "data", "scenario_csv", "translations", "*.jsonl"),
        os.path.join(ROOT, "data", "translations", "*.csv"),
        os.path.join(ROOT, "glossary", "*.csv"),
        os.path.join(ROOT, "data", "extracted", "*.jsonl"),
    ):
        for path in glob.glob(pattern):
            try:
                text = open(path, encoding="utf-8-sig", errors="replace").read()
            except Exception:
                continue
            chars.update(text)
    chars = {c for c in chars if ord(c) >= 0x20 and not (0xD800 <= ord(c) <= 0xDFFF)}
    return "".join(sorted(chars))


def rename_font(font: TTFont, family: str):
    name = font["name"]
    for rec in name.names:
        if rec.nameID in (1, 3, 4, 6, 16, 17):
            try:
                rec.string = family
            except Exception:
                pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=r"C:\Windows\Fonts\msyh.ttc")
    ap.add_argument("--font-number", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "WitE2CN.ttf"))
    ap.add_argument("--family", default="WitE2CN")
    ap.add_argument("--chars-file", default="")
    ap.add_argument("--gui-fonts", default="")
    ap.add_argument("--game", default=r"D:\Tool\Steam\steamapps\common\Gary Grigsby's War in the East 2")
    ap.add_argument("--install", action="store_true")
    args = ap.parse_args()

    text = open(args.chars_file, encoding="utf-8").read() if args.chars_file else collect_chars()
    text = "".join(sorted(set(text) | set(ASCII) | set(PUNCT)))
    print(f"characters: {len(text)}")

    font = TTFont(args.src, fontNumber=args.font_number)
    options = Options()
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.notdef_outline = True
    options.recalc_bounds = True
    options.drop_tables += ["DSIG"]
    subsetter = Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    rename_font(font, args.family)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    font.save(args.out)
    print(f"wrote {args.out} ({os.path.getsize(args.out)/1024:.0f} KB)")

    if args.install:
        dst_dir = os.path.join(args.game, "Dat", "Fonts")
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(args.out, os.path.join(dst_dir, "WitE2CN.ttf"))
        gui = args.gui_fonts or os.path.join(args.game, "Dat", "GuiFonts.json")
        if not os.path.exists(gui + ".orig"):
            shutil.copy2(gui, gui + ".orig")
        with open(gui, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        for key, val in data.items():
            if isinstance(val, dict) and val.get("active") == "true":
                val["name"] = args.family
                val["file"] = "WitE2CN.ttf"
        with open(gui, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent="\t")
        print(f"installed font and patched {gui}")


if __name__ == "__main__":
    main()
