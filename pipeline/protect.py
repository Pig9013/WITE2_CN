#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Placeholder and markup protection for LLM translation."""
from __future__ import annotations

import re
from dataclasses import dataclass

TOKEN_RE = re.compile(r"@@PH(\d+)@@")
PLACEHOLDER_PATTERNS = [
    re.compile(r"%[-+ 0#]*\d*(?:\.\d+)?[sdifuxXc]"),          # printf
    re.compile(r"\{[^{}\n]{1,80}\}"),                          # {0}, {unit}
    re.compile(r"<[^<>\n]{1,80}>"),                            # <cr>, <url>
    re.compile(r"\[[^\[\]\n]{1,80}\]"),                        # [b], [unit]
    re.compile(r"https?://[^\s<>()]+"),                        # URLs
]


@dataclass
class Protected:
    masked: str
    tokens: list[str]
    leading: str
    trailing: str


def protect(text: str) -> Protected:
    leading = text[: len(text) - len(text.lstrip())]
    trailing = text[len(text.rstrip()):]
    core = text.strip()
    tokens: list[str] = []

    def repl(m: re.Match) -> str:
        idx = len(tokens)
        tokens.append(m.group(0))
        return f"@@PH{idx}@@"

    masked = core
    for pat in PLACEHOLDER_PATTERNS:
        masked = pat.sub(repl, masked)
    return Protected(masked=masked, tokens=tokens, leading=leading, trailing=trailing)


def restore(protected: Protected, translated: str) -> str:
    out = translated.strip()
    for i, token in enumerate(protected.tokens):
        out = out.replace(f"@@PH{i}@@", token)
        # Tolerate the model inserting spaces around the token.
        out = re.sub(r"@@\s*PH\s*%d\s*@@" % i, token, out)
    return protected.leading + out + protected.trailing


def missing_tokens(protected: Protected, translated: str) -> list[str]:
    missing = []
    for i, token in enumerate(protected.tokens):
        if f"@@PH{i}@@" not in translated:
            missing.append(token)
    return missing


def extra_tokens(protected: Protected, translated: str) -> list[str]:
    used = {int(m.group(1)) for m in TOKEN_RE.finditer(translated)}
    return [f"@@PH{i}@@" for i in used if i >= len(protected.tokens)]


def translate_paragraphs(text: str, fn) -> str:
    """Apply fn to non-separator paragraphs, preserving blank-line layout."""
    parts = re.split(r"(\n\s*\n)", text)
    for i, part in enumerate(parts):
        if i % 2 == 0 and part.strip():
            parts[i] = fn(part)
    return "".join(parts)


if __name__ == "__main__":
    sample = "  Move %s to <b>Kharkov</b> ({0}) at 12:30.\n\nSupply: 88%%  "
    p = protect(sample)
    print(repr(p.masked), p.tokens, repr(p.leading), repr(p.trailing))
    fake = p.masked.replace("Move", "移动").replace("Kharkov", "哈尔科夫").replace("Supply", "补给")
    print(repr(restore(p, fake)))
    print("missing", missing_tokens(p, fake))
