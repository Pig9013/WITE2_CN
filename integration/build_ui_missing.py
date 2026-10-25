#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pick UI-like EXE strings that are not yet in the launcher/base tables."""
from __future__ import annotations

import csv
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "data", "extracted", "exe.jsonl")
UI = os.path.join(ROOT, "data", "translations", "ui_14b.zh.jsonl")
BASE = os.path.join(ROOT, "build", "translation.csv")
OUT = os.path.join(ROOT, "data", "extracted", "ui_missing.jsonl")

LOCALE = re.compile(r"^[a-z]{2}[-_][A-Z]{2}$")
CODE = re.compile(r"^[a-z][A-Za-z0-9_.]*$")
HTTP = re.compile(r"^(Accept|Content|Cache|Connection|Access|Allow|Authorization|Proxy|Range|Referer|Retry|Server|Trailer|Transfer|Upgrade|User-Agent|Vary|Warning|WWW|If-|Last-|Max-|Pragma|Date|ETag|Expect|Expires|From|Host|Location|Origin|Cookie|Set-Cookie)")


def main():
    known = set()
    if os.path.exists(UI):
        for line in open(UI, encoding="utf-8"):
            if line.strip():
                known.add(json.loads(line).get("text", "").strip().lower())
    if os.path.exists(BASE):
        with open(BASE, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                known.add((r.get("English Key") or "").strip().lower())

    rows = [json.loads(line) for line in open(EXE, encoding="utf-8") if line.strip()]
    out = []
    seen = set()
    for r in rows:
        s = (r.get("text") or "").strip()
        if not (3 <= len(s) <= 80):
            continue
        if not re.search(r"[A-Za-z]", s) or s.lower() in known or s.lower() in seen:
            continue
        if LOCALE.match(s) or CODE.match(s) or HTTP.match(s):
            continue
        if s.count("/") + s.count("\\") > 0 or "::" in s or s.startswith("."):
            continue
        if s.isupper() and len(s) > 12:
            continue
        # UI-like: spaces/punctuation, or a capitalized phrase, or keywords.
        ui_like = (" " in s or ":" in s or "?" in s or "'" in s or
                   s[0].isupper() and any(c.islower() for c in s))
        if not ui_like:
            continue
        seen.add(s.lower())
        out.append({"id": r.get("id", ""), "text": s, "kind": "exe_ui",
                    "context": r.get("context", ""), "meta": r.get("meta", {})})
    with open(OUT, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print({"missing": len(out), "out": OUT, "sample": [x["text"] for x in out[:15]]})


if __name__ == "__main__":
    main()
