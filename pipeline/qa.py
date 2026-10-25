#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quality checks for a translated string."""
from __future__ import annotations

import re
from collections import Counter
from typing import Optional

from protect import protect

CJK_RE = re.compile(r"[\u3400-\u9fff]")
LATIN_WORD_RE = re.compile(r"[A-Za-z]{4,}")
PUNCT_RUN_RE = re.compile(r"([，。！？；：、,.!?;:])\1{2,}")


def _issue(code: str, severity: str, message: str) -> dict:
    return {"code": code, "severity": severity, "message": message}


def check_pair(source: str, target: str, glossary=None, max_len: Optional[int] = None,
               kind: str = "") -> list[dict]:
    issues: list[dict] = []
    s = source.strip()
    t = target.strip()
    if not t:
        return [_issue("empty", "error", "译文为空")]
    if not s:
        return issues
    if not CJK_RE.search(t) and re.search(r"[A-Za-z]", s):
        issues.append(_issue("no_cjk", "error", "译文中没有中文字符"))
    if t == s and re.search(r"[A-Za-z]{2,}", s):
        issues.append(_issue("untranslated", "error", "译文与原文相同"))

    ps, pt = protect(source), protect(target)
    if Counter(ps.tokens) != Counter(pt.tokens):
        missing = [x for x in ps.tokens if x not in pt.tokens]
        extra = [x for x in pt.tokens if x not in ps.tokens]
        layout_only = all(x.lower() in ("<cr>", "<b>", "</b>", "<br>", "<br/>", "<br />",
                                        "[b]", "[/b]", "[i]", "[/i]")
                          for x in missing + extra)
        sev = "warning" if kind in ("description", "event", "scenario") and layout_only else "error"
        issues.append(_issue("placeholder", sev, f"占位符不一致；缺失={missing} 多出={extra}"))

    if glossary is not None:
        # Check against the masked source: "<cr>" must not be mistaken for "cr".
        sev = "warning" if kind in ("description", "event", "scenario") else "error"
        for msg in glossary.check(ps.masked, target):
            issues.append(_issue("glossary", sev, msg))

    if max_len is not None and max_len > 0 and len(t) > max_len:
        issues.append(_issue("max_len", "error", f"译文长度 {len(t)} 超过上限 {max_len}"))

    if len(s) >= 8:
        ratio = len(t) / max(1, len(s))
        if ratio > 1.35:
            issues.append(_issue("length_long", "warning", f"译文偏长（{len(t)}/{len(s)} = {ratio:.2f}）"))
        elif ratio < 0.20:
            issues.append(_issue("length_short", "warning", f"译文偏短（{len(t)}/{len(s)} = {ratio:.2f}）"))

    if source.count("\n") != target.count("\n"):
        issues.append(_issue("newline", "warning", "换行数不一致"))

    for open_ch, close_ch in (("(", ")"), ("[", "]"), ("{", "}")):
        if t.count(open_ch) != t.count(close_ch):
            issues.append(_issue("bracket", "warning", f"括号不配对: {open_ch}{close_ch}"))
    if t.count("“") != t.count("”"):
        issues.append(_issue("quote", "warning", "中文引号不配对"))

    if PUNCT_RUN_RE.search(t):
        issues.append(_issue("punctuation", "warning", "出现连续重复标点"))

    latin = LATIN_WORD_RE.findall(t)
    if len(latin) > 3 and kind not in ("exe_ui",):
        issues.append(_issue("latin_residue", "warning", f"残留英文单词较多: {latin[:6]}"))

    return issues


def is_blocking(issues: list[dict]) -> bool:
    return any(i["severity"] == "error" for i in issues)


def summarize(issues: list[dict]) -> str:
    if not issues:
        return "OK"
    return "; ".join(f"{i['severity']}:{i['code']}" for i in issues)


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from glossary import load_glossary
    g = load_glossary(os.path.join(os.path.dirname(__file__), "..", "glossary", "ww2_military_en_zh.csv"))
    tests = [
        ("The 4th Panzer Army attacked near Kharkov.", "第4装甲集团军在哈尔科夫附近发起攻击。"),
        ("The 4th Panzer Army attacked near Kharkov.", "第4装甲军在哈尔科夫附近发起攻击。"),
        ("Move %s to <b>Kharkov</b>.", "把 @@PH0@@ 移动到 @@PH1@@哈尔科夫@@PH2@@。"),
        ("Move %s to <b>Kharkov</b>.", "把哈尔科夫移过去。"),
    ]
    for s, t in tests:
        print(t, "=>", summarize(check_pair(s, t, g)))
