# -*- coding: utf-8 -*-
"""清理场景表显示层的脏单元格（v1.9.10 扫尾）。

与 fix_name_artifacts.py 的区别：**按英文源单元格行对齐**替换，而不是按中文值
全局替换。这样同名的中文值即使出现在别的单位/兵种上也不会被误伤（v1.9.10
批次四 SS 番号就吃过这个亏：旧值「第2/第13」同时是苏军航空团的名字）。

三类内容：
1. 元话语/原文残片（Bajnoczy -> 巴尼奥奇czy 不在翻译范围内…）；
2. 命令式误译/多语言混杂（AAMG Truck -> AA卡车、GR山地旅群、BR 装甲汽车团）；
3. 篇内散文残片（戈thic防线、特erek河畔），按英文原文是否含 Gothic/Terek 限定。

两层同写：data/**/*.jsonl 与 build/scenario_csv_zh/**。--check 只报不写，有残留返回 2。
"""
from __future__ import annotations

import argparse
import csv
import glob
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 英文键 -> 正译。必须精确等于英文源单元格才生效。
EN_FIX = {
    # 元话语 / 原文残片
    "Bajnoczy": "巴尼奥奇",
    "Markoczy": "马科奇",
    "Kurovichi": "库罗维奇",
    "Fort Kronprinz": "克龙普林茨要塞",
    # 命令/缩写误读
    "AAMG Truck": "高射机枪卡车",
    "Artillery Divisions": "炮兵师",
    "Feldherrnhalle Nr. 1": "统帅堂第1号",
    "Feldherrnhalle Nr. 2": "统帅堂第2号",
    "60th Sabratha": "第60萨布拉塔师",
    # 英国地方师：Leeds 统一为利兹（旧值 莱德斯/莱eds 三种写法）
    "1st Leeds": "第1利兹师",
    "2nd Leeds": "第2利兹师",
    "3rd Leeds": "第3利兹师",
    # OBs 国别缩写：BE=比利时、NE=荷兰、GR=希腊、BZ=巴西、AI=意大利盟军
    "BE Infantry Brigade Group": "比利时步兵旅群",
    "BE Armoured Car Regiment": "比利时装甲汽车团",
    "BE Fortified Zone": "比利时要塞区",
    "NE Infantry Brigade Group": "荷兰步兵旅群",
    "NE Fortified Zone": "荷兰要塞区",
    "GR Mountain Brigade Group": "希腊山地旅群",
    "GR Fortified Zone": "希腊要塞区",
    "BZ Infantry Division": "巴西步兵师",
    # AI = Allied Italy（意大利共同交战军，Nation 24：Cremona/Folgore/Friuli/Legnano…），
    # 不是「人工智能」。旧值「AI机械化集团」把国家码当缩略语留着。
    "AI Motorized Group": "意大利摩托化集群",
    # 苏军航空团：2/13 与 2/20 是歼击航空团番号，不是党卫军营（批次四误伤回滚）。
    # 同表其余 IAP 一律保留英文，故这里也恢复英文，令字典条目自然消失。
    "2/13 IAP-KBF": "2/13 IAP-KBF",
    "2/20 IAP": "2/20 IAP",
    # 单元测试第二遍扫出的残片与半译（2026-11-07 扫尾）
    "LW Kdo Kirkenes": "空军希尔克内斯指挥部",
    "II/Czechowice Heimat": "切霍维采第2本土部队",
    "II/Zwickau Heimat": "茨维考第2本土部队",
    "10th 'Piave'": "第10皮亚韦师",
    # OBs 保加利亚条目：旧值只译了国名前缀，兵种整段留在英文
    "Bul. Mot. Anti-Tank Battalion": "保加利亚摩托化反坦克营",
    "Bul. Mot. Field Gun Battalion": "保加利亚摩托化野战炮营",
    "Bul. Anti-Aircraft Regiment": "保加利亚高射炮团",
    "Bul. Heavy Anti-Aircraft Battalion": "保加利亚重型高射炮营",
    "Bul. Mot. Anti-Aircraft Battalion": "保加利亚摩托化高射炮营",
    # Korps Abteilung 是「军级支队」，不是 "corps 部队"
    "Korps Abteilung": "军级支队",
    "1st Bn BR": "英国第1营",
    "CA AGRA Brigade": "加拿大AGRA旅",
}

# 通用残留守卫：中文紧贴小写拉丁片段（Bajnoczy -> 巴尼奥奇czy 的 "czy"、
# Czechowice -> 切赫owitz 的 "owitz"、"红oub" 的 "oub"）。专有名词 van Duren 例外。
RESIDUE_RE = re.compile(r"[\u4e00-\u9fff]([a-z]{3,})")
RESIDUE_ALLOW = {"van"}

# (英文原文须含, 脏片段, 正片段)
PROSE_FIX = (
    ("Gothic", "戈thic防线", "哥特防线"),
    ("Terek", "特erek河畔", "捷列克河畔"),
    # German "Schanze" = 多面堡；旧值把 redoubt 的 red- 丢了，只剩 "红oub"。
    ("schanze", "红oub", "多面堡"),
)


