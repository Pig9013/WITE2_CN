# -*- coding: utf-8 -*-
"""清理译文残渣（保守版 v2）。

顺序：
  1) 删 @@PH0@@ 之类内部占位符；
  2) 若出现空行分段，且末段是短中文（<=24 字），取末段——模型常在末尾给出最终答案；
  3) 否则若出现「应该是：/译文：」之类，取其后；
  4) 否则若出现解释标记，且其前是 >=4 字的完整中文（不以「但/并且/以及/而且/否则/因此」结尾），截断；
  5) 去掉结尾的小写拉丁残片（不动大写缩写与符号）；
  6) 合并叠字（军军→军 等）。
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"
REPORT = PROJECT / "audit" / "residue-report.txt"

PH = re.compile(r"@@[A-Za-z]+?\d*@@|@[a-z]+\s[^@]{0,40}@@")
MARK = re.compile(r"注意[:：]|由于|应该|保持原文|请提供|此处|术语表|建议|无法确定|无法给出|不需要翻译")
CUT_AFTER = re.compile(r"(?:应该是|译文|正确译名|最终结果|因此)\s*[:：]\s*")
LOWER_TAIL = re.compile(r"[a-z\u00e0-\u00ff]{1,7}$")
CJK = re.compile(r"[\u4e00-\u9fff]")
DUP = re.compile(r"(军|师|团|旅|营|兵)\1")
BAD_END = ("但", "并且", "以及", "而且", "否则", "因此", "所以", "而", "且")


def clean(v: str):
    if not v or not isinstance(v, str):
        return None
    s = PH.sub("", v)
    if "@" in s:                      # 中文译文里不该出现 @，一律当占位符残渣删掉
        s = s.replace("@", "")
    # 2) 末段短中文
    if "\n" in s:
        segs = [x.strip() for x in s.split("\n") if x.strip()]
        if len(segs) >= 2:
            last = segs[-1]
            if MARK.search(last) or last.startswith("（") or last.startswith("("):
                # 末段是模型注释，退回首段（若首段有中文）
                if CJK.search(segs[0]):
                    s = segs[0]
            elif 2 <= len(CJK.findall(last)) and len(last) <= 24 and not re.search(r"[A-Za-z]{4,}", last):
                s = last
    # 3) 显式答案标记
    if s is v or s == PH.sub("", v):
        m = CUT_AFTER.search(s)
        if m:
            s = s[m.end():].strip()
    # 4) 解释标记截断
    m = MARK.search(s)
    if m:
        head = s[: m.start()].strip(" 　，。,；;：:")
        if len(CJK.findall(head)) >= 2 and not head.endswith(BAD_END):
            s = head
    # 5)(6)
    s = LOWER_TAIL.sub("", s).strip(" 　-—·、")
    s = DUP.sub(r"\1", s)
    s = s.strip()
    if s and s != v and len(CJK.findall(s)) >= 1 and not re.search(r"@@", s):
        return s
    return None


def main() -> None:
    n = 0
    weak = []
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
            if isinstance(tr, str):
                new = clean(tr)
                if new:
                    row["translation"] = new
                    dirty = True
                    n += 1
                    if len(CJK.findall(new)) < 2:
                        weak.append((row.get("text"), new))
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
                if not z[i]:
                    continue
                new = clean(z[i])
                if new:
                    z[i] = new
                    dirty = True
                    cells += 1
        if dirty:
            with zh.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(zrows)

    # 词表类 CSV 也过一遍（build_maps 后读，会覆盖 jsonl）
    for rel, kc, vc in (("data/translations/unit_names_en_zh.csv", "en", "zh"),
                        ("build/translation.csv", "English Key", "Translated Text"),
                        ("mod/assets/translation.csv", "English Key", "Translated Text")):
        path = PROJECT / rel
        if not path.exists():
            continue
        raw = path.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        rows = list(csv.reader(raw.decode("utf-8-sig").splitlines(keepends=True)))
        if not rows:
            continue
        header = rows[0]
        if kc not in header or vc not in header:
            continue
        ki, vi = header.index(kc), header.index(vc)
        dirty = False
        for row in rows[1:]:
            if len(row) <= max(ki, vi):
                continue
            new = clean(row[vi])
            if new:
                row[vi] = new
                dirty = True
                cells += 1
        if dirty:
            with path.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(rows)

    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(f"{k!r} => {v!r}" for k, v in weak[:120]), encoding="utf-8")
    print(f"jsonl={n} csv_cells={cells} weak={len(weak)}")


if __name__ == "__main__":
    main()
