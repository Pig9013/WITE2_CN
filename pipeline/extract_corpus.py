#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract translatable text from a War in the East 2 installation.

Outputs JSONL records with a stable id, source file, kind, text and context.
No game files are modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from collections import Counter, defaultdict

DEFAULT_GAME = r"D:\Tool\Steam\steamapps\common\Gary Grigsby's War in the East 2"

INFO_FILES = {
    "deviceInfo.csv": "device",
    "aircraftInfo.csv": "aircraft",
    "groundInfo.csv": "ground",
    "leaderInfo.csv": "leader",
    "airGroupInfo.csv": "airgroup",
    "unitInfo.csv": "unit",
}

URL_RE = re.compile(r"<url>.*?</url>", re.I | re.S)
TAG_RE = re.compile(r"<[^<>]{1,40}>")
WS_RE = re.compile(r"[ \t]+")


def stable_id(*parts: object) -> str:
    h = hashlib.sha1("\x1f".join(str(p) for p in parts).encode("utf-8", "replace"))
    return h.hexdigest()[:16]


def clean_text(s: str) -> str:
    if s is None:
        return ""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\ufffd", "")
    return s.strip()


def has_letters(s: str) -> bool:
    return len(re.findall(r"[A-Za-z]", s)) >= 2


def read_info_csv(path: str):
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        sample = f.read(8192)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except Exception:
        dialect = csv.excel
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        yield from csv.DictReader(f, dialect=dialect)


def extract_info_csv(game: str, outdir: str):
    records = []
    for fname, kind in INFO_FILES.items():
        path = os.path.join(game, "Dat", "Info", fname)
        if not os.path.exists(path):
            continue
        for row in read_info_csv(path):
            row_id = (row.get("id") or "").strip()
            nat = (row.get("nat") or "").strip()
            # unitInfo uses Editor Name / Text Display Name
            names = []
            for key in ("name", "Editor Name", "Text Display Name"):
                val = clean_text(row.get(key, ""))
                if val:
                    names.append(val)
            seen = set()
            for val in names:
                for part in re.split(r"\s*;\s*", val):
                    part = clean_text(part)
                    if not part or part in seen or not has_letters(part):
                        continue
                    seen.add(part)
                    records.append({
                        "id": stable_id(fname, row_id, "name", part),
                        "source": fname,
                        "row_id": row_id,
                        "kind": f"{kind}_name",
                        "text": part,
                        "context": f"{fname} id={row_id} nat={nat}",
                        "meta": {"nat": nat},
                    })
            caption = clean_text(row.get("caption") or row.get("Caption") or "")
            if caption and has_letters(caption) and caption not in seen:
                records.append({
                    "id": stable_id(fname, row_id, "caption", caption),
                    "source": fname,
                    "row_id": row_id,
                    "kind": f"{kind}_caption",
                    "text": caption,
                    "context": f"{fname} id={row_id} nat={nat}",
                    "meta": {"nat": nat},
                })
            text = clean_text(row.get("text", ""))
            if text and has_letters(text):
                # Keep markup, remove URLs from the translatable body.
                body = URL_RE.sub("", text).strip()
                if body:
                    records.append({
                        "id": stable_id(fname, row_id, "text", body[:200]),
                        "source": fname,
                        "row_id": row_id,
                        "kind": f"{kind}_description",
                        "text": body,
                        "context": f"{fname} id={row_id} nat={nat}",
                        "meta": {"nat": nat},
                    })
    return records


def extract_scenarios(game: str):
    records = []
    scen_dir = os.path.join(game, "Dat", "Scen")
    if not os.path.isdir(scen_dir):
        return records
    for name in sorted(os.listdir(scen_dir)):
        if not name.lower().endswith(".txt"):
            continue
        path = os.path.join(scen_dir, name)
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            text = clean_text(f.read())
        if not text or not has_letters(text):
            continue
        records.append({
            "id": stable_id("scenario", name, text[:100]),
            "source": name,
            "row_id": "",
            "kind": "scenario_text",
            "text": text,
            "context": f"Dat/Scen/{name}",
            "meta": {"filename": name},
        })
    return records


def extract_exe_strings(game: str):
    """Extract UTF-16LE UI-like strings from the game executable.

    The engine stores user-facing strings as UTF-16LE. ASCII runs are mostly
    paths/symbols and are intentionally omitted.
    """
    exe = os.path.join(game, "WarInTheEast2.exe")
    if not os.path.exists(exe):
        return []
    data = open(exe, "rb").read()
    records = []
    seen = set()
    # ASCII chars encoded as UTF-16LE, at least 4 chars.
    for m in re.finditer(rb"(?:[\x20-\x7e]\x00){4,}", data):
        raw = m.group()
        try:
            s = raw.decode("utf-16le")
        except UnicodeDecodeError:
            continue
        s = s.strip()
        if not (4 <= len(s) <= 300):
            continue
        if not has_letters(s):
            continue
        # Filter technical/file strings.
        if re.search(r"(?:\.dll|\.exe|\.bmp|\.tga|\.wav|\.wmv|\.csv|\.dat|\.scn|\\|/|%[0-9.]*[a-zA-Z]|\{[0-9]+\})", s, re.I):
            continue
        if re.fullmatch(r"[A-Za-z0-9 _.,:;!?()\-+/'\"%]+", s) is None:
            continue
        # Skip obvious C++ identifiers / enum values.
        if re.fullmatch(r"[A-Z][A-Z0-9_]{3,}", s):
            continue
        if s in seen:
            continue
        seen.add(s)
        records.append({
            "id": stable_id("exe", m.start(), s),
            "source": "WarInTheEast2.exe",
            "row_id": str(m.start()),
            "kind": "exe_ui",
            "text": s,
            "context": f"exe offset 0x{m.start():x}",
            "meta": {"offset": m.start()},
        })
    return records


def write_jsonl(path: str, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def build_name_inventory(records):
    counts = Counter()
    sources = defaultdict(set)
    for r in records:
        if r["kind"].endswith("_name") or r["kind"] in ("exe_ui", "scenario_text"):
            text = r["text"]
            counts[text] += 1
            sources[text].add(r["source"])
    return counts, sources


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=DEFAULT_GAME)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "data", "extracted"))
    ap.add_argument("--skip-exe", action="store_true")
    args = ap.parse_args()
    outdir = os.path.abspath(args.out)
    os.makedirs(outdir, exist_ok=True)

    info = extract_info_csv(args.game, outdir)
    scen = extract_scenarios(args.game)
    exe = [] if args.skip_exe else extract_exe_strings(args.game)

    for name, recs in (("info", info), ("scenarios", scen), ("exe", exe)):
        write_jsonl(os.path.join(outdir, f"{name}.jsonl"), recs)

    all_recs = info + scen + exe
    write_jsonl(os.path.join(outdir, "all.jsonl"), all_recs)

    counts, sources = build_name_inventory(all_recs)
    inv_path = os.path.join(outdir, "name_inventory.csv")
    with open(inv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["text", "count", "sources"])
        for text, n in counts.most_common():
            w.writerow([text, n, ";".join(sorted(sources[text]))])

    summary = {
        "game": args.game,
        "info_records": len(info),
        "scenario_records": len(scen),
        "exe_records": len(exe),
        "total_records": len(all_recs),
        "unique_texts": len({r["text"] for r in all_recs}),
        "by_kind": dict(Counter(r["kind"] for r in all_recs)),
        "characters": sum(len(r["text"]) for r in all_recs),
    }
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