def find_game():
    candidates = []
    env = os.environ.get("WITE2_GAME")
    if env:
        candidates.append(env)
    for rel in (("mod", "settings.local.json"), ("mod", "settings.json")):
        path = os.path.join(ROOT, *rel)
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
            except ValueError:
                continue
            for key in ("game_path", "install_path", "game_dir", "wite2_path"):
                value = data.get(key)
                if value:
                    candidates.append(value)
    for candidate in candidates:
        if os.path.exists(os.path.join(candidate, "WarInTheEast2.exe")):
            return candidate
    raise SystemExit("找不到游戏目录；请设置 WITE2_GAME 或在 mod\\settings.json 填写 game_path。")


def load_csv(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    bom = b""
    if raw.startswith(b"\xef\xbb\xbf"):
        bom, raw = raw[:3], raw[3:]
    newline = "\r\n" if b"\r\n" in raw[:4000] else "\n"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        # 原版 CSV 里混有 cp1252 字符（人名/地名），与 build_maps.py 同一回退策略。
        text = raw.decode("cp1252")
    rows = list(csv.reader(io.StringIO(text, newline="")))
    return bom, newline, rows


def dump_csv(path, bom, newline, rows):
    buf = io.StringIO(newline="")
    csv.writer(buf, lineterminator=newline).writerows(rows)
    data = bom + buf.getvalue().encode("utf-8")
    with open(path, "wb") as fh:
        fh.write(data)


def desired(en_cell, zh_cell):
    """按英文源单元格决定目标值；无需改动返回 None。"""
    if en_cell in EN_FIX:
        want = EN_FIX[en_cell]
        return None if zh_cell == want else want
    for en_word, bad, good in PROSE_FIX:
        if en_word in en_cell and bad in zh_cell:
            return zh_cell.replace(bad, good)
    return None


def fix_csv(game, check):
    files = cells = scanned = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "build", "scenario_csv_zh", "*", "*.zh.csv"))):
        scanned += 1
        scenario = os.path.basename(os.path.dirname(path))
        name = os.path.basename(path)[: -len(".zh.csv")] + ".csv"
        source = os.path.join(game, "Dat", "CSV", scenario, name)
        backup = os.path.join(ROOT, "csv_swap_backup", scenario, name)
        if not os.path.exists(source) and os.path.exists(backup):
            source = backup
        if not os.path.exists(source):
            continue
        _, _, en_rows = load_csv(source)
        bom, newline, zh_rows = load_csv(path)
        touched = 0
        for i, zh_row in enumerate(zh_rows):
            if i >= len(en_rows):
                break
            en_row = en_rows[i]
            for j, zh_cell in enumerate(zh_row):
                if j >= len(en_row):
                    break
                want = desired(en_row[j], zh_cell)
                if want is not None:
                    zh_row[j] = want
                    touched += 1
        if touched:
            files += 1
            cells += touched
            if not check:
                dump_csv(path, bom, newline, zh_rows)
                back = load_csv(path)
                if back[0] != bom or back[1] != newline or back[2] != zh_rows:
                    raise SystemExit("写回后往返不一致，拒写：%s" % path)
    return scanned, files, cells


def scan_residue():
    """跨全表扫「中文+小写拉丁」残留；返回 [(file, row, token, cell[:60])]。"""
    hits = []
    for path in sorted(glob.glob(os.path.join(ROOT, "build", "scenario_csv_zh", "*", "*.zh.csv"))):
        _, _, rows = load_csv(path)
        rel = os.path.relpath(path, ROOT)
        for i, row in enumerate(rows):
            for cell in row:
                for m in RESIDUE_RE.finditer(cell):
                    if m.group(1) in RESIDUE_ALLOW:
                        continue
                    hits.append((rel, i, m.group(1), cell[:60]))
    return hits


def fix_jsonl(check):
    files = cells = 0
    keys = set(EN_FIX)
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "**", "*.jsonl"), recursive=True)):
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
        out, touched = [], 0
        for line in lines:
            stripped = line.strip()
            if not stripped:
                out.append(line)
                continue
            try:
                rec = json.loads(stripped)
            except ValueError:
                out.append(line)
                continue
            text = rec.get("text")
            trans = rec.get("translation")
            want = None
            if isinstance(text, str) and text in keys:
                want = EN_FIX[text]
            elif isinstance(text, str) and isinstance(trans, str):
                for en_word, bad, good in PROSE_FIX:
                    if en_word in text and bad in trans:
                        want = trans.replace(bad, good)
                        break
            if want is not None and want != trans:
                rec["translation"] = want
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只报告，不写入；有残留返回 2")
    args = ap.parse_args()
    game = find_game()
    scanned, cf, cc = fix_csv(game, args.check)
    jf, jc = fix_jsonl(args.check)
    print("fix_cell_dirt: csv %d cells / %d files (scanned %d); jsonl %d cells / %d files"
          % (cc, cf, scanned, jc, jf))
    residue = scan_residue()
    if residue:
        for rel, i, token, cell in residue[:10]:
            print("  RESIDUE %s r%d %r => %s" % (rel, i, token, cell))
        print("fix_cell_dirt: residue %d cell(s)" % len(residue))
    else:
        print("fix_cell_dirt: residue 0")
    if args.check and (cc or jc or residue):
        print("FAIL: 场景表仍有脏单元格")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
