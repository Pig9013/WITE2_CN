# -*- coding: utf-8 -*-
"""把文字版 PDF 抽成逐页文本（JSONL + 纯文本），保留页码以便引用。

用法： python extract_text.py <selection.jsonl> <out_root>
selection.jsonl 每行 {"path": "..."}
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf


def slug(path: Path) -> str:
    s = path.stem
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "_", s)[:80]
    return s.strip("_") or "doc"


def main() -> None:
    sel = Path(sys.argv[1])
    out_root = Path(sys.argv[2])
    out_root.mkdir(parents=True, exist_ok=True)
    items = [json.loads(l) for l in sel.read_text(encoding="utf-8").splitlines() if l.strip()]
    for i, it in enumerate(items, 1):
        p = Path(it["path"])
        if not p.exists():
            print("missing", p, flush=True)
            continue
        dest = out_root / slug(p)
        dest.mkdir(parents=True, exist_ok=True)
        pagef = dest / "pages.jsonl"
        fullf = dest / "full.txt"
        try:
            doc = pymupdf.open(str(p))
        except Exception as e:
            print("open fail", p, e, flush=True)
            continue
        n = doc.page_count
        with pagef.open("w", encoding="utf-8") as pf, fullf.open("w", encoding="utf-8") as ff:
            ff.write(f"# {p}\n# pages={n}\n\n")
            for pi in range(n):
                try:
                    t = doc.load_page(pi).get_text("text") or ""
                except Exception:
                    t = ""
                t = t.replace("\r\n", "\n").strip()
                pf.write(json.dumps({"page": pi + 1, "text": t}, ensure_ascii=False) + "\n")
                ff.write(f"\n### p.{pi+1}\n{t}\n")
        doc.close()
        meta = {"path": str(p), "pages": n, "slug": dest.name, "size": p.stat().st_size}
        (dest / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{i}/{len(items)}] {dest.name} pages={n}", flush=True)


if __name__ == "__main__":
    main()
