#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge the missing-UI batch and manual UI words into translation_full.csv."""
from __future__ import annotations

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "build", "translation.csv")
EXTRA = os.path.join(ROOT, "data", "translations", "ui_extra.zh.jsonl")
MANUAL = os.path.join(ROOT, "glossary", "ui_extra.csv")
OUT = os.path.join(ROOT, "build", "translation_full.csv")
HEADER = ["ID", "English Key", "English Length", "Description",
          "max length", "Translate?", "Translated Text"]


def norm(s: str) -> str:
    return " ".join(s.strip().lower().split())


def main():
    rows = []
    seen = {}
    with open(BASE, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            src = (r.get("English Key") or "").strip()
            dst = (r.get("Translated Text") or "").strip()
            if not src or not dst:
                continue
            k = norm(src)
            if k in seen:
                continue
            seen[k] = len(rows)
            rows.append([r.get("ID", len(rows) + 1), src, len(src),
                         r.get("Description", ""), r.get("max length", ""), "Y", dst])
    added = 0
    if os.path.exists(EXTRA):
        for line in open(EXTRA, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            src = (r.get("text") or "").strip()
            dst = (r.get("translation") or "").strip()
            if not src or not dst or r.get("qa_status") == "blocked":
                continue
            # Keep phrases/labels; generic lowercase single words are internal keys.
            if src.islower() and " " not in src and norm(src) not in ("auto", "air", "support"):
                continue
            k = norm(src)
            if k in seen:
                continue
            seen[k] = len(rows)
            rows.append([len(rows) + 1, src, len(src), "ui-extra", "", "Y", dst])
            added += 1
    manual = 0
    if os.path.exists(MANUAL):
        with open(MANUAL, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                src = (r.get("en") or "").strip()
                dst = (r.get("zh") or "").strip()
                if not src or not dst:
                    continue
                k = norm(src)
                if k in seen:
                    rows[seen[k]][6] = dst
                else:
                    seen[k] = len(rows)
                    rows.append([len(rows) + 1, src, len(src), "ui-manual", "", "Y", dst])
                manual += 1
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    print(json.dumps({"base": len(rows) - added, "added": added, "manual": manual,
                      "total": len(rows), "out": OUT}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
