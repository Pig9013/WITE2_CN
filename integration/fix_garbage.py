# -*- coding: utf-8 -*-
"""修掉译文里的乱码残渣（U+FFFD、混入的阿拉伯/泰/韩/埃塞俄比亚字母、'iếc' 之类）。

这些是早期模型流水线留下的脏数据，界面上会显示成方块，也会把字体字符集撑大。
做法是逐条精确替换（不做猜测性批量替换），jsonl 与剧本 CSV 一起改。
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
CSV_DIR = PROJECT / "build" / "scenario_csv_zh"

# 精确替换表：脏串 -> 正确串
REPL = [
    ("转隶航空队至预备\ufffd\ufffd态", "转隶航空队至预备状态"),
    ("选择建造单位\niếc单位进行建造", "选择建造单位"),
    ("东界X\niếc", "东界X"),
    ("iếc", ""),
    ("\ufffd", ""),
    ("新阿赫特尔스크", "新阿尔汉格尔斯克"),
    ("迪亚뎀", "王冠"),
    ("尼켈", "尼克尔"),
    ("加拉ți", "加拉茨"),
    ("皮亚季卡ți", "皮亚季哈特基"),
    ("雅블ォネツ", "雅布洛涅茨"),
    ("霍โฆ", "许"),
    ("米拉ندела", "米兰德拉"),
    ("玛斯卡ራ", "马斯卡拉"),
    ("热季诺普德拉斯كي", "拉曾波德拉斯基"),
    ("丘克وف", "崔可夫"),
    ("威尔ارد S.", "威拉德 S."),
    ("威尔ارد G.", "威拉德 G."),
    ("辛特尼克拉스", "圣尼克拉斯"),
]


def fix(text: str) -> str:
    for a, b in REPL:
        if a in text:
            text = text.replace(a, b)
    return text


def main() -> None:
    changed = 0
    for path in sorted(DATA.rglob("*.jsonl")):
        text = path.read_text(encoding="utf-8-sig")
        if not text.strip():
            continue
        rows, dirty = [], False
        for line in text.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            tr = row.get("translation")
            if isinstance(tr, str):
                new = fix(tr)
                if new != tr:
                    row["translation"] = new
                    dirty = True
                    changed += 1
            rows.append(row)
        if dirty:
            with path.open("w", encoding="utf-8", newline="\n") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

    for path in sorted(CSV_DIR.rglob("*.zh.csv")):
        raw = path.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        try:
            txt = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            continue
        rows, dirty = [], False
        for row in csv.reader(txt.splitlines(keepends=True)):
            out = []
            for cell in row:
                new = fix(cell)
                if new != cell:
                    dirty = True
                    changed += 1
                out.append(new)
            rows.append(out)
        if dirty:
            with path.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(rows)

    print("fixed strings:", changed)


if __name__ == "__main__":
    main()
