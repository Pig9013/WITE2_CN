# -*- coding: utf-8 -*-
"""把 glossary/designations.py 的术语库导出成 Markdown 表（docs/番号与缩写术语表.md 的数据部分）。"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "glossary"))
import designations as D  # noqa: E402

OUT = PROJECT / "docs" / "番号与缩写术语表.generated.md"


def main() -> None:
    lines = []
    lines.append("## 一、苏联空军番号缩写（俄文原语）\n")
    lines.append("| 游戏中的写法 | 俄文缩写 | 俄文全称 | 中文定译 |")
    lines.append("|---|---|---|---|")
    for k, (ru, full, zh) in sorted(D.SOV_AIR.items(), key=lambda x: x[1][2]):
        lines.append(f"| {k} | {ru} | {full} | {zh} |")
    lines.append("")
    lines.append("## 二、舰队航空兵后缀\n")
    lines.append("| 写法 | 俄文缩写 | 俄文全称 | 中文 |")
    lines.append("|---|---|---|---|")
    for k, (ru, full, zh) in D.SOV_FLEET.items():
        lines.append(f"| {k} | {ru} | {full} | {zh} |")
    lines.append("")
    lines.append("## 三、苏联地面部队与统帅部预备队\n")
    lines.append("| 写法 | 俄文缩写 | 俄文全称 | 中文 |")
    lines.append("|---|---|---|---|")
    for k, (ru, full, zh) in D.SOV_GROUND.items():
        lines.append(f"| {k} | {ru} | {full} | {zh} |")
    lines.append("")
    lines.append("## 四、德军番号与司令部缩写\n")
    lines.append("| 写法 | 德文全称 | 中文定译 |")
    lines.append("|---|---|---|")
    for k, (full, zh) in sorted(D.DE_ABBR.items()):
        lines.append(f"| {k} | {full} | {zh} |")
    lines.append("")
    lines.append("## 五、德国空军联队与侦察大队\n")
    lines.append("| 写法 | 德文全称 | 中文 |")
    lines.append("|---|---|---|")
    for k, (full, zh) in sorted(D.DE_AIR.items()):
        lines.append(f"| {k} | {full} | {zh} |")
    lines.append("")
    lines.append("## 六、编制（TO&E）词表\n")
    lines.append("| 英文 | 中文 |")
    lines.append("|---|---|")
    for k, v in sorted(D.OB_WORDS.items()):
        lines.append(f"| {k} | {v} |")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", OUT, len(lines), "lines")


if __name__ == "__main__":
    main()
