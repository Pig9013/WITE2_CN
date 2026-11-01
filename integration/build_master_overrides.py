# -*- coding: utf-8 -*-
"""把 glossary 下的各类定译汇总成单一覆盖层（build_maps 最后应用，优先级最高）。

动机：词典是多层叠加（jsonl → 词表 CSV → 场景 CSV），同一条要在多层各改一遍才生效，
修一次漏一层就会「反复改同一个词」。这里把所有定译汇成一份，一次改、处处生效。
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
GLOSS = PROJECT / "glossary"
OUT = GLOSS / "master_overrides.json"


def main() -> None:
    table = {}
    ref = GLOSS / "reference_overrides.json"
    if ref.exists():
        data = json.loads(ref.read_text(encoding="utf-8"))
        # 同一键可能同时出现在多个组（自动清理脚本会误收 UI 串）。
        # 优先级：terms（自动批量）< places < ui（人工逐条）。
        for group in ("terms", "places", "ui"):
            for k, v in (data.get(group) or {}).items():
                if isinstance(v, list) and v:
                    table[k] = v[0]
    manual = GLOSS / "manual_translations.json"
    if manual.exists():
        for k, v in json.loads(manual.read_text(encoding="utf-8")).items():
            table[k] = v
    OUT.write_text(json.dumps(table, ensure_ascii=False, indent=0), encoding="utf-8")
    print("master overrides:", len(table))


if __name__ == "__main__":
    main()
