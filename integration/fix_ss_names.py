# -*- coding: utf-8 -*-
"""SS 番号整族规范化（v1.9.10 批次四）。

修复四类缺陷：
1. 斜杠分队名（1/13th SS）旧译「第1/第13」，SS 与分队语义整段丢失；
2. 国籍缩写被直译成前置定语的乱序（第15拉脱维亚运兵党卫军步兵师）；
3. 把番号当单词直译的脏值（第28党卫军师墙单位、第34党卫军师（净选）、第26猎兵师（党卫军））；
4. 罗马数字 / 中文数字与阿拉伯数字混用（I 党卫军、第四党卫军装甲师），以及 jsonl 层
   给裸番号擅自补「师」（第13党卫军装甲师，13th SS 实为山地师）。

统一口径（写进 docs/SS番号审计_v1.9.10.md）：
- 数字一律阿拉伯数字，SS 一律译「党卫军」；
- 番号在前、兵种在后：第N党卫军（国籍）<兵种><编制>；兵种只在英文原文写明时才补；
- 分队名 N/M 读作「第M党卫军第N营」；
- 军级（Roman + Corps/Mountain/Cossack）用「党卫军第N<兵种>军」，避免「第10党卫军军」叠字。

两层同时改：jsonl 语料层（data/**）与场景 CSV 显示层（build/scenario_csv_zh/**）。
--check 只报不写，有残留返回 2。
"""
from __future__ import annotations

