# -*- coding: utf-8 -*-
"""扫描版 PDF 走本机 tesseract OCR（chi_sim+eng），逐页输出，保留页码。

页面已有文字层时直接取文字，不重复 OCR。
用法： python ocr_pdf.py <pdf> <out_dir> [dpi] [lang]
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pymupdf

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def slug(path: Path) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "_", path.stem)[:80]
    return s.strip("_") or "doc"


def ocr_page(pdf: pymupdf.Document, idx: int, dpi: int, lang: str) -> str:
    page = pdf.load_page(idx)
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        pix.save(tmp)
        env = dict(os.environ, TESSDATA_PREFIX=r"C:\Program Files\Tesseract-OCR\tessdata")
        r = subprocess.run([TESS, tmp, "stdout", "-l", lang, "--psm", "3"],
                           capture_output=True, encoding="utf-8", errors="replace", env=env, timeout=180)
        return (r.stdout or "").strip()
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def main() -> None:
    pdf_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    lang = sys.argv[4] if len(sys.argv) > 4 else "chi_sim+eng"
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(pdf_path))
    n = doc.page_count
    first, last = 0, n
    if len(sys.argv) > 5 and sys.argv[5] == "--range":
        first = int(sys.argv[6]); last = min(n, int(sys.argv[7]))
    with (out_dir / "pages.jsonl").open("w", encoding="utf-8") as pf, (out_dir / "full.txt").open("w", encoding="utf-8") as ff:
        ff.write(f"# {pdf_path}\n# pages={n} ocr={lang} dpi={dpi}\n\n")
        for pi in range(first, last):
            t = ""
            try:
                t = (doc.load_page(pi).get_text("text") or "").strip()
            except Exception:
                t = ""
            src = "text"
            if len(t) < 40:
                try:
                    t = ocr_page(doc, pi, dpi, lang)
                except Exception as e:
                    t = ""
                src = "ocr"
            pf.write(json.dumps({"page": pi + 1, "text": t, "src": src}, ensure_ascii=False) + "\n")
            ff.write(f"\n### p.{pi+1} [{src}]\n{t}\n")
            if (pi + 1) % 10 == 0:
                print(f"  page {pi+1}/{last}", flush=True)
    doc.close()
    (out_dir / "meta.json").write_text(json.dumps({"path": str(pdf_path), "pages": n, "dpi": dpi,
                                                   "lang": lang, "slug": out_dir.name},
                                                  ensure_ascii=False, indent=1), encoding="utf-8")
    print("done", out_dir)


if __name__ == "__main__":
    main()
