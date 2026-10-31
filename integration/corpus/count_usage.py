# -*- coding: utf-8 -*-
"""在中文语料里统计番号写法惯例（容忍 OCR 插入的空格）。"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

CORPUS = Path(r"D:\Tool\WITE2\corpus")
S = r"\s*"
PAT_GF = re.compile(r"近卫\s*第\s*(\d+)\s*([^\s，。；、：（）()]{0,8}?)(师|军|旅|团|集团军|航空军|航空师|航空团|骑兵军|坦克军|机械化军)")
PAT_GM = re.compile(r"第\s*(\d+)\s*近卫([^\s，。；、：（）()]{0,8}?)(师|军|旅|团|集团军|航空军|航空师|航空团|骑兵军|坦克军|机械化军)")
PAT_PVO1 = re.compile(r"防空\s*第\s*\d+")
PAT_PVO2 = re.compile(r"第\s*\d+\s*防空")
TOKENS = ["方面军", "集团军群", "集团军", "军", "师", "旅", "团", "歼击航空军", "强击航空团",
          "轰炸航空军", "混成航空师", "坦克军", "机械化军", "骑兵军", "步兵师", "近卫", "预备队",
          "最高统帅部", "国土防空军", "防空军", "防空部队", "突击集团军", "航空集团军"]


def main() -> None:
    roots = sys.argv[1:] or [str(CORPUS)]
    stats = Counter()
    ex = {"gf": [], "gm": [], "pvo1": [], "pvo2": []}
    files = []
    for root in roots:
        files += sorted(Path(root).rglob("full.txt"))
    total = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        total += len(text)
        for m in PAT_GF.finditer(text):
            stats["近卫第N"] += 1
            if len(ex["gf"]) < 15:
                ex["gf"].append(m.group(0).replace(" ", ""))
        for m in PAT_GM.finditer(text):
            stats["第N近卫"] += 1
            if len(ex["gm"]) < 15:
                ex["gm"].append(m.group(0).replace(" ", ""))
        stats["防空第N"] += len(PAT_PVO1.findall(text))
        stats["第N防空"] += len(PAT_PVO2.findall(text))
        for t in TOKENS:
            stats[t] += text.count(t)
    out = [f"files={len(files)} chars={total}"]
    for k, v in stats.most_common():
        out.append(f"{v:8d}  {k}")
    out.append("例 近卫第N: " + " / ".join(ex["gf"]))
    out.append("例 第N近卫: " + " / ".join(ex["gm"]))
    Path(r"D:\Tool\WITE2\_work\cn_usage.txt").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out[:14]))


if __name__ == "__main__":
    main()
