# -*- coding: utf-8 -*-
"""把仍是英文的长文本按人工译文覆盖。键是英文原文，值是中文。"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SRC = PROJECT / "glossary" / "manual_translations.json"


def main() -> None:
    table = json.loads(SRC.read_text(encoding="utf-8"))
    n = 0
    for path in sorted((PROJECT / "data").rglob("*.jsonl")):
        if "extracted" in path.parts:
            continue
        text = path.read_text(encoding="utf-8-sig")
        if not text.strip():
            continue
        rows, dirty = [], False
        for line in text.splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            src = r.get("text")
            if isinstance(src, str) and src in table:
                if r.get("translation") != table[src]:
                    r["translation"] = table[src]
                    dirty = True
                    n += 1
            rows.append(r)
        if dirty:
            with path.open("w", encoding="utf-8", newline="\n") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("applied:", n)


if __name__ == "__main__":
    main()
