# -*- coding: utf-8 -*-
"""清掉地名译文里混进来的拉丁字母残渣与模型解释。

典型：'吕贝ben'（Lübben）、'施韦因富特\n\n注：此处应为…'、'洛里ći 由于…'、'Repno沃卡'。
做法：
  1) 截断第一处换行之后的内容（模型解释都在换行后）；
  2) 去掉「注：」起的尾巴；
  3) 若剩下「中文 + 拉丁尾巴」，保留中文前缀（长度 ≥ 2）；
  4) 其余（以拉丁开头、或中文不足）记入待人工清单，不动。
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
PLACE = PROJECT / "data" / "scenario_csv" / "translations" / "place.zh.jsonl"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"
REPORT = PROJECT / "audit" / "place-latin-report.txt"

# 人工复核后逐条给出的标准译名（英文原文 -> 中文）
MANUAL = {
    "La Spezia": "拉斯佩齐亚", "Baia Mare": "巴亚马雷", "Bekescsaba": "贝凯什乔巴",
    "Kromy": "克罗梅", "Repyovka": "列皮约夫卡", "Gorny Balykley": "戈尔内巴雷克列伊",
    "Drogchin": "德罗吉钦", "Shklov": "什克洛夫", "Mersrags": "梅尔斯拉格斯",
    "Kamenets-Podolsky": "卡缅涅茨-波多利斯基", "Konstantinovka": "康斯坦丁诺夫卡",
    "Globino": "格洛比诺", "Maloarchangelsk": "小阿尔汉格尔斯克", "Emba": "恩巴",
    "Stoke on Trent": "特伦特河畔斯托克", "Newcastle upon Tyne": "泰恩河畔纽卡斯尔",
    "Chalon-sur-Saone": "索恩河畔沙隆", "Nogent sur Seine": "塞纳河畔诺让",
    "Montfort-sur-Meu": "默河畔蒙福尔", "Berck-sur-Mer": "滨海贝尔克",
    "Peronne": "佩罗讷", "Romilly-sur-Seine": "塞纳河畔罗米伊", "Fes": "非斯",
    "Gavle": "耶夫勒", "Balikesir": "巴勒克埃西尔", "Caltanissetta": "卡尔塔尼塞塔",
    "Luebben": "吕本", "Helmstedt": "赫尔姆施泰特", "Langendiebach": "兰根迪巴赫",
    "Toijala": "托伊亚拉", "Brazi": "布拉齐", "Fuzesabony": "菲泽沙博尼",
    "Hadju Boszormeny": "豪伊杜博瑟尔梅尼", "Wadowice": "瓦多维采", "Parczew": "帕尔切夫",
    "Brest Litovsk": "布列斯特-立托夫斯克", "Ilovlinskaya": "伊洛夫林斯卡亚",
    "Volnovakha": "沃尔诺瓦哈", "Valmiera": "瓦尔米耶拉", "Novorzhev": "诺沃尔热夫",
    "Zolochev (E)": "佐洛切夫", "Dzerzhinsk (e)": "捷尔任斯克", "Pavlovo (e)": "帕夫洛沃",
    "Nikolaevka (e)": "尼古拉耶夫卡", "Maina": "迈纳", "Syzran": "瑟兹兰",
    "Cheboksary": "切博克萨雷", "Telsiai": "特尔希艾", "Orany": "奥拉尼",
    "Hersfeld": "赫斯费尔德", "Locri": "洛克里", "Piest'any": "皮耶什佳尼",
    "Kramatorskaya": "克拉马托尔斯克", "Schwerin": "什未林", "Lapy": "瓦佩",
    "Viana do Castelo": "维亚纳-杜卡斯特卢", "Ciudad Real": "雷阿尔城",
    "Abu Ageila": "阿布阿盖拉", "Tanta": "坦塔", "Grafton Underwood": "格拉夫顿安德伍德",
    "Aulnay-aux-Planches": "奥尔奈欧普朗什", "Vailly-sur-Aisne": "艾讷河畔瓦伊",
    "G u l f  o f  S i d r a": "锡德拉湾", "Indre": "安德尔",
    "J u l i a n  A l p s": "尤利安阿尔卑斯山", "Schwarze Elster": "施瓦策埃尔斯特",
    "Drina": "德里纳河", "Malse": "马尔谢河", "Stettiner Haff": "什切青潟湖",
    "S u d e t e n  M o u n t a i n s": "苏台德山脉", "M  a  r  c  h  e": "马尔凯",
    "H o d n a": "霍德纳", "H o d n a  M o u n t  a  i  n  s": "霍德纳山脉",
    "Joensuu": "约恩苏", "Kestenga": "凯斯滕加", "Globitzy": "格洛比齐",
    "Goryn": "戈伦河", "L. Lacha": "拉恰湖", "L e s s e r  C a u c a s u s": "小高加索",
    "A. Kumoyarsky": "库莫亚尔斯基", "Konda": "孔达",
    "L o f o t e n  I s l a n d s": "罗弗敦群岛", "Vestfjorden": "韦斯特峡湾",
    "S o u t h  T u n i s i a": "南突尼斯",
}

CJK = re.compile(r"[\u4e00-\u9fff]")
CJK_PREFIX = re.compile(r"^([\u4e00-\u9fff][\u4e00-\u9fff·\-—\s]{1,20})[^\u4e00-\u9fff]*$")


def clean(v: str) -> tuple[str | None, bool]:
    """返回 (新值, 是否需要人工)。None 表示不改。"""
    if not v or not (CJK.search(v) and re.search(r"[A-Za-z]", v)):
        return None, False
    s = v.split("\n")[0].strip()
    s = re.split(r"注[:：]", s)[0].strip()
    s = re.sub(r"\s{2,}", " ", s)
    if not re.search(r"[A-Za-z]", s):
        return (s if s and s != v else None), False
    m = CJK_PREFIX.match(s)
    if m:
        cand = m.group(1).strip()
        if len(cand) >= 2 and cand != v:
            return cand, False
    return None, True


def main() -> None:
    rows = [json.loads(l) for l in PLACE.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    fixed, manual = 0, []
    for r in rows:
        forced = MANUAL.get((r.get("text") or "").strip())
        new, need_manual = clean(r.get("translation") or "")
        if forced:
            if r.get("translation") != forced:
                r["translation"] = forced
                fixed += 1
            continue
        if new is not None:
            r["translation"] = new
            fixed += 1
        elif need_manual:
            manual.append((r.get("text"), r.get("translation")))
    with PLACE.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    from fix_scenario_names import find_game, load_rows
    game = find_game()
    base = game / "Dat" / "CSV"
    cells = 0
    for zhf in sorted(CSVDIR.rglob("*.zh.csv")):
        rel = zhf.relative_to(CSVDIR)
        src_p = base / rel.parent.name / rel.name.replace(".zh.csv", ".csv")
        if not src_p.exists():
            continue
        srows, _ = load_rows(src_p)
        zrows, bom = load_rows(zhf)
        if len(srows) != len(zrows):
            continue
        dirty = False
        for s, z in zip(srows, zrows):
            for i in range(min(len(s), len(z))):
                forced = MANUAL.get((s[i] or "").strip())
                if forced:
                    if z[i] != forced:
                        z[i] = forced
                        dirty = True
                        cells += 1
                    continue
                new, _ = clean(z[i])
                if new:
                    z[i] = new
                    dirty = True
                    cells += 1
        if dirty:
            with zhf.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                csv.writer(f).writerows(zrows)

    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(f"{k!r} => {v!r}" for k, v in manual), encoding="utf-8")
    print(f"fixed={fixed} csv_cells={cells} manual={len(manual)} -> {REPORT}")


if __name__ == "__main__":
    main()
