#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build game-ready unit / air-group name tables from extracted JSONL."""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "pipeline"))

from name_rules import TOKEN_MAP, TYPO, translate_unit_name  # noqa: E402


def main():
    src = os.path.join(ROOT, "data", "extracted", "all.jsonl")
    outdir = os.path.join(ROOT, "data", "translations")
    os.makedirs(outdir, exist_ok=True)
    records = [json.loads(line) for line in open(src, encoding="utf-8") if line.strip()]
    names = []
    seen = set()
    for r in records:
        if r.get("kind") not in ("unit_name", "airgroup_name"):
            continue
        en = r.get("text", "").strip()
        if not en or en in seen:
            continue
        seen.add(en)
        zh = translate_unit_name(en)
        names.append({"en": en, "zh": zh or "", "source": r.get("source", ""),
                      "row_id": r.get("row_id", ""), "context": r.get("context", "")})
    names.sort(key=lambda x: x["en"].lower())
    failed = [n for n in names if not n["zh"]]
    out = os.path.join(outdir, "unit_names_en_zh.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["en", "zh", "source", "row_id", "context"])
        w.writeheader()
        w.writerows(names)

    token_rows = []
    for en, zh in sorted(TOKEN_MAP.items(), key=lambda kv: kv[0]):
        if not zh:
            continue
        token_rows.append({"en": en, "zh": zh, "type": "token"})
    for wrong, right in sorted(TYPO.items()):
        zh = TOKEN_MAP.get(right, "")
        token_rows.append({"en": wrong, "zh": zh, "type": f"typo->{right}"})
    tok_out = os.path.join(ROOT, "glossary", "unit_tokens_en_zh.csv")
    with open(tok_out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["en", "zh", "type"])
        w.writeheader()
        w.writerows(token_rows)

    print(json.dumps({
        "unit_names": len(names),
        "translated": len(names) - len(failed),
        "failed": len(failed),
        "out": out,
        "tokens": len(token_rows),
        "token_out": tok_out,
        "sample": names[:5],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
