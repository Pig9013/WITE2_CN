#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Glossary loading, matching and compliance checks."""
from __future__ import annotations

import csv
import hashlib
import os
import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

MODES = {"strict", "hint", "name"}


def normalize(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = re.sub(r"\s+", " ", s)
    return s


def core_zh(zh: str) -> str:
    """Drop parenthetical glosses for substring checks."""
    return re.split(r"[（(]", zh, maxsplit=1)[0].strip()


@dataclass
class Entry:
    en: str
    zh: str
    category: str = ""
    aliases: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    notes: str = ""
    confidence: str = "A"
    mode: str = "strict"
    source: str = ""

    @property
    def forms(self) -> list[str]:
        return [self.en] + self.aliases


@dataclass
class TermMatch:
    entry: Entry
    start: int
    end: int
    text: str


class Glossary:
    def __init__(self, entries: Iterable[Entry], path: str = ""):
        self.entries = list(entries)
        self.path = path
        self.by_form: dict[str, Entry] = {}
        for e in self.entries:
            if e.mode not in MODES:
                raise ValueError(f"bad mode {e.mode!r} for {e.en!r}")
            for form in e.forms:
                key = normalize(form)
                if not key:
                    continue
                if key in self.by_form and self.by_form[key] is not e:
                    # Keep the longest form; exact collisions are reported by validate().
                    if len(form) > len(self.by_form[key].en):
                        self.by_form[key] = e
                else:
                    self.by_form[key] = e
        self.version = self._version()
        self._regex, self._lookup = self._build_regex()

    def _version(self) -> str:
        h = hashlib.sha1()
        for e in sorted(self.entries, key=lambda x: x.en.lower()):
            h.update(("|".join([e.en, e.zh, ",".join(e.aliases), e.mode])).encode("utf-8"))
        return h.hexdigest()[:12]

    def _build_regex(self):
        pairs = []
        lookup = {}
        for e in self.entries:
            for form in e.forms:
                if not form.strip():
                    continue
                pattern = re.escape(form).replace(r"\ ", r"\s+")
                # Acronyms must match case-sensitively to avoid matching inside words.
                if form.isupper() and len(form) <= 6 and re.fullmatch(r"[A-Z0-9.]+", form):
                    pattern = f"(?-i:{pattern})"
                if re.match(r"[A-Za-z0-9]", form):
                    pattern = r"(?<![A-Za-z0-9])" + pattern
                if re.search(r"[A-Za-z0-9]$", form):
                    pattern = pattern + r"(?![A-Za-z0-9])"
                pairs.append((len(form), pattern, e))
                lookup[normalize(form)] = e
        pairs.sort(key=lambda x: -x[0])
        combined = re.compile("|".join(p for _, p, _ in pairs), re.IGNORECASE)
        return combined, lookup

    def find(self, text: str) -> list[TermMatch]:
        """Longest, non-overlapping matches."""
        found = []
        for m in self._regex.finditer(text):
            e = self._lookup.get(normalize(m.group(0)))
            if not e:
                continue
            found.append(TermMatch(e, m.start(), m.end(), m.group(0)))
        found.sort(key=lambda x: (x.start, -(x.end - x.start)))
        out = []
        last_end = -1
        for tm in found:
            if tm.start >= last_end:
                out.append(tm)
                last_end = tm.end
        return out

    def hints(self, text: str, limit: int = 40) -> list[Entry]:
        seen = set()
        out = []
        for tm in self.find(text):
            if tm.entry.en in seen:
                continue
            seen.add(tm.entry.en)
            out.append(tm.entry)
            if len(out) >= limit:
                break
        return out

    def exact(self, text: str) -> Optional[Entry]:
        return self.by_form.get(normalize(text))

    ACCEPT_VARIANTS = {
        "Stavka": ["最高统帅部", "苏军最高统帅部"],
    }

    def check(self, source: str, target: str) -> list[str]:
        """Return hard glossary violations (strict entries only)."""
        issues = []
        for tm in self.find(source):
            e = tm.entry
            if e.mode != "strict":
                continue
            accepted = [core_zh(e.zh)] + self.ACCEPT_VARIANTS.get(e.en, [])
            if not any(a and a in target for a in accepted):
                issues.append(f"术语未按表译出: {tm.text} -> 应为“{e.zh}”")
        matched = {tm.entry.en for tm in self.find(source)}
        for e in self.entries:
            if e.mode != "strict" or e.en not in matched:
                continue
            # If the approved rendering is present, a shorter forbidden string may
            # simply be a substring of it (e.g. "军" inside "集团军").
            if core_zh(e.zh) in target:
                continue
            for bad in e.forbidden:
                if bad and bad in target:
                    issues.append(f"使用了禁用译法“{bad}”（{e.en} 应为“{e.zh}”）")
        return issues

    def validate(self) -> list[str]:
        warnings = []
        forms = {}
        for e in self.entries:
            if not e.en or not e.zh:
                warnings.append(f"空字段: {e}")
            if e.mode == "strict" and e.confidence not in ("A", "B"):
                warnings.append(f"严格术语置信度偏低: {e.en} ({e.confidence})")
            for form in e.forms:
                key = normalize(form)
                if key in forms and forms[key] is not e:
                    warnings.append(f"词条冲突: {form!r} 同时属于 {forms[key].en!r} 与 {e.en!r}")
                forms[key] = e
        return warnings


def load_glossary(path: str) -> Glossary:
    entries = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            aliases = [a.strip() for a in (row.get("aliases") or "").split(";") if a.strip()]
            forbidden = [a.strip() for a in (row.get("forbidden") or "").split(";") if a.strip()]
            entries.append(Entry(
                en=(row.get("en") or "").strip(),
                zh=(row.get("zh") or "").strip(),
                category=(row.get("category") or "").strip(),
                aliases=aliases,
                forbidden=forbidden,
                notes=(row.get("notes") or "").strip(),
                confidence=(row.get("confidence") or "A").strip(),
                mode=(row.get("mode") or "strict").strip(),
                source=(row.get("source") or "").strip(),
            ))
    return Glossary(entries, path)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--glossary", default=os.path.join(os.path.dirname(__file__), "..", "glossary", "ww2_military_en_zh.csv"))
    ap.add_argument("--text", default="")
    args = ap.parse_args()
    g = load_glossary(args.glossary)
    print(f"entries={len(g.entries)} forms={len(g.by_form)} version={g.version}")
    for w in g.validate()[:20]:
        print("WARN", w)
    if args.text:
        print("matches:", [(m.text, m.entry.zh, m.start, m.end) for m in g.find(args.text)])
        print("check:", g.check(args.text, ""))
