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
    # 与丢弃层交叉核对：master_drops.json 里的键绝不能再进覆盖层，
    # 否则一旦 build_maps 的丢弃顺序被改回「drop 之后套覆盖」，死键就会复活
    # （v1.6.5 地形名变黑、v1.9.7 小河消失都是这条路径）。
    drops_path = GLOSS / "master_drops.json"
    if drops_path.exists():
        drops = set(json.loads(drops_path.read_text(encoding="utf-8")))
        revived = sorted(drops & set(table))
        if revived:
            raise SystemExit(
                "以下键在 master_drops.json 里已声明丢弃，却又出现在覆盖层："
                + "、".join(revived[:20])
                + "（请从 reference_overrides.json / manual_translations.json 删除）"
            )
    OUT.write_text(json.dumps(table, ensure_ascii=False, indent=0), encoding="utf-8")
    print("master overrides:", len(table))


if __name__ == "__main__":
    main()
