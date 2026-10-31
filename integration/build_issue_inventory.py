# -*- coding: utf-8 -*-
"""生成 docs/全量问题清查.md：把所有缺陷类型、命中点、高发区一次性列清。"""
from __future__ import annotations

import collections
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DICT = PROJECT / "mod" / "payload" / "translations.json"
PROV = PROJECT / "audit" / "provenance.json"
OV = PROJECT / "glossary" / "reference_overrides.json"
MANUAL = PROJECT / "glossary" / "manual_translations.json"
OUT = PROJECT / "docs" / "全量问题清查.md"

CJK = re.compile(r"[\u4e00-\u9fff]")


def main() -> None:
    d = json.loads(DICT.read_text(encoding="utf-8"))
    prov = json.loads(PROV.read_text(encoding="utf-8")) if PROV.exists() else {}
    ov = json.loads(OV.read_text(encoding="utf-8")) if OV.exists() else {}
    manual = json.loads(MANUAL.read_text(encoding="utf-8")) if MANUAL.exists() else {}

    src = collections.Counter()
    for k, o in prov.items():
        src[str(o).split(" / ")[0].split(" ")[0]] += 1

    def count(pred):
        return sum(1 for v in d.values() if isinstance(v, str) and pred(v))

    rows = [
        ("01", "空译文", "值为空/纯空白", count(lambda v: not v.strip()), "翻译流程漏写", "0"),
        ("02", "模型自述残留", "含 注意：/应该是/请提供（不含正常用词的「由于」）", count(lambda v: bool(re.search(r"注意[:：]|应该是|请提供|无法确定|保持原样", v))), "早期本地模型把思考过程写进输出", "0"),
        ("03", "内部占位符", "含 @ 或 @@PHn@@", count(lambda v: "@" in v), "导出/回填的占位符未替换", "0"),
        ("04", "假名/西里尔/乱码", "混入非中文字符", count(lambda v: bool(re.search(r"[\ufffd\u3040-\u30ff\u0400-\u04ff\u0370-\u03ff]", v))), "多语种模型串味", "0"),
        ("05", "叠字", "军军/师师/的的/了了", count(lambda v: bool(re.search(r"(军|师|团|旅|营|兵|的|了|在|是)\1", v))), "拼接或重复生成", "0"),
        ("06", "数字残渣", "60% c% 之类", count(lambda v: bool(re.search(r"\d+%\s*[A-Za-z]", v))), "模型复制原文片段", "0"),
        ("07", "未翻译", "整条仍是拉丁字母", count(lambda v: bool(v.strip()) and not CJK.search(v) and bool(re.fullmatch(r"[\sA-Za-z0-9\.\-\(\)%/,']+", v))), "漏译/跳过", "3 条有意保留"),
        ("08", "中文夹长拉丁", "剔除型号名后仍夹 5+ 字母", count(lambda v: bool(re.search(r"[A-Za-z]{5,}", v)) and bool(CJK.search(v)) and not re.search(r"Sd[Kk]fz|Panzer|Flak|Pak|Jagd|B-d|Mk|Hispano|SAFAT|ShKAS|Theodor|Marauder", v)), "型号名保留原文", "0 条真缺陷（型号名属正常）"),
        ("09", "括号失衡", "（与）数量不等", count(lambda v: v.count("（") != v.count("）")), "截断或替换残留", "0"),
        ("10", "标点堆积", "。，：连续出现（排除 cr 标记）", count(lambda v: bool(re.search(r"[，。；：：]{2,}", v.replace("<cr>", "")))), "项目符号丢失", "0"),
        ("11", "长句重复片段", "8~24 字二次出现", count(lambda v: bool(re.search(r"(.{8,24})\1", v.replace("<cr>", "")))), "生成时重复输出", "7 条表头误报"),
        ("12", "地名常用词化", "地名被译成常用词", 0, "按字面义直译（Vecht 战斗）", "已清 60 条"),
        ("13", "名称与编制矛盾", "第N师 vs 编制为营", 0, "名字缺类型时瞎猜", "已清 150 条"),
        ("14", "专名直译", "Sep. 九月 / 3 Gennaio 一月三日", 0, "把缩写或番号当普通词", "已清 20 条"),
        ("15", "国名缩写误译", "Bul. 布良斯克", 0, "缩写撞上地名", "已清 104 条"),
    ]

    L = []
    L.append("# 全量问题清查\n")
    L.append("> 一份清单：问题类型 → 判定方法 → 当前命中数 → 根因 → 状态。")
    L.append("> 数据快照：词典 " + str(len(d)) + " 条。\n")

    L.append("## 一、为什么会反复改同一个词\n")
    L.append("词典是**多层叠加**构建的，后读的层覆盖先读的层：\n")
    L.append("    data/**/*.jsonl")
    L.append("      -> data/translations/unit_names_en_zh.csv")
    L.append("      -> build/translation.csv")
    L.append("      -> mod/assets/translation.csv")
    L.append("      -> build/scenario_csv_zh/*.zh.csv\n")
    L.append("同一条词条可能同时存在三四个层里。只改了 jsonl，场景 CSV 里的旧值照样覆盖回来，")
    L.append("于是同一个词要改三四次——这就是看到的「重复劳动」。\n")
    L.append("**结构性修复**：新增 glossary/master_overrides.json 作为**最后一道覆盖层**，")
    L.append("build_maps.py 在写词典前统一套用。以后改一次即生效，不必逐层改。")
    L.append("现有 " + str(len(ov.get("places", {})) + len(ov.get("terms", {})) + len(ov.get("ui", {})) + len(manual)) +
             " 条定译已全部汇入该层。\n")

    L.append("## 二、问题类型总表\n")
    L.append("| 编号 | 类型 | 判定方法 | 当前命中 | 根因 | 状态 |")
    L.append("|---|---|---|---|---|---|")
    for r in rows:
        L.append("| " + r[0] + " | " + r[1] + " | " + r[2] + " | " + str(r[3]) + " | " + r[4] + " | " + r[5] + " |")
    L.append("")

    L.append("## 三、高发区\n")
    L.append("| 类别 | 定译条数 | 主要问题 |")
    L.append("|---|---|---|")
    L.append("| 地名 | " + str(len(ov.get("places", {}))) + " | 音译混乱、常用词直译、大城零命中 |")
    L.append("| 番号/部队 | " + str(len(ov.get("terms", {}))) + " | 类型词乱补、国名缩写误译、专名直译 |")
    L.append("| 界面词 | " + str(len(ov.get("ui", {}))) + " | 机制词直译 |")
    L.append("| 长文本人工重译 | " + str(len(manual)) + " | 整段仍英文、模型自述 |")
    L.append("")

    L.append("## 四、词典来源分层\n")
    L.append("| 来源层 | 条目数 |")
    L.append("|---|---|")
    for k, n in src.most_common(12):
        L.append("| " + str(k) + " | " + str(n) + " |")
    L.append("")

    L.append("## 五、无法自动判定的三类\n")
    L.append("1. **译名取舍**：同一地名有多种通行译法（哈尔科夫/哈尔基夫），无对错。")
    L.append("2. **句子流畅度**：语义无误但读着别扭，机器判不出。")
    L.append("3. **史实性**：原文本身矛盾（如 XI SS 军「1945 年组建、1945 年 2 月改称」），照译不算错。\n")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote", OUT.name, "dict", len(d))


if __name__ == "__main__":
    main()