import argparse
import csv
import glob
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 英文键 -> 正译
BY_EN = {
    # 1. 分队名 N/M
    "1/13th SS": "第13党卫军第1营",
    "2/13th SS": "第13党卫军第2营",
    "3/13th SS": "第13党卫军第3营",
    "1/20th SS Est.": "第20党卫军（爱沙尼亚）第1营",
    "2/20th SS Est.": "第20党卫军（爱沙尼亚）第2营",
    "3/20th SS Est.": "第20党卫军（爱沙尼亚）第3营",
    "1/33rd SS Fr.": "第33党卫军（法国）第1营",
    "2/33rd SS Fr.": "第33党卫军（法国）第2营",
    "3/33rd SS Fr.": "第33党卫军（法国）第3营",
    "1/Nord SS": "北方党卫军第1营",
    "2/Nord SS": "北方党卫军第2营",
    "3/Nord SS": "北方党卫军第3营",
    "1/Wiking SS": "维京党卫军第1营",
    "2/Wiking SS": "维京党卫军第2营",
    "3/Wiking SS": "维京党卫军第3营",
    # 2. 国籍后缀（缩写 -> 全称，前置定语 -> 括号注）
    "14th SS Ukr.": "第14党卫军（乌克兰）",
    "15th SS Latv.": "第15党卫军（拉脱维亚）",
    "19th SS Latv.": "第19党卫军（拉脱维亚）",
    "19th SS Latvian": "第19党卫军（拉脱维亚）",
    "20th SS Est.": "第20党卫军（爱沙尼亚）",
    "25th SS Hun.": "第25党卫军（匈牙利）",
    "26th SS Hun.": "第26党卫军（匈牙利）",
    "28th SS Wall.": "第28党卫军（瓦隆）",
    "29th SS Ital.": "第29党卫军（意大利）",
    "29th SS Russ.": "第29党卫军（俄罗斯）",
    "30th SS Russ.": "第30党卫军（俄罗斯）",
    "31st SS Croat.": "第31党卫军（克罗地亚）",
    "33rd SS Fr.": "第33党卫军（法国）",
    "34th SS Neth.": "第34党卫军（荷兰）",
    "1st SS Ital.": "第1党卫军（意大利）",
    "6th SS Flan.": "第6党卫军（佛兰德）",
    "27th SS Flan.": "第27党卫军装甲掷弹兵师（佛兰德）",
    "8th SS French Sturm": "第8党卫军（法国）突击旅",
    "35th SS und Polizei": "第35党卫军与警察部队",
    "4th SS Neth.": "荷兰党卫军第4装甲掷弹兵旅",
    # 3. 名号型（Nord/Wiking/Nederland 等）
    "Nord SS": "北方党卫军",
    "Wiking SS": "维京党卫军",
    "Totenkopf SS": "骷髅党卫军",
    "Langemarck SS": "兰根马克党卫军",
    "Wallonian SS": "瓦隆党卫军",
    "Charlemagne SS French": "夏尔曼党卫军（法国）",
    "Flandern SS": "佛兰德党卫军",
    "Narva SS Estonian": "纳尔瓦党卫军（爱沙尼亚）",
    "Landstorm Neth. SS": "荷兰国土风暴党卫军",
    "Landstorm Nederland' SS": "荷兰国土风暴党卫军",
    "SS Landstorm Neth.": "荷兰国土风暴党卫军",
    "2nd SS Latvian": "拉脱维亚党卫军第2旅",
    "3rd SS Estonian": "爱沙尼亚党卫军第3旅",
    "5th SS Wallonian": "瓦隆党卫军第5突击旅",
    "5th SS Walloonian": "瓦隆党卫军第5突击旅",
    # 4. 军级（Roman + Corps/Mountain/Cossack）
    "V SS Mountain": "党卫军第5山地军",
    "IX SS Mountain": "党卫军第9山地军",
    "XV SS Cossack": "党卫军第15哥萨克骑兵军",
    "VI SS Latv.": "党卫军第6军（拉脱维亚）",
    "IV SS Panzer Corps": "党卫军第4装甲军",
    "VII SS Panzer Corps": "党卫军第7装甲军",
    "XI SS Panzer Corps": "党卫军第11装甲军",
    # 5. 英文写明编制的师
    "18th SS Mountain": "第18党卫军山地师",
    "1st SS Panzer Division": "第1党卫军装甲师",
    "1st SS Panzer Division L.A.H.": "第1党卫军装甲师阿道夫·希特勒警卫旗队",
    "2nd SS Panzer Division Das Reich": "第2党卫军装甲师帝国",
    "3rd SS Panzer Division 'Totenkopf'": "第3党卫军装甲师骷髅",
    "5th SS Panzer Division 'Wiking'": "第5党卫军装甲师维京",
    "23rd SS Panzergrenadier Division": "第23党卫军装甲掷弹兵师",
    "23rd SS Vlntr Pzrgrn 'Nederland'": "第23党卫军志愿装甲掷弹兵师（荷兰）",
    "Polizei SS Infantry Division": "警察党卫军步兵师",
    "Totenkopf SS Motorized Division": "骷髅党卫军摩托化师",
    "43a 2nd SS Lett.": "43a 第2党卫军（拉脱维亚）",
    "43b 2nd SS Lett.": "43b 第2党卫军（拉脱维亚）",
    "****** Waffen SS Battalions ******": "****** 武装党卫军营 ******",
}

# 6. 裸番号：罗马/中文数字统一为阿拉伯，并去掉 jsonl 层擅自补的「师」
_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
          "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
          "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20}
for _r, _n in _ROMAN.items():
    BY_EN["%s SS" % _r] = "第%d党卫军" % _n
for _n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
           24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 49, 51, 101, 102, 103,
           105, 500, 501, 502, 503, 504, 505, 509, 512, 513, 560, 561, 600):
    for _suf in ("st", "nd", "rd", "th"):
        _k = "%d%s SS" % (_n, _suf)
        if _k in BY_EN:
            continue
    BY_EN["%d%s SS" % (_n, "st" if _n % 10 == 1 and _n != 11 else "nd" if _n % 10 == 2 and _n != 12 else "rd" if _n % 10 == 3 and _n != 13 else "th")] = "第%d党卫军" % _n

# 旧中文值（字典层）-> 新值：用于场景 CSV 的显示层替换
CELL_FIX = {}


def _dict_value_map() -> dict:
    path = os.path.join(ROOT, "mod", "payload", "translations.json")
    with open(path, encoding="utf-8") as fh:
        cur = json.load(fh)
    out = {}
    for en, new in BY_EN.items():
        old = cur.get(en)
        if old and old != new:
            out[old] = new
    return out


