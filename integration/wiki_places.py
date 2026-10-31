# -*- coding: utf-8 -*-
"""用维基百科跨语言链接给地名找回标准中文名。

en.wikipedia 的 langlinks 给出中文标题（多为繁体），用 OpenCC 转简体后与我们的译名比对。
输出 audit/place-wikipedia.tsv（不一致项），供人工确认后写进 reference_overrides。
"""
from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import opencc

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "audit" / "place-wikipedia.tsv"
PROXY = "http://127.0.0.1:7897"
API = "https://en.wikipedia.org/w/api.php"
CC = opencc.OpenCC("t2s")

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
opener.addheaders = [("User-Agent", "WitE2CN/1.0 (place-name check)")]


def fetch(titles):
    q = urllib.parse.urlencode({
        "action": "query", "titles": "|".join(titles), "prop": "langlinks",
        "lllang": "zh", "format": "json", "redirects": "1",
    })
    with opener.open(API + "?" + q, timeout=40) as r:
        data = json.loads(r.read().decode("utf-8"))
    pages = data.get("query", {}).get("pages", {})
    res = {}
    for p in pages.values():
        ll = p.get("langlinks") or []
        if ll:
            res[p["title"]] = ll[0]["*"]
    return res


def main() -> None:
    rows = []
    for line in (PROJECT / "data" / "scenario_csv" / "translations" / "place.zh.jsonl").read_text(
            encoding="utf-8-sig").splitlines():
        if line.strip():
            r = json.loads(line)
            t = (r.get("text") or "").strip()
            if t:
                rows.append((t, (r.get("translation") or "").strip()))
    names = [t for t, _ in rows]
    print("places:", len(names))

    cache_p = PROJECT / "audit" / "place-wiki-cache.json"
    got = {}
    if cache_p.exists():
        got = json.loads(cache_p.read_text(encoding="utf-8"))
    B = 50
    for i in range(0, len(names), B):
        batch = [n for n in names[i:i + B] if len(n) < 80 and "  " not in n and n not in got]
        if not batch:
            continue
        for attempt in range(4):
            try:
                got.update(fetch(batch))
                break
            except Exception as e:
                time.sleep(3 * (attempt + 1))
        time.sleep(0.9)
        if i % 200 == 0:
            cache_p.write_text(json.dumps(got, ensure_ascii=False), encoding="utf-8")
            print("  ...", i, "done", len(got), flush=True)
    cache_p.write_text(json.dumps(got, ensure_ascii=False), encoding="utf-8")

    out = []
    for t, ours in rows:
        zh = got.get(t)
        if not zh:
            continue
        zh = CC.convert(zh)
        zh = zh.split(" (")[0].strip()
        if not zh or not ours:
            continue
        if zh == ours:
            continue
        out.append((t, ours, zh))

    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["english", "ours", "wikipedia_zh"])
        w.writerows(out)
    print("wikipedia matched:", len(got), " mismatched:", len(out))


if __name__ == "__main__":
    main()
