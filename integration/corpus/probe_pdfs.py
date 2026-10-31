# -*- coding: utf-8 -*-
"""扫描书库里的 PDF：判断是文字版还是扫描件，并记录语言/关键词特征。

输出 JSONL：每行一个 PDF 的探测结果。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf

ROOTS = [r"D:\书", r"D:\兵棋"]
OUT = Path(r"D:\Tool\WITE2\_work\pdf_probe2.jsonl")

CJK = re.compile(r"[\u4e00-\u9fff]")
CYR = re.compile(r"[\u0400-\u04ff]")
LAT = re.compile(r"[A-Za-z]")
KW = ["order of battle", "division", "corps", "army group", "panzer", "infantry", "rifle",
      "guards", "corps", "soviet", "russ", "german", "wehrmacht", "heeres", "luftwaffe",
      "дивизи", "корпус", "полк", "армия", "гвард", "пво", "иак",
      "师", "军", "集团军", "方面军", "步兵", "坦克", "航空", "近卫", "编制", "番号"]


def probe(path: Path) -> dict:
    rec = {"path": str(path), "size": path.stat().st_size}
    try:
        doc = pymupdf.open(str(path))
    except Exception as e:
        rec["error"] = str(e)[:120]
        return rec
    try:
        n = doc.page_count
        rec["pages"] = n
        if n == 0:
            rec["error"] = "no pages"
            return rec
        idx = sorted({0, 1, 2, n // 2, max(0, n - 2), n - 1})
        idx = [i for i in idx if 0 <= i < n]
        text = ""
        for i in idx:
            try:
                text += doc.load_page(i).get_text("text") or ""
            except Exception:
                pass
        rec["sample_chars"] = len(text)
        rec["chars_per_page"] = round(len(text) / max(1, len(idx)))
        full = text[:20000]
        rec["cjk"] = len(CJK.findall(full))
        rec["cyr"] = len(CYR.findall(full))
        rec["lat"] = len(LAT.findall(full))
        low = full.lower()
        rec["kw"] = [k for k in KW if k.lower() in low]
        rec["head"] = re.sub(r"\s+", " ", full[:200])
        rec["images"] = sum(1 for i in idx if doc.load_page(i).get_images())
        return rec
    finally:
        try:
            doc.close()
        except Exception:
            pass


def main() -> None:
    files = []
    for root in ROOTS:
        for p in Path(root).rglob("*.pdf"):
            files.append(p)
    files.sort()
    print(f"probing {len(files)} pdfs", flush=True)
    with OUT.open("w", encoding="utf-8") as f:
        for i, p in enumerate(files, 1):
            rec = probe(p)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if i % 100 == 0:
                print(f"  {i}/{len(files)}", flush=True)
    print("done")


if __name__ == "__main__":
    main()