def fix_jsonl(check: bool) -> tuple[int, int]:
    files = cells = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "**", "*.jsonl"), recursive=True)):
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
        out, touched = [], 0
        for line in lines:
            s = line.strip()
            if not s:
                out.append(line)
                continue
            try:
                rec = json.loads(s)
            except ValueError:
                out.append(line)
                continue
            text = rec.get("text")
            if isinstance(text, str) and text in BY_EN and rec.get("translation") != BY_EN[text]:
                rec["translation"] = BY_EN[text]
                touched += 1
                out.append(json.dumps(rec, ensure_ascii=False) + ("\n" if line.endswith("\n") else ""))
            else:
                out.append(line)
        if touched:
            files += 1
            cells += touched
            if not check:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.writelines(out)
    return files, cells


def _load(path: str):
    with open(path, "rb") as fh:
        raw = fh.read()
    bom = b""
    if raw.startswith(b"\xef\xbb\xbf"):
        bom, raw = raw[:3], raw[3:]
    newline = "\r\n" if b"\r\n" in raw[:4000] else "\n"
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline="")))
    return bom, newline, rows


def _dump(path: str, bom: bytes, newline: str, rows) -> None:
    buf = io.StringIO(newline="")
    csv.writer(buf, lineterminator=newline).writerows(rows)
    with open(path, "wb") as fh:
        fh.write(bom + buf.getvalue().encode("utf-8"))


def fix_csv(check: bool) -> tuple[int, int, int]:
    files = cells = scanned = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "build", "scenario_csv_zh", "*", "*.zh.csv"))):
        scanned += 1
        bom, newline, rows = _load(path)
        touched = 0
        for row in rows:
            for i, cell in enumerate(row):
                if cell in CELL_FIX:
                    row[i] = CELL_FIX[cell]
                    touched += 1
        if touched:
            files += 1
            cells += touched
            if not check:
                _dump(path, bom, newline, rows)
                back = _load(path)
                if back[0] != bom or back[1] != newline or back[2] != rows:
                    raise SystemExit("写回后往返不一致，拒写：%s" % path)
    return scanned, files, cells


# 词表层：值与键的对应列位置不同
# (相对路径, 译文列, 英文键列)；-1 表示最后一列
VOCAB = (
    ("mod/assets/translation.csv", -1, 1),
    ("build/translation.csv", -1, 1),
    ("data/translations/unit_names_en_zh.csv", 1, 0),
)


def fix_vocab(check: bool) -> tuple[int, int]:
    files = cells = 0
    for rel, vil, kil in VOCAB:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(path):
            continue
        bom, newline, rows = _load(path)
        touched = 0
        for row in rows:
            if len(row) <= max(vil, kil):
                continue
            en = row[kil]
            if en in BY_EN and row[vil] != BY_EN[en]:
                row[vil] = BY_EN[en]
                touched += 1
        if touched:
            files += 1
            cells += touched
            if not check:
                _dump(path, bom, newline, rows)
                back = _load(path)
                if back[0] != bom or back[1] != newline or back[2] != rows:
                    raise SystemExit("写回后往返不一致，拒写：%s" % path)
    return files, cells


def main() -> int:
    global CELL_FIX
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    CELL_FIX = _dict_value_map()
    printed = 0
    for old, new in sorted(CELL_FIX.items()):
        if old != new:
            print("CELL %s -> %s" % (old, new))
            printed += 1
    jf, jc = fix_jsonl(args.check)
    scanned, cf, cc = fix_csv(args.check)
    vf, vc = fix_vocab(args.check)
    print("fix_ss_names: jsonl %d cells / %d files; csv %d cells / %d files (scanned %d); vocab %d cells / %d files; cell-map %d"
          % (jc, jf, cc, cf, scanned, vc, vf, printed))
    if args.check and (jc or cc or vc):
        print("FAIL: 仍有 SS 番号脏值")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
