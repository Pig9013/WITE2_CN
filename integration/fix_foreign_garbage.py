# -*- coding: utf-8 -*-
"""清掉译文里混入的日文假名 / 西里尔字母，以及模型解释性废话。

来源：早期本地模型流水线在音译时把原文词尾（-ск/-ль/-ン/カ）留在中文里，
甚至有把「我没有提供…请使用…」这类指令回复写进译文的。这类脏数据在界面上就是方块。

两步：先逐条精确替换（MANUAL），再对剩下的做「剥离非中文字符」的机械清洗。
覆盖 data/**/*.jsonl（不含 extracted）与 build/scenario_csv_zh/**/*.zh.csv。
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"

KANA_CYR = re.compile(r"[\u3040-\u30ff\uff66-\uff9f\u0400-\u04ff]+")

# 整条重写（原文 -> 正确译文）
MANUAL = {
    "Loknya": "洛克尼亚",
    "Yama": "亚马",
    "Como": "科莫",
    "Pervomaysk": "五一城",
    "Stromsund": "斯特伦松德",
    "Chojnice": "霍伊尼采",
    "Troitsk": "特罗伊茨克",
    "Jurbarkas": "尤尔巴尔卡斯",
    "Viljandi": "维尔扬迪",
    "Fetesti": "费泰什蒂",
    "Tsarekonstantinovka": "察列康斯坦丁诺夫卡",
    "Bobrovitsa": "博布罗维察",
    "Goetzendorf": "格岑多夫",
    "Ruegen": "吕根岛",
    "Ekaterinovka": "叶卡捷琳诺夫卡",
    "Gyomaendrod": "久洛马恩德勒德",
    "Tarnava Mare": "大特尔纳瓦河",
    "Spassk-Ryazansky": "梁赞州斯帕斯克",
    "Notadden": "Notadden",
    "Radom": "拉多姆",
    "Penza": "彭扎",
    "P o i t o u": "普瓦图",
    "Coo": "科",
    "Sio": "Sio",
    "Yunyakha": "尤尼亚哈",
}

TIDY = [
    (r"[（(]\s*$", ""),
    (r"\s{2,}", " "),
    (r"^[\s\-—·]+", ""),
    (r"[\s\-—·]+$", ""),
]


def clean(text: str) -> str:
    s = KANA_CYR.sub("", text)
    for pat, rep in TIDY:
        s = re.sub(pat, rep, s)
    return s.strip()


def main() -> None:
    fixed = stripped = 0
    for path in sorted(DATA.rglob("*.jsonl")):
        if "extracted" in path.parts:
            continue
        text = path.read_text(encoding="utf-8-sig")
        if not text.strip():
            continue
        rows, dirty = [], False
        for line in text.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            tr = row.get("translation")
            src = row.get("text")
            if isinstance(tr, str):
                new = MANUAL.get(src, None)
                if new is None and (KANA_CYR.search(tr)):
                    new = clean(tr)
                    if new != tr:
                        stripped += 1
                elif new is not None and new != tr:
                    fixed += 1
                if new is not None and new != tr:
                    row["translation"] = new
                    dirty = True
            rows.append(row)
        if dirty:
            with path.open("w", encoding="utf-8", newline="\n") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

    from fix_scenario_names import find_game, load_rows
    game = find_game()
    base = game / "Dat" / "CSV"
    cells = 0
    for zh in sorted(CSVDIR.rglob("*.zh.csv")):
        rel = zh.relative_to(CSVDIR)
        src_p = base / rel.parent.name / rel.name.replace(".zh.csv", ".csv")
        if not src_p.exists():
            continue
        srows, _ = load_rows(src_p)
        zrows, bom = load_rows(zh)
        if len(srows) != len(zrows):
            continue
        dirty = False
        for s, z in zip(srows, zrows):
            for i in range(min(len(s), len(z))):
                if not KANA_CYR.search(z[i]):
                    continue
                new = MANUAL.get(s[i].strip()) or clean(z[i])
                if new and new != z[i]:
                    z[i] = new
                    dirty = True
                    cells += 1
        if dirty:
            with zh.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(zrows)

    print(f"manual={fixed} stripped={stripped} csv_cells={cells}")


if __name__ == "__main__":
    main()
