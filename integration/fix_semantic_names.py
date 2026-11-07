# -*- coding: utf-8 -*-
"""semantic 类同词多译的定点裁决（v1.9.10 批次五）。

audit/layer-conflicts.json 里 399 条 semantic 冲突不是格式差异，是真正的译名分歧
（262 条地名音译、103 条部队番号、34 条长事件正文）。逐条裁决需要权威译名表，
本轮只处理**能由英文原文直接判定**的条目（FIX 表），其余留在
audit/semantic-unresolved.csv 待裁决。

写法：同一英文键在 jsonl 与场景 CSV 两层必须一致；CSV 按**英文源表同一行列**
定位（不按中文值猜），避免误伤同值的其他键。写回后做字节往返校验。
--check 只报不写，仍有残留返回 2。
"""
from __future__ import annotations

import argparse
import csv
import glob
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 英文键 -> 正译。只收「英文原文足以判定」的条目：
# - Fliegerkorps 是 Luftwaffe 的航空军（不是「航空队」，航空队是 Luftflotte）；
# - OKL = Oberkommando der Luftwaffe，空军总司令部；
# - Transcaucasus 是外高加索（不是「高加索地区」）；
# - Rosiorii 是罗马尼亚地名 Rosiorii de Vede，不是「摩托化步兵」；
# - Heimat 部队读作「本土部队」，不是「故乡/家乡/故土」。
FIX = {
    "Transcaucasus": "外高加索",
    "Rosiorii": "罗希奥里",
    "I Fliegerkorps": "第1航空军",
    "II Fliegerkorps": "第2航空军",
    "X Fliegerkorps": "第10航空军",
    "OKL": "空军总司令部",
    "L.A.H. SS": "党卫军阿道夫·希特勒警卫旗队",
    "Hauck": "豪克",
    "Neame": "尼姆",
    "Leeming": "利明",
    "Bowmore": "波摩",
    "Frontier": "边境",
    "I/Chemnitz Heimat": "开姆尼茨第1本土部队",
    "I/S. BH Heimat": "BH 第1本土部队",
    "II/N. BH Heimat": "BH 第2（N）本土部队",
    "IV/Stuttgart Heimat": "斯图加特第4本土部队",
    "VI/Stuttgart Heimat": "斯图加特第6本土部队",
}


def _find_game() -> Path:
    candidates = []
    env = os.environ.get("WITE2_GAME")
    if env:
        candidates.append(Path(env))
    for name in ("settings.json", "settings.local.json"):
        p = ROOT / "mod" / name
        if p.exists():
            try:
                value = json.loads(p.read_text(encoding="utf-8")).get("game_path")
                if value:
                    candidates.append(Path(value))
            except Exception:
                pass
    for c in candidates:
        if (c / "WarInTheEast2.exe").exists():
            return c
    raise SystemExit("找不到游戏目录：设置 WITE2_GAME 或在 mod/settings.json 填 game_path")


def _load(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    bom = b""
    if raw.startswith(b"\xef\xbb\xbf"):
        bom, raw = raw[:3], raw[3:]
    newline = "\r\n" if b"\r\n" in raw[:4000] else "\n"
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline="")))
    return bom, newline, rows


def _dump(path, bom, newline, rows):
    buf = io.StringIO(newline="")
    csv.writer(buf, lineterminator=newline).writerows(rows)
    with open(path, "wb") as fh:
        fh.write(bom + buf.getvalue().encode("utf-8"))


def fix_jsonl(check):
    files = cells = 0
    # data/extracted/ 是 EXE/CSV 抽出的**原文证据**，不是译文层，绝不在那里写 translation。
    targets = []
    for sub in ("data/scenario_csv/translations", "data/translations"):
        targets += sorted(glob.glob(str(ROOT / sub / "*.jsonl")))
    for path in targets:
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
            if isinstance(text, str) and text in FIX and rec.get("translation") != FIX[text]:
                rec["translation"] = FIX[text]
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


# 只改「显示名列」。GameEvents.zh.csv 是宽参数表（列号到 500+），里面同名的
# 英文格是事件脚本参数，不是可译文本——按文件名白名单排除，避免把脚本翻译坏。
DISPLAY_FILES = {"Units.zh.csv", "Locations.zh.csv", "Leaders.zh.csv",
                 "AOGs.zh.csv", "MapText.zh.csv"}
DISPLAY_COLUMNS = {"Name", "newName", "mtText"}


def fix_csv(game, check):
    files = cells = 0
    for zh_path in sorted((ROOT / "build" / "scenario_csv_zh").glob("*/*.zh.csv")):
        if zh_path.name not in DISPLAY_FILES:
            continue
        scenario = zh_path.parent.name
        name = zh_path.name.replace(".zh.csv", ".csv")
        source = game / "Dat" / "CSV" / scenario / name
        if not source.exists():
            source = ROOT / "csv_swap_backup" / scenario / name
        if not source.exists():
            continue
        try:
            src_rows = list(csv.reader(source.read_bytes().decode("utf-8-sig").splitlines(keepends=True)))
        except UnicodeDecodeError:
            src_rows = list(csv.reader(source.read_bytes().decode("cp1252").lstrip("\ufeff").splitlines(keepends=True)))
        bom, newline, rows = _load(zh_path)
        if len(src_rows) != len(rows):
            raise SystemExit("结构不一致：%s" % zh_path)
        header = rows[0]
        cols = [j for j, name in enumerate(header) if name in DISPLAY_COLUMNS]
        if not cols:
            raise SystemExit("找不到显示名列：%s" % zh_path)
        touched = 0
        for i, (src_row, row) in enumerate(zip(src_rows, rows)):
            if i == 0:
                continue
            if len(src_row) != len(row):
                raise SystemExit("列数不一致：%s 行 %d" % (zh_path, i + 1))
            for j in cols:
                if j >= len(src_row):
                    continue
                src = src_row[j]
                if src in FIX and row[j] != FIX[src] and row[j]:
                    row[j] = FIX[src]
                    touched += 1
        if touched:
            files += 1
            cells += touched
            if not check:
                _dump(zh_path, bom, newline, rows)
                back = _load(zh_path)
                if back[0] != bom or back[1] != newline or back[2] != rows:
                    raise SystemExit("写回后往返不一致，拒写：%s" % zh_path)
    return files, cells


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files, cells = fix_jsonl(args.check)
    cf, cc = fix_csv(_find_game(), args.check)
    print("semantic fix: %d keys" % len(FIX))
    print("jsonl: %d files / %d cells" % (files, cells))
    print("scenario csv: %d files / %d cells" % (cf, cc))
    if args.check and (cells or cc):
        print("SEMANTIC-FIX: FAIL")
        return 2
    print("SEMANTIC-FIX: %s" % ("CHECK OK" if args.check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
