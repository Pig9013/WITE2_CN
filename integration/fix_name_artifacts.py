# -*- coding: utf-8 -*-
"""清理「LLM 元话语 / 转义残留 / 缩写误读」类译名脏值（v1.9.10 批次三）。

三类脏值：
1. 译文里混入翻译过程的元话语（「…不在翻译范围内，因此最终译文为：…」「…请注意…」）；
2. 译名后粘连原文残片（Debden -> 德宾dden）或转义符被读成文字（Harrowbeer -> 哈罗贝尔回车符）；
3. 缩写被当成单词误译（Fin. 芬兰 -> 结束、Hun. 匈牙利 -> 霍恩）。

脏值同时存在于两层：jsonl 语料层（data/**）与场景 CSV 显示层（build/scenario_csv_zh/**）。
本脚本按精确值替换两层，--check 只报不写（有残留返回 2）。
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 字典键（英文）-> 正译。键必须精确匹配，避免误伤同名长文本。
DICT_FIX = {
    "HQ Hun.": "匈军司令部",            # Hun. = Hungarian，不是 Horn
    "Fin. Air Base": "芬兰空军基地",     # Fin. = Finnish，不是 finish
    "Fin. Machine Gun Battalion": "芬兰机枪营",  # 旧值以句点开头
    "5th Rail.": "第5铁路部队",          # 旧值结尾多一个句号
    "Debden": "德布登",                  # 旧值混入原文残片与注释
    "Harrowbeer": "哈罗比尔",            # 旧值是问答式元话语
    "Lyzha": "利扎",                     # 旧值混入原文残片与「说明」
}

# 场景 CSV 里的脏单元格（精确值）-> 正译。与 DICT_FIX 的值保持一致。
CELL_FIX = {
    "司令部霍恩。": "匈军司令部",
    "结束。机场": "芬兰空军基地",
    ".机枪营": "芬兰机枪营",
    "5号铁路部队。": "第5铁路部队",
    "德宾dden（地名保留英文，避免不准确的音译）": "德布登",
    "德宾镇": "德布登",
    "哈罗贝尔回答问题时，请注意提供的信息表明没有现成的": "哈罗比尔",
    "哈罗贝尔回车符": "哈罗比尔",
    "利扎hya 说明": "利扎",
}


def fix_jsonl(check: bool, apply: bool) -> tuple[int, int]:
    changed_files = 0
    changed_cells = 0
    pat = glob.glob(os.path.join(ROOT, "data", "**", "*.jsonl"), recursive=True)
    for path in sorted(pat):
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
        out = []
        touched = 0
        for line in lines:
            stripped = line.strip()
            if not stripped:
                out.append(line)
                continue
            try:
                rec = json.loads(stripped)
            except ValueError:
                out.append(line)
                continue
            text = rec.get("text")
            if isinstance(text, str) and text in DICT_FIX and rec.get("translation") != DICT_FIX[text]:
                rec["translation"] = DICT_FIX[text]
                touched += 1
                out.append(json.dumps(rec, ensure_ascii=False) + ("\n" if line.endswith("\n") else ""))
            else:
                out.append(line)
        if touched:
            changed_files += 1
            changed_cells += touched
            if not check:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.writelines(out)
    return changed_files, changed_cells


def _load(path: str):
    """读 CSV，保留 BOM 与行尾；用 StringIO(newline="") 才能字节级往返。"""
    import io

    with open(path, "rb") as fh:
        raw = fh.read()
    bom = b""
    if raw.startswith(b"\xef\xbb\xbf"):
        bom = raw[:3]
        raw = raw[3:]
    newline = "\r\n" if b"\r\n" in raw[:4000] else "\n"
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline="")))
    return bom, newline, rows


def _dump(path: str, bom: bytes, newline: str, rows) -> None:
    import io

    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator=newline)
    w.writerows(rows)
    with open(path, "wb") as fh:
        fh.write(bom + buf.getvalue().encode("utf-8"))


def fix_csv(check: bool) -> tuple[int, int, int]:
    files = 0
    cells = 0
    scanned = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "build", "scenario_csv_zh", "*", "*.zh.csv"))):
        scanned += 1
        bom, newline, rows = _load(path)
        touched = 0
        for row in rows:
            for i, cell in enumerate(row):
                if cell in CELL_FIX:
                    row[i] = CELL_FIX[cell]
                    touched += 1
        if touched:
            files += 1
            cells += touched
            if not check:
                _dump(path, bom, newline, rows)
    return scanned, files, cells


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只报告，不写入；有残留返回 2")
    args = ap.parse_args()
    jf, jc = fix_jsonl(args.check, not args.check)
    scanned, cf, cc = fix_csv(args.check)
    print("fix_name_artifacts: jsonl %d cells / %d files; csv %d cells / %d files (scanned %d)"
          % (jc, jf, cc, cf, scanned))
    if args.check and (jc or cc):
        print("FAIL: 仍有脏译名残留")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
