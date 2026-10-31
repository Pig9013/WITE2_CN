# -*- coding: utf-8 -*-
"""把 docs 下的对照表导出成 XLSX（按文档里的小节分 sheet），便于作为发布附件。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

PROJECT = Path(__file__).resolve().parent.parent
DOCS = PROJECT / "docs"


def parse(path: Path):
    """返回 [(小节标题, [表头, 行...]), ...]"""
    lines = path.read_text(encoding="utf-8").splitlines()
    section, tables, cur, header = "", [], [], None
    for ln in lines:
        if ln.startswith("## "):
            if cur:
                tables.append((section, cur))
                cur = []
            section = ln[3:].strip()
        if ln.startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                continue
            if header is None:
                header = cells
            cur.append(cells)
    if cur:
        tables.append((section, cur))
    return tables


def export(md: Path, out: Path) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    head_fill = PatternFill("solid", fgColor="1F4E79")
    head_font = Font(color="FFFFFF", bold=True)
    for i, (section, rows) in enumerate(parse(md)):
        title = re.sub(r"[\\/:*?\[\]]", "", section)[:28] or "Sheet%d" % (i + 1)
        ws = wb.create_sheet(title=title[:31])
        for r, row in enumerate(rows, start=1):
            for c, val in enumerate(row, start=1):
                cell = ws.cell(row=r, column=c, value=val)
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                if r == 1:
                    cell.fill = head_fill
                    cell.font = head_font
            if r == 1:
                ws.freeze_panes = "A2"
        for c in range(1, len(rows[0]) + 1):
            width = max(len(str(row[c - 1])) if c - 1 < len(row) else 0 for row in rows[:80])
            ws.column_dimensions[get_column_letter(c)].width = min(60, max(10, width * 1.6))
    wb.save(out)
    print("wrote", out.name, "sheets", len(wb.sheetnames))


def main() -> None:
    for name in ("术语与番号总表", "权威对照表"):
        md = DOCS / (name + ".md")
        if md.exists():
            export(md, DOCS / (name + ".xlsx"))


if __name__ == "__main__":
    main()
