# -*- coding: utf-8 -*-
"""用 GeoNames 反查我们的地名译名：英文名 → 候选地点 → 中文名对照。

数据：
  gazetteer/cities500.txt        人口>=500 的城镇（含经纬度、国家、别名）
  gazetteer/alternateNamesV2.txt 各语言别名（用 isolanguage=zh 取中文名）
输出：audit/place-gazetteer.tsv，列出「我们的译名」与「GeoNames 中文名」不一致的条目。
"""
from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
GZ = Path(r"D:\Tool\WITE2\gazetteer")
CITY = GZ / "cities500.txt"
ALT = GZ / "alternateNamesV2.txt"
OUT = PROJECT / "audit" / "place-gazetteer.tsv"
STATS = PROJECT / "audit" / "place-gazetteer-stats.txt"


def load_cities():
    idx = defaultdict(list)
    with CITY.open(encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if len(row) < 9:
                continue
            gid, name, asciiname, alt, lat, lon, fclass, fcode, cc = row[:9]
            idx[name.lower()].append((gid, name, float(lat), float(lon), cc))
    return idx


def load_zh():
    zh = defaultdict(list)
    if not ALT.exists():
        return zh
    with ALT.open(encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if len(row) < 4:
                continue
            gid, lang, name = row[0], row[2], row[3]
            if lang in ("zh", "zh-CN", "zh-Hans", "zh_Hans"):
                zh[gid].append(name)
    return zh


def main() -> None:
    import sys
    sys.path.insert(0, str(PROJECT / "integration"))
    from fix_scenario_names import find_game, load_rows

    # 我们的译名
    ours = {}
    for line in (PROJECT / "data" / "scenario_csv" / "translations" / "place.zh.jsonl").read_text(
            encoding="utf-8-sig").splitlines():
        if line.strip():
            r = json.loads(line)
            t = (r.get("text") or "").strip()
            if t:
                ours[t] = (r.get("translation") or "").strip()

    # 坐标
    game = find_game()
    rows, _ = load_rows(Path(game) / "Dat" / "CSV" / "1941 Campaign" / "Locations.csv")
    h = rows[0]
    ni, xi, yi = h.index("Name"), h.index("X"), h.index("Y")
    locs = {}
    for r in rows[1:]:
        if len(r) <= max(ni, xi, yi):
            continue
        try:
            locs[r[ni].strip()] = (int(r[xi]), int(r[yi]))
        except ValueError:
            pass

    idx = load_cities()
    zh = load_zh()
    anchors = []   # 唯一匹配、且 GeoNames 有中文名的点，用来给同名前两义做国家投票
    for name, (x, y) in locs.items():
        c = idx.get(name.lower(), [])
        if len(c) == 1 and zh.get(c[0][0]):
            anchors.append((x, y, c[0][4]))
    print("anchors:", len(anchors))

    rows_out = []
    stat = Counter()
    for name, our_zh in ours.items():
        c = idx.get(name.lower(), [])
        if not c:
            stat["未匹配"] += 1
            continue
        cand = c
        if len(c) > 1:
            xy = locs.get(name)
            if xy and anchors:
                near = sorted(anchors, key=lambda a: (a[0]-xy[0])**2 + (a[1]-xy[1])**2)[:8]
                cc = Counter(a[2] for a in near).most_common(1)[0][0]
                filtered = [x for x in c if x[4] == cc]
                if filtered:
                    cand = filtered
                    stat["多义按邻近国家消歧"] += 1
            if len(cand) > 1:
                stat["多义未消歧"] += 1
        gid, gname, lat, lon, cc = cand[0]
        zs = zh.get(gid) or []
        if not zs:
            stat["匹配但无中文名"] += 1
            continue
        gz = zs[0]
        if not our_zh:
            stat["我方无译文"] += 1
            continue
        if gz == our_zh or gz in our_zh or our_zh in gz:
            stat["一致"] += 1
        else:
            stat["不一致"] += 1
            rows_out.append((name, our_zh, gz, cc, lat, lon, gid))
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["english", "ours", "geonames_zh", "country", "lat", "lon", "gid"])
        w.writerows(rows_out)
    STATS.write_text("\n".join(f"{v}\t{k}" for k, v in stat.most_common()), encoding="utf-8")
    print(dict(stat))


if __name__ == "__main__":
    main()
