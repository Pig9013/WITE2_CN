# -*- coding: utf-8 -*-
"""把三路文献清单合并成 docs/文献参考目录.md（GB/T 7714-2015 著录）。"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
LIB = Path(r"D:\Tool\WITE2\文献库")
MANI = LIB / "_manifest"
OUT = PROJECT / "docs" / "文献参考目录.md"

STREAMS = [
    ("01_soviet.json", "一、苏联红军编制、番号与空军/国土防空"),
    ("02_german.json", "二、德国国防军与武装党卫军编制、番号与缩写"),
    ("03_chinese.json", "三、中文文献与工具书"),
]


def load(name):
    p = MANI / name
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return []
    if isinstance(data, dict):
        data = data.get("items", [])
    return data if isinstance(data, list) else []


def main():
    lines = []
    lines.append("# 二战苏德编制参考书目（GB/T 7714-2015）\n")
    lines.append("> 用途：WitE2 简中汉化里**部队番号与缩写**的译名依据。")
    lines.append("> 每条给出规范著录；能公开下载的附本地路径，不能下载的附链接，供自行获取。")
    lines.append("> 本地文件存放在 mod 仓库之外的 文献库 目录，不随仓库分发。\n")

    downloaded, failed = [], []
    for fn, title in STREAMS:
        items = load(fn)
        lines.append(f"## {title}\n")
        if not items:
            lines.append("_（该路清单尚未生成）_\n")
            continue
        lines.append("| # | 著录 | 中文题名 | 状态 | 位置 / 链接 |")
        lines.append("|---|---|---|---|---|")
        for i, it in enumerate(items, 1):
            cite = (it.get("gbt7714") or "").replace("|", "/").strip() or (it.get("title") or "")
            zh = (it.get("title_zh") or "").replace("|", "/")
            status = it.get("status", "")
            if status == "downloaded":
                loc = it.get("local_path", "")
                downloaded.append((cite, loc, it.get("bytes")))
                mark = "已下载"
            else:
                loc = it.get("pdf_url") or it.get("landing_url") or ""
                failed.append((cite, loc, it.get("fail_reason", "")))
                mark = "需自行下载"
            lines.append(f"| {i} | {cite} | {zh} | {mark} | {loc} |")
        lines.append("")

    lines.append("## 下载失败的条目（链接目录）\n")
    if failed:
        for i, (cite, url, why) in enumerate(failed, 1):
            lines.append(f"{i}. {cite}")
            lines.append(f"   - 链接：{url}")
            if why:
                lines.append(f"   - 原因：{why}")
    else:
        lines.append("_暂无_")
    lines.append("")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name} downloaded={len(downloaded)} failed={len(failed)}")


if __name__ == "__main__":
    main()
