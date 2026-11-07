# -*- coding: utf-8 -*-
"""单位名概念词统一（v1.9.10 批次二）：把 jsonl 语料层与场景表的概念词
统一到 glossary/unit_tokens_en_zh.csv 的定译，只改「词」，不改结构。

判据：unit_tokens_en_zh.csv（coastal=滨海、fallschirm=伞兵、replacement=补充、
light=轻装、north=北方、grossdeutschland=大德意志、feldherrnhalle=统帅堂）。
场景 CSV 是玩家可见层，jsonl 只进词典；两层都要改，否则同一英文名两种译法。

用法：
  python integration/fix_unit_terms.py --check   只看差异（有差异 exit 2）
  python integration/fix_unit_terms.py           落地
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
TRANS_DIRS = [PROJECT / "data" / "translations", PROJECT / "data" / "scenario_csv" / "translations"]
CSV_DIR = PROJECT / "build" / "scenario_csv_zh"
SETTINGS = PROJECT / "mod" / "settings.local.json"


# ---- 规则：(名称, 触发键正则, 值变换) -------------------------------------
def _sub(pat, rep, count=0):
    return lambda v: re.sub(pat, rep, v, count=count)


def _if(cond, fn):
    return lambda v: fn(v) if cond(v) else v


RULES = []


def rule(name, key_re, fn):
    RULES.append((name, re.compile(key_re), fn))


rule("coastal", r"Coastal( Fortress)?$|Coastal (Army|Group)$", _sub("海岸", "滨海"))
rule("fortress-num", r"Fortress", _sub(r"(\d+)号要塞", r"第\1要塞"))
rule("fortress-num2", r"Fortress", _sub(r"^(\d+)(?=要塞)", r"第\1"))
rule("fortress-inf", r"Fortress", _sub(r"^(\d+)步兵师（要塞）$", r"第\1要塞"))
rule("fortress-bare", r"Fortress", _sub(r"^(\d+)步兵师$", r"第\1要塞师"))
rule("fallschirm", r"Fallschirm", _sub("空降", "伞兵"))
rule("fallschirm-roman", r"^I Fallschirm$", _sub(r"^I 伞兵$", "第1伞兵"))
rule("fallschirm-roman2", r"^II Fallschirm$", _sub(r"^第二伞兵师$", "第2伞兵师"))
rule("feldherrnhalle", r"Feldherrnhalle", _sub("猎兵师", "统帅堂师"))
rule("feldherrnhalle2", r"Feldherrnhalle", _sub("斐迪南大厅", "统帅堂"))
rule("feldherrnhalle3", r"Feldherrnhalle", _sub("元首大厅", "统帅堂"))
rule("grossdeutschland", r"Grossdeutschland", _sub("大日耳曼", "大德意志"))
rule("grossdeutschland-slash", r"Grossdeutschland", _sub("/", "／"))
rule("caucasus", r"North Caucasus", _sub(r"(?<!北方)(?<!北)高加索", "北方高加索"))
rule("light-mountain", r"Light Mountain", _sub("轻型山地", "轻装山地"))
rule("replacement", r"Replacement", _sub("后备", "补充"))
rule("replacement-1st", r"Replacement", _sub(r"^第一次补充征兵$", "第1补充"))
rule("replacement-2nd", r"Replacement", _sub(r"^第二次补充部队$", "第2补充部队"))
rule("sturm-mot", r"Sturm Mot\.", _sub("摩托化步兵", "摩托化"))
rule("sturm-mot-add", r"Sturm Mot\.", _sub(r"^第(\d+)摩托化", r"第\1突击摩托化"))
rule("croat", r"Croat", _sub(r"^第(\d+)步兵师（克罗地亚）$", r"克罗地亚第\1师"))
rule("russian", r"Russian", _sub("步兵师", "俄罗斯师"))
rule("guards-order", r"Guards|Gds", _sub(r"^(\d+)近卫", r"近卫第\1"))
rule("mot-prefix", r"^(\d+) Mot\.$", _sub(r"^(\d+)摩托化", r"第\1摩托化"))
for _fam in (r"Fortress$", r"Russian$", r"Guards$|Gds$", r"Coastal( Fortress)?$",
             r"Replacement$", r"Mot\.$", r"Croat\.?$", r"Feldherrnhalle$"):
    rule("num-prefix:" + _fam, _fam, _sub(r"^(\d+)(?=[\u4e00-\u9fff])", r"第\1"))

# 单条硬伤：机器翻译残留 / 把编号当年份 / 英文没翻
EXACT = {
    "502nd Fortress": "第502要塞",
    "41 Naval": "第41海军部队",
    "42 Naval": "第42海军部队",
    "156th Reserve": "第156预备部队",
    "27th 'Sekler'": "第27塞凯伊",
    "627th Volga": "第627伏尔加",
    "826th Volga": "第826伏尔加",
    "Grossdeutschland": "大德意志",
    "41 Spanish": "西班牙第41",
    "42 Western": "第42西方",
    "43 Panzergrenadier": "第43装甲掷弹兵",
    "44 Mot.": "第44摩托化旅",
    "1st Light": "第1轻装",
    "533rd Coastal": "第533滨海部队",
}


NAME_COLUMNS = {"name", "newname", "shortname", "new name"}


def is_name(text: str) -> bool:
    """只改「单位名」，绝不动战史正文（正文里 North Caucasus / Russian 是地名、族裔）。"""
    if not text or len(text) > 48:
        return False
    return not re.search(r"[.;:!?]\s", text) and text.count(" ") <= 6


def fix(text: str, value: str) -> str:
    if text in EXACT:
        return EXACT[text]
    if not is_name(text):
        return value
    out = value
    for _name, rx, fn in RULES:
        if rx.search(text):
            out = fn(out)
    return out


def read_jsonl(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def write_jsonl(p: Path, rows) -> None:
    p.write_text("\n".join(json.dumps(o, ensure_ascii=False) for o in rows) + "\n",
                 encoding="utf-8", newline="\n")


def load_csv(p: Path, lenient: bool = False):
    raw = p.read_bytes()
    bom = raw[:3] == bytes([239, 187, 191])
    enc = "utf-8-sig" if bom else "utf-8"
    try:
        text = raw.decode(enc)
    except UnicodeDecodeError:
        if not lenient:
            raise
        enc = "latin-1"  # 英文源表只用来对键，ASCII 足够
        text = raw.decode(enc)
    return list(csv.reader(text.splitlines(keepends=True))), enc, ("\r\n" if "\r\n" in text else "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--list", default="0", help="打印前 N 条差异")
    args = ap.parse_args()
    show = int(args.list)

    hits = []
    for d in TRANS_DIRS:
        for p in sorted(list(d.glob("*.zh.jsonl")) + list(d.glob("*.zh.qa.jsonl"))):
            rows = read_jsonl(p)
            n = 0
            for o in rows:
                old = o.get("translation")
                if not isinstance(old, str) or not o.get("text"):
                    continue
                if str(o.get("column", "")).lower() not in NAME_COLUMNS:
                    continue
                if o.get("kind") not in ("unit",):
                    continue
                new = fix(o["text"], old)
                if new != old:
                    n += 1
                    if len(hits) < 4000:
                        hits.append((o["text"], old, new))
                    o["translation"] = new
                    o["qa_status"] = "ok"
            if n and not args.check:
                write_jsonl(p, rows)

    csv_hits = 0
    game = json.loads(SETTINGS.read_text(encoding="utf-8"))["game_path"]
    base = Path(game) / "Dat" / "CSV"
    for zh in sorted(CSV_DIR.glob("*/*.zh.csv")):
        src = base / zh.parent.name / (zh.name[:-7] + ".csv")
        if not src.exists():
            continue
        srows, _, _ = load_csv(src, lenient=True)
        zrows, enc, nl = load_csv(zh)
        if len(srows) != len(zrows):
            continue
        n = 0
        cols = {i for i, h in enumerate(srows[0]) if h.strip().lower() in NAME_COLUMNS} if srows else set()
        for s, z in zip(srows, zrows):
            for i, cell in enumerate(s):
                if i not in cols or i >= len(z) or not z[i]:
                    continue
                new = fix(cell, z[i])
                if new != z[i]:
                    z[i] = new
                    n += 1
        if n:
            csv_hits += n
            if not args.check:
                with zh.open("w", encoding=enc, newline="") as f:
                    csv.writer(f, lineterminator=nl).writerows(zrows)

    print("fix_unit_terms: jsonl %d cells; csv %d cells" % (len(hits), csv_hits))
    for t, o, n in hits[:show]:
        print("  %-38r %s -> %s" % (t, o, n))
    if args.check:
        return 0 if not hits and not csv_hits else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
