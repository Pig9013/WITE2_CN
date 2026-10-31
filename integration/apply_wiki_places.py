# -*- coding: utf-8 -*-
"""用维基百科中文名订正地名（audit/place-wikipedia.tsv）。

过滤掉明显不适用的：
  - 带行政区后缀的（…区 / …县 / …市 / …首都大区）
  - 中文名过长（地图标签放不下）
  - 明显是消歧义误配（维基条目取的是动物/常用词）
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
TSV = PROJECT / "audit" / "place-wikipedia.tsv"
OV = PROJECT / "glossary" / "reference_overrides.json"

BAD_SUFFIX = ("区", "县", "市", "首都大区", "州", "郡", "省")
BAD_WORDS = {"狞猫", "爸爸", "猎豹", "全部", "湖", "河"}
NOTE = "维基百科中文条目名（en→zh langlinks，OpenCC 转简体）"


def main() -> None:
    rows = list(csv.DictReader(TSV.open(encoding="utf-8"), delimiter="\t"))
    ov = json.loads(OV.read_text(encoding="utf-8"))
    places = ov.setdefault("places", {})
    n = skip = 0
    skipped = []
    for r in rows:
        en, ours, wiki = r["english"], r["ours"], r["wikipedia_zh"]
        if not wiki or not en:
            continue
        if wiki in BAD_WORDS or wiki.endswith(BAD_SUFFIX):
            skip += 1
            skipped.append((en, ours, wiki))
            continue
        if len(wiki) > len(ours) + 6:
            skip += 1
            skipped.append((en, ours, wiki))
            continue
        places[en] = [wiki, NOTE]
        n += 1
    OV.write_text(json.dumps(ov, indent=1, ensure_ascii=False), encoding="utf-8")
    (PROJECT / "audit" / "place-wiki-skipped.tsv").write_text(
        "\n".join(f"{a}\t{b}\t{c}" for a, b, c in skipped), encoding="utf-8")
    print(f"applied={n} skipped={skip}")


if __name__ == "__main__":
    main()
