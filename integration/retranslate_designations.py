# -*- coding: utf-8 -*-
"""按术语库规则重译部队番号，并写出变更单。

只改 unit / airgroup / aog 三类行；其余文本（百科、事件、UI）不动。
每条变更都记进 audit/designation-changes.tsv，便于逐条核对。
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "glossary"))
import designations as D  # noqa: E402

TRANS = PROJECT / "data" / "scenario_csv" / "translations"
FILES = ["unit.zh.jsonl", "airgroup.zh.jsonl", "aog.zh.jsonl"]


def load_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


def find_game() -> Path:
    env = os.environ.get("WITE2_GAME")
    if env and (Path(env) / "WarInTheEast2.exe").exists():
        return Path(env)
    settings = PROJECT / "mod" / "settings.local.json"
    for name in ("settings.local.json", "settings.json"):
        p = PROJECT / "mod" / name
        if p.exists():
            try:
                gp = json.loads(p.read_text(encoding="utf-8")).get("game_path")
                if gp and (Path(gp) / "WarInTheEast2.exe").exists():
                    return Path(gp)
            except Exception:
                pass
    raise SystemExit("找不到游戏目录；请设置 WITE2_GAME")


def build_ob_map(game: Path) -> dict:
    """name -> 出现次数最多的编制名（OB 的 Name + ' ' + Suffix）。"""
    base = game / "Dat" / "CSV"
    obs = {}
    for scen in sorted(p for p in base.iterdir() if p.is_dir()):
        p = scen / "OBs.csv"
        if not p.exists():
            continue
        rows = list(csv.reader(load_text(p).splitlines(keepends=True)))
        if not rows or "ID" not in rows[0] or "Suffix" not in rows[0]:
            continue
        h = rows[0]
        id_i, nm_i, sf_i = h.index("ID"), h.index("Name"), h.index("Suffix")
        for r in rows[1:]:
            if len(r) <= sf_i:
                continue
            obs[r[id_i]] = (r[nm_i] + " " + r[sf_i]).strip()
    votes = defaultdict(Counter)
    for scen in sorted(p for p in base.iterdir() if p.is_dir()):
        for fn in ("Units.csv", "AirGroups.csv", "AOGs.csv"):
            p = scen / fn
            if not p.exists():
                continue
            rows = list(csv.reader(load_text(p).splitlines(keepends=True)))
            if not rows or "Name" not in rows[0] or "Type" not in rows[0]:
                continue
            h = rows[0]
            ni, ti = h.index("Name"), h.index("Type")
            for r in rows[1:]:
                if len(r) <= max(ni, ti):
                    continue
                ob = obs.get(r[ti])
                if ob:
                    votes[r[ni]][ob] += 1
    return {k: v.most_common(1)[0][0] for k, v in votes.items()}


def main() -> None:
    game = find_game()
    ob_map = build_ob_map(game)
    changes = []
    stats = Counter()

    for fn in FILES:
        path = TRANS / fn
        rows = []
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            rows.append(json.loads(line))
        for row in rows:
            src = (row.get("text") or "").strip()
            old = row.get("translation") or ""
            new = None

            if D.is_fragment(src):
                # 纯序数/数字不能做词典键，否则表格里的数字列会被逐格替换
                if old != src:
                    row["translation"] = src
                    stats["fragment"] += 1
                continue

            new = D.reference_fix(src) or D._sov_air(src) or D._german_hq(src) or D._rvgk(src, ob_map.get(src, ""))
            if new is None and old:
                fixed = D.guards_first(old)
                if fixed != old:
                    new = fixed
                    stats["guards-order"] += 1
            if new and new != old and src:
                changes.append({
                    "file": fn, "source": src, "old": old, "new": new,
                    "rule": "sov-air" if D._sov_air(src) else (
                        "german-hq" if D._german_hq(src) else (
                            "rvgk" if D._rvgk(src, ob_map.get(src, "")) else "guards-order")),
                })
                row["translation"] = new
                stats[changes[-1]["rule"]] += 1

        with path.open("w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    out = PROJECT / "audit" / "designation-changes.tsv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["file", "source", "old", "new", "rule"])
        for c in changes:
            w.writerow([c["file"], c["source"], c["old"], c["new"], c["rule"]])

    print(f"changes: {len(changes)}  {dict(stats)}")
    print(f"log: {out}")


if __name__ == "__main__":
    main()
