#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prompt templates for WitE2 translation."""
from __future__ import annotations

from typing import Iterable

SYSTEM_PROMPT = """你是《War in the East 2》（东线战争2）的资深中文化译者，专精二战东线军事史与兵棋术语。你的译文会直接显示在游戏内，必须准确、简洁、统一。

只输出译文本身：不要解释，不要加“译文：”，不要用引号包住整段，不要保留英文原文（专有名词和型号除外）。

硬性规则：
1. 必须逐字采用【术语表】给出的译法；术语表标为 strict 的词不得换成近义词。
2. 原文中的 @@PH0@@、@@PH1@@ 等占位符必须原样保留，数量、顺序和位置都不能变。
3. 部队番号中的数字用阿拉伯数字：1st Panzer Division -> 第1装甲师；XXX Corps -> 第30军；Army Group North -> 北方集团军群。
4. 装备型号、舰船/飞机编号、日期、百分比、数值不要改写：Bf 109、T-34、8.8 cm Flak、1941 等保持原样或按术语表处理。
5. 人名、地名使用通用中文译名；没有把握的专有名词保留英文，不要音译出一个没人认识的版本。
6. 游戏界面/按钮/标签要短，优先 2-6 个汉字；说明文字要通顺，不要逐词硬译。
7. 不要增删原文信息，不要添加原文没有的解释、括号注释或单位换算。
8. 原文中的 <cr>、<b>、</b>、[b]、%s、{0} 等标记都是格式标记，必须按占位符规则保留。
"""

KIND_LABEL = {
    "unit_name": "部队番号",
    "airgroup_name": "航空部队番号",
    "leader_name": "将领姓名",
    "ui": "游戏界面文本",
    "exe_ui": "游戏界面文本",
    "description": "百科/说明文本",
    "scenario": "战役简报",
    "event": "事件/报告文本",
    "caption": "装备/部队简介标题",
}


def _hint_block(hints: Iterable) -> str:
    lines = []
    for e in hints:
        note = f"（{e.notes}）" if e.notes else ""
        lines.append(f"- {e.en} = {e.zh}{note}")
    return "\n".join(lines) if lines else "（无）"


def build_messages(source: str, context: str = "", hints: Iterable = (), kind: str = "description",
                   max_len: int | None = None) -> list[dict]:
    label = KIND_LABEL.get(kind, "游戏文本")
    limit = f"\n【长度限制】译文不超过 {max_len} 个字符。" if max_len else ""
    user = f"""【文本类型】{label}
【上下文】{context or '（无）'}
【术语表（必须遵守）】
{_hint_block(hints)}
【原文】
{source}
【译文】{limit}"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def build_retry_messages(source: str, previous: str, issues: list[str], context: str = "",
                         hints: Iterable = (), kind: str = "description",
                         max_len: int | None = None) -> list[dict]:
    base = build_messages(source, context, hints, kind, max_len)
    feedback = "\n".join(f"- {x}" for x in issues)
    base.append({"role": "assistant", "content": previous})
    base.append({
        "role": "user",
        "content": f"""上一版译文有以下硬性问题，请修正后重新输出完整译文（只输出译文）：
{feedback}

特别注意：术语必须与术语表完全一致；@@PHn@@ 占位符一个都不能少；不要添加解释。""",
    })
    return base


def build_batch_messages(items: list[dict], context: str = "", hints: Iterable = (),
                         kind: str = "exe_ui") -> list[dict]:
    """Batch UI strings as JSON.  Each item: {id, text}."""
    import json
    label = KIND_LABEL.get(kind, "游戏文本")
    user = f"""【文本类型】{label}
【上下文】{context or '（无）'}
【术语表（必须遵守）】
{_hint_block(hints)}
【任务】逐条翻译下面 JSON 数组中的 text 字段。只输出 JSON 数组，格式为 [{{"id": 原id, "text": "中文译文"}}]，不要输出任何其他内容。占位符 @@PHn@@ 必须原样保留。
【输入】
{json.dumps(items, ensure_ascii=False)}"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
