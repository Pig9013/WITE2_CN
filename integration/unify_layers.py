# -*- coding: utf-8 -*-
"""分层统一：一个键一条译文，同时写入 jsonl / 场景 CSV / 覆盖层，避免「只改一层，游戏里没变」。

分层现实（2026-11-06）：
  data/**/translations/*.zh.jsonl      － 语料层（equipment / unit / place / event / hotkey / ui ...）
  build/scenario_csv_zh/**/*.zh.csv    － 场景表（14 个剧本的单元格）
  glossary/reference_overrides.json    － 定译层（terms < places < ui）→ build_master_overrides.py
  glossary/manual_translations.json    － 人工层
  glossary/master_overrides.json       － 生成物：最后套用，压掉下面所有层

动作：
  set             把 value 同时写进 jsonl（含 .qa）、场景 CSV、reference_overrides（缺则加进 ui 组）、manual
  revert          译文回退成英文原文（等于从词典拿掉），并删掉覆盖层里的旧译
  drop_override   只删覆盖层（下层 jsonl 已经是对的，覆盖层在压它）
  adopt_override  把覆盖层现有译文写回 jsonl / CSV（覆盖层内容更完整时用）

pattern 规则按正则展开（热键这类几百条大小写/组合键变体不逐条手写）。
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
GLOSS = PROJECT / "glossary"
UNIFY = GLOSS / "layer_unify.json"
REF = GLOSS / "reference_overrides.json"
MAN = GLOSS / "manual_translations.json"
JSONL_DIRS = [PROJECT / "data" / "translations", PROJECT / "data" / "scenario_csv" / "translations"]
CSV_DIR = PROJECT / "build" / "scenario_csv_zh"
GROUPS = ("terms", "places", "ui")


def read_jsonl(p: Path):
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(p: Path, rows) -> None:
    p.write_text("\n".join(json.dumps(o, ensure_ascii=False) for o in rows) + "\n",
                 encoding="utf-8", newline="\n")


def load_csv(p: Path):
    raw = p.read_bytes()
    bom = raw[:3] == bytes([239, 187, 191])
    enc = "utf-8-sig" if bom else "utf-8"
    try:
        text = raw.decode(enc)
    except UnicodeDecodeError:
        enc = "cp1252"
        text = raw.decode(enc)
    return list(csv.reader(text.splitlines(keepends=True))), enc


def resolve(rules, ref, man) -> dict:
    out = {}
    for e in rules.get("entries", []):
        action = e.get("action", "set")
        value = e["key"] if action == "revert" else e.get("value")
        out[e["key"]] = [action, value, e.get("note", "")]
    pats = rules.get("patterns") or []
    if pats:
        pool = set()
        for d in JSONL_DIRS:
            for p in list(d.glob("*.zh.jsonl")) + list(d.glob("*.zh.qa.jsonl")):
                pool.update(o["text"] for o in read_jsonl(p) if "text" in o)
        for g in GROUPS:
            pool.update((ref.get(g) or {}).keys())
        pool.update(man.keys())
        for r in pats:
            rx = re.compile(r["regex"], re.I if "i" in r.get("flags", "").lower() else 0)
            for key in pool:
                if key in out:
                    continue
                m = rx.match(key)
                if not m:
                    continue
                value = re.sub(r"\{(\d)\}", lambda x, m=m: m.group(int(x.group(1))) or "", r["value"])
                value = value.replace("{key}", key)
                out[key] = ["set", value, r.get("note", "")]
    # adopt_override：取覆盖层现值当目标
    for key, item in out.items():
        if item[0] != "adopt_override":
            continue
        cur = None
        for g in GROUPS:
            if key in (ref.get(g) or {}):
                cur = ref[g][key][0]
        if cur is None:
            cur = man.get(key)
        if cur is None:
            item[0] = "skip"
            item[1] = None
            print("  ! adopt_override 无覆盖层来源：", repr(key))
        else:
            item[0] = "set"
            item[1] = cur
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    ref = json.loads(REF.read_text(encoding="utf-8"))
    man = json.loads(MAN.read_text(encoding="utf-8")) if MAN.exists() else {}
    plan = resolve(json.loads(UNIFY.read_text(encoding="utf-8")), ref, man)

    jh, ch, rc, mc = {}, {}, 0, 0
    jsonl_keys = set()
    # 1) jsonl
    for d in JSONL_DIRS:
        for p in sorted(list(d.glob("*.zh.jsonl")) + list(d.glob("*.zh.qa.jsonl"))):
            rows = read_jsonl(p)
            n = 0
            for o in rows:
                jsonl_keys.add(o.get("text"))
                hit = plan.get(o.get("text"))
                if not hit or hit[0] not in ("set", "revert"):
                    continue
                if o.get("translation") != hit[1]:
                    o["translation"] = hit[1]
                    o["qa_status"] = "ok"
                    n += 1
            if n:
                jh[p] = n
                if not args.check:
                    write_jsonl(p, rows)
    # 2) 覆盖层 / 人工层
    for key, (action, value, note) in plan.items():
        present = [g for g in GROUPS if key in (ref.get(g) or {})]
        if action in ("set", "revert"):
            if present:
                for g in present:
                    if ref[g][key][0] != value:
                        ref[g][key][0] = value
                        rc += 1
            elif key not in man and key not in jsonl_keys:
                # 只给「下层根本没有」的键补覆盖层，避免把已有语料再抄一份进覆盖层（那正是分层的病根）
                ref.setdefault("ui", {})[key] = [value, "分层统一（unify_layers.py）"]
                rc += 1
        elif action == "drop_override":
            for g in present:
                del ref[g][key]
                rc += 1
        if key in man:
            if action in ("set", "revert"):
                if man[key] != value:
                    man[key] = value
                    mc += 1
            elif action == "drop_override":
                del man[key]
                mc += 1
    # 3) 场景 CSV
    game = json.loads((PROJECT / "mod" / "settings.local.json").read_text(encoding="utf-8"))["game_path"]
    base = Path(game) / "Dat" / "CSV"
    for zh in sorted(CSV_DIR.glob("*/*.zh.csv")):
        src = base / zh.parent.name / (zh.name[:-7] + ".csv")
        if not src.exists():
            continue
        srows, _ = load_csv(src)
        zrows, enc = load_csv(zh)
        if len(srows) != len(zrows) or len(srows[0]) != len(zrows[0]):
            continue
        n = 0
        for s, z in zip(srows, zrows):
            for i, cell in enumerate(s):
                hit = plan.get(cell)
                if not hit or hit[0] not in ("set", "revert") or i >= len(z):
                    continue
                if z[i] != hit[1]:
                    z[i] = hit[1]
                    n += 1
        if n:
            ch[zh.name] = n
            if not args.check:
                with zh.open("w", encoding=enc, newline="") as f:
                    csv.writer(f).writerows(zrows)

    j = sum(jh.values()); c = sum(ch.values())
    if args.check:
        ok = j == 0 and c == 0 and rc == 0 and mc == 0
        print("layer unify check: jsonl %d, csv %d, ref %d, manual %d%s"
              % (j, c, rc, mc, "" if ok else "  <-- DRIFT"))
        return 0 if ok else 2
    if rc:
        REF.write_text(json.dumps(ref, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    if mc:
        MAN.write_text(json.dumps(man, ensure_ascii=False, indent=0), encoding="utf-8")
    print("layer unify: keys %d; jsonl cells %d (%d files); csv cells %d (%d files); ref %d; manual %d"
          % (len(plan), j, len(jh), c, len(ch), rc, mc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
