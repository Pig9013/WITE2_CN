# -*- coding: utf-8 -*-
r"""地面部队「N/M」分队名重算（第56师第1团 / 第1/8）。

背景（v1.9.20）：
    Units.csv 的 Name 列有一批「分队名」写法，如 1/56th、I/13th。旧翻译把它
    按字面拼成「第1/第56」，两个「第」叠在一起、编制语义全丢；更糟的是
    glossary/unit_name_canon.csv 里有 7 条按「场景表多数值」定出来的
    csv-majority 条目，把英军坦克旅、德军空军高炮营的分队名定成了
    「第33党卫军（法国）第1营」这类完全不相关的党卫军营。

口径（由 WarInTheEast2 的显示机制决定）：
    引擎把单位名拼成「译(Units.Name) + 空格 + 译(OBs.Suffix)」（师徽文件名
    //Sym//GE//1st 装甲师.tga 是硬证据，mod/build_crest_map.py 也按此生成），
    所以 Name 只能译成「片段」，兵种词由后缀补。

    规则（按该键在所有剧本里实际配过的 OB 后缀判定）：
      1) 全部后缀都含 Division（1/56th 只配过 Infantry Division 等）：
         1/56th -> 第56师第1团，分队是师属团级，语义确定。
      2) 其余（同一键跨师/旅/团/营/连，如 1/8th 配过 6 种后缀）：
         1/8th  -> 第1/8，不揣测级别，保持与英文同构的分队编号。

    带附属词的分队名（I/3rd Lehr、I/999th Afrika、(158th Res)）同样按编号
    处理，附属词译出后接在编号后面：「第1/3 教导」「第1/16（158预备）」；
    党卫军各师（1/13th SS）、空军番号（2/15 IAP）与装备名整条跳过，保持原译。

    两条既改语料层 data/scenario_csv/translations/unit.zh*.jsonl，也改显示层
    build/scenario_csv_zh/*/Units.zh.csv（按英文源表同一行同一列定位，只碰
    Name 列）。另删除 unit_name_canon.csv 里对这批键的 csv-majority 误判条目。

用法：
    python integration/fix_unit_slash.py --check   # 只报告，仍有待改则 exit 2
    python integration/fix_unit_slash.py           # 写入
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
JSONL_TARGETS = (
    ROOT / "data" / "scenario_csv" / "translations" / "unit.zh.jsonl",
    ROOT / "data" / "scenario_csv" / "translations" / "unit.zh.qa.jsonl",
)
CANON = ROOT / "glossary" / "unit_name_canon.csv"
ZH_DIR = ROOT / "build" / "scenario_csv_zh"
SLASH = re.compile(r"^(\d+|[IVXLCDM]+)/(\d+)(?:st|nd|rd|th)?(?:\s+(.+))?$")
ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

# 分队名尾部的附属词（I/3rd Lehr 的 Lehr、I/999th Afrika 的 Afrika）。它们属于
# 父编制名，英文里不能省，中文里同样保留，只是放到「第1/3」后面。
# 值为 False 的键整条跳过：党卫军各师（SS/SS Est./SS Fr.）目前译作
# 「第13党卫军第2营」，语义已正确，按「第2/13 党卫军」重写反而更差；
# 空军番号（IAP 等）与装备、年份组合不是地面分队，一律不碰。
DESCRIPTORS = {
    "Fallschirm": "伞兵",
    "Lehr": "教导",
    "Guards": "近卫",
    "Gds": "近卫",
    "Afrika": "非洲",
    "African": "非洲",
    "Mot.": "摩托化",
    "Volks": "国民",
    "Ost": "东方",
    "zbV": "特设",
    "Fortress": "要塞",
    "Position": "阵地",
    "Mountain": "山地",
    "Naval": "海军",
    "LW": "空军",
    "Reserve": "预备",
    "Sturm": "突击",
    "Tabor Goums": "摩洛哥土著",
    "Senegal": "塞内加尔",
    "Cuneense": "库内奥",
    "Cosseria": "科塞里亚",
    "'Blue'": "蓝色",
}
SKIP_DESC = {
    "SS", "SS Est.", "SS Fr.",
    "IAP", "BAP", "BBAP", "IAP-KBF", "IAP PVO", "IAP-ChF",
    "USG Drop Tank", "Very Cold Winter",
}
RES_PAREN = re.compile(r"^\((\d+)(?:st|nd|rd|th)\s+Res\)$")
STURM_PAREN = re.compile(r"^Sturm \((.+)\)$")
ROMAN_PAIR = re.compile(r"^(\d+|[IVX]+)/(\d+)(?:st|nd|rd|th)?$")
ORDINAL = re.compile(r"^(\d+)(?:st|nd|rd|th)$")


def roman_to_int(s):
    s = s.upper()
    if s.isdigit():
        return int(s)
    total = prev = 0
    for ch in reversed(s):
        v = ROMAN.get(ch)
        if not v:
            return None
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def game_dir():
    env = os.environ.get("WITE2_GAME")
    cands = [Path(env)] if env else []
    for name in ("settings.local.json", "settings.json"):
        p = ROOT / "mod" / name
        if p.exists():
            try:
                v = json.loads(p.read_text(encoding="utf-8")).get("game_path")
                if v:
                    cands.append(Path(v))
            except Exception:
                pass
    for c in cands:
        if (c / "Dat" / "CSV").exists():
            return c
    raise SystemExit("找不到游戏目录：设置 WITE2_GAME 或在 mod/settings.local.json 填 game_path")


def load_csv(path):
    raw = path.read_bytes()
    if raw.startswith(BOM):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
    return list(csv.reader(io.StringIO(text, newline="")))


def suffix_map(csv_root):
    """分队名 -> 该键在全部剧本里配过的 OB 后缀计数。"""
    seen = collections.defaultdict(collections.Counter)
    for d in sorted(csv_root.iterdir()):
        units, obs = d / "Units.csv", d / "OBs.csv"
        if not (units.exists() and obs.exists()):
            continue
        orows = load_csv(obs)
        if not orows or "Name" not in orows[0] or "Suffix" not in orows[0]:
            continue
        i_name, i_suf = orows[0].index("Name"), orows[0].index("Suffix")
        table = {}
        for r in orows[1:]:
            if len(r) > max(i_name, i_suf):
                table[r[0].strip()] = r[i_suf].strip()
        urows = load_csv(units)
        if not urows or "Name" not in urows[0] or "Type" not in urows[0]:
            continue
        i_u, i_t = urows[0].index("Name"), urows[0].index("Type")
        for r in urows[1:]:
            if len(r) <= max(i_u, i_t):
                continue
            name = r[i_u].strip()
            if not SLASH.match(name):
                continue
            suf = table.get(r[i_t].strip(), "")
            if suf:
                seen[name][suf] += 1
    return {k: dict(v) for k, v in seen.items()}


def desc_zh(desc):
    """附属词中文；返回 False 表示整条键跳过，返回原文表示照抄。"""
    desc = desc.strip()
    if desc in SKIP_DESC:
        return False
    if desc in DESCRIPTORS:
        return DESCRIPTORS[desc]
    m = RES_PAREN.match(desc)
    if m:
        return "（%d预备）" % int(m.group(1))
    if desc == "(Res)":
        return "（预备）"
    m = STURM_PAREN.match(desc)
    if m:
        inner = m.group(1)
        pair = ROMAN_PAIR.match(inner)
        if pair:
            l, r = roman_to_int(pair.group(1)), int(pair.group(2))
            if l is not None:
                return "突击（%d/%d）" % (l, r)
        ordi = ORDINAL.match(inner)
        if ordi:
            return "突击（%d）" % int(ordi.group(1))
        return "突击（%s）" % inner
    return desc


def decide(key, suffixes):
    m = SLASH.match(key)
    left = roman_to_int(m.group(1))
    right = int(m.group(2))
    if left is None:
        return None
    dz = ""
    if m.group(3):
        dz = desc_zh(m.group(3))
        if dz is False:
            return None
    # 只有 1/2/3 号分队能确定是「师属团」（师一般辖三个团）；
    # 5/5th、6/42nd 这类英军空降师的分队实际是旅/营，硬套「师第团」会出错。
    # 括号里是父编制编号（1/16th (158th Res)）时不能套「第N师第M团」，
    # 否则会把 16 当成师号、又塞进 158，拼出「第16（158预备）师第1团」。
    if 1 <= left <= 3 and not dz.startswith("（") and suffixes and all(
        "Division" in s for s in suffixes
    ):
        return "第%d%s师第%d团" % (right, dz, left)
    base = "第%d/%d" % (left, right)
    if not dz:
        return base
    return base + (dz if dz.startswith("（") else " " + dz)


def build_table():
    smap = suffix_map(game_dir() / "Dat" / "CSV")
    keys = []
    for line in JSONL_TARGETS[0].read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        text = (json.loads(line).get("text") or "").strip()
        if SLASH.match(text):
            keys.append(text)
    table, unknown = {}, []
    for k in sorted(set(keys)):
        v = decide(k, smap.get(k) or {})
        if v is None:
            unknown.append(k)
        else:
            table[k] = v
    return table, smap, unknown


def fix_jsonl(table, check):
    files = cells = 0
    for path in JSONL_TARGETS:
        if not path.exists():
            continue
        out, touched = [], 0
        for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
            s = line.strip()
            if not s:
                out.append(line)
                continue
            rec = json.loads(s)
            text = (rec.get("text") or "").strip()
            if text in table and rec.get("translation") != table[text]:
                rec["translation"] = table[text]
                touched += 1
                out.append(json.dumps(rec, ensure_ascii=False) + ("\n" if line.endswith("\n") else ""))
            else:
                out.append(line)
        if touched:
            files += 1
            cells += touched
            old_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            if len(old_lines) != len(out):
                raise SystemExit("行数变化，拒写：%s" % path)
            changed = sum(1 for a, b in zip(old_lines, out) if a != b)
            if changed != touched:
                raise SystemExit("改动行数不符（%d != %d），拒写：%s" % (changed, touched, path))
            if not check:
                path.write_text("".join(out), encoding="utf-8", newline="")
    return files, cells


def _load_zh(path):
    raw = path.read_bytes()
    bom = BOM if raw.startswith(BOM) else b""
    body = raw[len(bom):]
    newline = "\r\n" if b"\r\n" in body[:4000] else "\n"
    rows = list(csv.reader(io.StringIO(body.decode("utf-8"), newline="")))
    return bom, newline, rows


def _dump_zh(path, bom, newline, rows):
    buf = io.StringIO(newline="")
    csv.writer(buf, lineterminator=newline).writerows(rows)
    path.write_bytes(bom + buf.getvalue().encode("utf-8"))


def fix_csv(table, check):
    files = cells = 0
    csv_root = game_dir() / "Dat" / "CSV"
    for zh in sorted(ZH_DIR.glob("*/Units.zh.csv")):
        src = csv_root / zh.parent.name / "Units.csv"
        if not src.exists():
            continue
        srows = load_csv(src)
        bom, newline, rows = _load_zh(zh)
        if len(srows) != len(rows) or not rows:
            raise SystemExit("结构不一致：%s" % zh)
        if "Name" not in rows[0]:
            raise SystemExit("找不到 Name 列：%s" % zh)
        col = rows[0].index("Name")
        touched = 0
        for i in range(1, len(rows)):
            s, z = srows[i], rows[i]
            if col >= len(s) or col >= len(z):
                continue
            key = s[col].strip()
            if key in table and z[col] != table[key]:
                z[col] = table[key]
                touched += 1
        if touched:
            files += 1
            cells += touched
            if not check:
                _dump_zh(zh, bom, newline, rows)
                back = _load_zh(zh)
                if back[0] != bom or back[2] != rows:
                    raise SystemExit("写回后往返不一致，拒写：%s" % zh)
    return files, cells


def drop_canon(table, check):
    if not CANON.exists():
        return []
    raw = CANON.read_bytes()
    bom = BOM if raw.startswith(BOM) else b""
    lines = raw[len(bom):].decode("utf-8").splitlines(keepends=True)
    keep, dropped = [lines[0]], []
    for line in lines[1:]:
        en = line.split(",")[0].strip()
        if en in table:
            dropped.append(en)
        else:
            keep.append(line)
    if dropped and not check:
        CANON.write_bytes(bom + "".join(keep).encode("utf-8"))
    return dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    table, smap, unknown = build_table()
    jf, jc = fix_jsonl(table, args.check)
    cf, cc = fix_csv(table, args.check)
    cd = drop_canon(table, args.check)
    div = sum(1 for v in table.values() if v.endswith("团"))
    print("slash keys: %d (division-level %d / numbered %d)" % (len(table), div, len(table) - div))
    print("jsonl: %d files / %d cells" % (jf, jc))
    print("scenario csv: %d files / %d cells" % (cf, cc))
    print("canon rows to drop: %d %s" % (len(cd), cd))
    for k in unknown[:10]:
        print("  unresolved %s" % k)
    if args.check:
        return 2 if (jc or cc or cd) else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
