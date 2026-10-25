#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Offline translation pipeline for War in the East 2 text.

Examples:
  python translate_wite2.py scan --input ..\data\extracted\scenarios.jsonl
  python translate_wite2.py translate --input ..\data\extracted\scenarios.jsonl --out ..\data\translations\scenarios.zh.jsonl --limit 2
  python translate_wite2.py translate --input units.csv --out units.zh.csv --text-cols name,caption
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Iterable, Optional

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from glossary import Glossary, load_glossary  # noqa: E402
from llm_client import ChatClient, LLMConfig, LLMError  # noqa: E402
from name_rules import translate_unit_name  # noqa: E402
from prompts import build_batch_messages, build_messages, build_retry_messages  # noqa: E402
from protect import protect, restore  # noqa: E402
from qa import check_pair, is_blocking, summarize  # noqa: E402
from tm import TM  # noqa: E402

log = logging.getLogger("wite2")

DEFAULT_CONFIG = {
    "provider": "openai",
    "base_url": "http://127.0.0.1:1234/v1",
    "model": "qwen2.5-14b-instruct",
    "api_key": "lm-studio",
    "temperature": 0.1,
    "top_p": 0.9,
    "max_tokens": 2048,
    "timeout": 180,
    "retries": 3,
    "num_ctx": 8192,
    "glossary": "glossary/ww2_military_en_zh.csv",
    "tm": "data/translations/tm.sqlite",
    "max_chunk_chars": 1800,
    "batch_size": 1,
    "strict": True,
}

HARD_CODES = {"empty", "placeholder", "llm_error", "no_llm", "no_cjk"}

KIND_MAP = {
    "unit_name": "unit_name",
    "airgroup_name": "airgroup_name",
    "leader_name": "leader_name",
    "scenario_text": "scenario",
    "exe_ui": "exe_ui",
}


def load_config(path: str) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig") as f:
            cfg.update(json.load(f))
    for key in ("glossary", "tm"):
        p = cfg.get(key, "")
        if p and not os.path.isabs(p):
            cfg[key] = str((ROOT / p).resolve())
    return cfg


def has_letters(s: str) -> bool:
    return len(re.findall(r"[A-Za-z]", s)) >= 2


def as_kind(raw: str) -> str:
    if raw in KIND_MAP:
        return KIND_MAP[raw]
    if raw.endswith("_description"):
        return "description"
    if raw.endswith("_caption"):
        return "caption"
    if raw.endswith("_name"):
        return "unit_name"
    return raw or "description"


def split_chunks(text: str, max_chars: int = 1800) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts = re.split(r"(<cr>|\n\s*\n)", text)
    chunks: list[str] = []
    cur = ""
    for part in parts:
        if not part:
            continue
        # Never merge across a blank-line boundary; keep the separator as its
        # own untranslated chunk so paragraph layout survives.
        if re.fullmatch(r"\n\s*\n", part):
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(part)
            continue
        if cur and len(cur) + len(part) > max_chars:
            chunks.append(cur)
            cur = part
        else:
            cur += part
    if cur:
        chunks.append(cur)
    # Hard-split any remaining oversized chunk on sentence boundaries.
    out = []
    for ch in chunks:
        if len(ch) <= max_chars:
            out.append(ch)
            continue
        sentences = re.split(r"(?<=[.!?;:])\s+", ch)
        buf = ""
        for s in sentences:
            if buf and len(buf) + len(s) > max_chars:
                out.append(buf)
                buf = s
            else:
                buf += ("" if not buf else " ") + s
        if buf:
            out.append(buf)
    return out or [text]


def sanitize_markup(source: str, target: str) -> str:
    """Drop decorative tags the model invented, but keep tags present in source."""
    for tag in ("<b>", "</b>", "<i>", "</i>", "<u>", "</u>",
                "<strong>", "</strong>", "<em>", "</em>", "<br>", "<br/>", "<br />",
                "[b]", "[/b]", "[i]", "[/i]"):
        if tag.lower() not in source.lower():
            target = re.sub(re.escape(tag), "", target, flags=re.I)
    # Remove placeholder-looking artifacts the model invented. Descriptions in
    # the game data do not use printf/brace placeholders.
    for pat in (r"%[-+ 0#]*\d*(?:\.\d+)?[sdifuxXc]", r"\{[^{}\n]{1,80}\}",
                r"</?div[^>]*>", r"\[@PH[^\]]*\]"):
        for m in list(re.finditer(pat, target, flags=re.I)):
            if m.group(0).lower() not in source.lower():
                target = target.replace(m.group(0), "")
    return target


class Translator:
    def __init__(self, cfg: dict, glossary: Glossary, tm: TM, client: Optional[ChatClient] = None):
        self.cfg = cfg
        self.glossary = glossary
        self.tm = tm
        self.model = cfg["model"]
        self.max_chunk = int(cfg.get("max_chunk_chars", 1800))
        self.strip_chars = bool(cfg.get("strict", True))
        self.fail_closed = bool(cfg.get("fail_closed", True))
        if client is None and cfg.get("provider") != "none":
            client = ChatClient(LLMConfig.from_dict(cfg))
        self.client = client

    def _cache_key(self, source: str, kind: str) -> str:
        return TM.make_key(self.model, self.glossary.version, source, kind)

    def translate(self, source: str, kind: str = "description", context: str = "",
                  max_len: Optional[int] = None) -> tuple[str, list[dict], str]:
        src = source.strip()
        if not src or not has_letters(src):
            return source, [], "kept"

        if kind in ("unit_name", "airgroup_name"):
            name = translate_unit_name(src)
            if name:
                return name, [], "ok"
        if kind == "leader_name":
            return source, [], "kept"

        if kind in ("exe_ui", "caption") and len(src.split()) <= 6:
            entry = self.glossary.exact(src)
            if entry:
                return entry.zh, [], "ok"

        key = self._cache_key(src, kind)
        cached = self.tm.get(key)
        if cached and not self.cfg.get("force"):
            return cached["target"], cached.get("issues", []), "cached"

        if len(src) > self.max_chunk and kind in ("description", "scenario", "event"):
            target, issues = self._translate_long(src, kind, context, max_len)
        else:
            target, issues = self._translate_chunk(src, kind, context, max_len)

        blocking = is_blocking(issues)
        if blocking:
            hard = any(i.get("code") in HARD_CODES for i in issues)
            if hard or self.fail_closed:
                self.tm.put(key, src, source, self.model, self.glossary.version, kind, "blocked", issues)
                return source, issues, "blocked"
            self.tm.put(key, src, target, self.model, self.glossary.version, kind, "review", issues)
            return target, issues, "review"
        self.tm.put(key, src, target, self.model, self.glossary.version, kind, "ok", issues)
        return target, issues, "ok"

    def _translate_long(self, source: str, kind: str, context: str, max_len: Optional[int]) -> tuple[str, list[dict]]:
        chunks = split_chunks(source, self.max_chunk)
        outs = []
        all_issues = []
        for ch in chunks:
            if not has_letters(ch):
                outs.append(ch)
                continue
            t, issues = self._translate_chunk(ch, kind, context, None)
            outs.append(t)
            all_issues.extend(issues)
        target = "".join(outs)
        final_issues = check_pair(source, target, self.glossary, max_len, kind)
        return target, final_issues

    def _translate_chunk(self, source: str, kind: str, context: str, max_len: Optional[int]) -> tuple[str, list[dict]]:
        protected = protect(source)
        hints = self.glossary.hints(source)
        messages = build_messages(protected.masked, context, hints, kind, max_len)
        target = source
        issues: list[dict] = []
        for attempt in range(2):
            if self.client is None:
                return source, [{"code": "no_llm", "severity": "error", "message": "未配置 LLM"}]
            try:
                raw = self.client.chat(messages)
            except LLMError as e:
                issues = [{"code": "llm_error", "severity": "error", "message": str(e)}]
                break
            target = restore(protected, raw)
            target = re.sub(r"@@PH\\d+@@", "", target)
            if kind in ("description", "scenario", "event"):
                target = sanitize_markup(source, target)
            issues = check_pair(source, target, self.glossary, max_len, kind)
            if not is_blocking(issues):
                break
            if attempt == 0:
                messages = build_retry_messages(
                    protected.masked, raw, [i["message"] for i in issues if i["severity"] == "error"],
                    context, hints, kind, max_len,
                )
        return target, issues


# ---------------- input / output ----------------


def read_jsonl(path: str) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def translate_jsonl(args, cfg, tr: Translator):
    rows = read_jsonl(args.input)
    if args.kinds:
        allowed = {k.strip() for k in args.kinds.split(",")}
        rows = [r for r in rows if r.get("kind") in allowed]
    if args.limit:
        rows = rows[: args.limit]
    out_path = args.out or str(Path(args.input).with_suffix(".zh.jsonl"))
    qa_path = str(Path(out_path).with_suffix(".qa.jsonl"))
    start = time.time()
    done = 0
    stats = {"ok": 0, "blocked": 0, "cached": 0, "kept": 0}
    with open(out_path, "w", encoding="utf-8", newline="\n") as fo, \
         open(qa_path, "w", encoding="utf-8", newline="\n") as fq:
        for r in rows:
            kind = as_kind(r.get("kind", ""))
            target, issues, status = tr.translate(
                r.get("text", ""), kind, r.get("context", ""), r.get("max_len"),
            )
            rec = dict(r)
            rec["translation"] = target
            rec["qa_status"] = status
            fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fq.write(json.dumps({**rec, "issues": issues}, ensure_ascii=False) + "\n")
            stats[status] = stats.get(status, 0) + 1
            done += 1
            if done % 10 == 0:
                elapsed = max(0.1, time.time() - start)
                log.info("progress %d/%d (%.1f/s) %s", done, len(rows), done / elapsed, stats)
    log.info("done %d -> %s; %s", done, out_path, stats)
    return stats


def detect_text_columns(header: list[str], rows: list[dict]) -> list[str]:
    good = re.compile(r"(name|text|caption|description|title|message|event|label|tooltip|briefing|note|remark|comment)", re.I)
    bad = re.compile(r"^(id|nat|image|date|turn|year|month|day|x|y|lat|lon|num|number|value|size|length|width|height)$", re.I)
    cols = []
    for h in header:
        if bad.search(h.strip()):
            continue
        if good.search(h):
            vals = [str(r.get(h, "")) for r in rows[:50]]
            if any(has_letters(v) for v in vals):
                cols.append(h)
    if cols:
        return cols
    # Fallback: any column with mostly alphabetic values.
    for h in header:
        vals = [str(r.get(h, "")) for r in rows[:50] if str(r.get(h, "")).strip()]
        if vals and sum(1 for v in vals if has_letters(v)) / len(vals) >= 0.6:
            cols.append(h)
    return cols


def read_csv_table(path: str):
    with open(path, "rb") as f:
        raw = f.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig", "replace")
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
    except Exception:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    header = reader.fieldnames or []
    rows = list(reader)
    return header, rows, bom, dialect


def translate_csv(args, cfg, tr: Translator):
    header, rows, bom, dialect = read_csv_table(args.input)
    if not header:
        raise SystemExit("CSV has no header")
    cols = [c.strip() for c in args.text_cols.split(",")] if args.text_cols else detect_text_columns(header, rows)
    if not cols:
        raise SystemExit("no text columns detected; pass --text-cols")
    for c in cols:
        if c not in header:
            raise SystemExit(f"column not found: {c}")
    if args.limit:
        rows = rows[: args.limit]
    out_path = args.out or str(Path(args.input).with_suffix(".zh.csv"))
    qa_path = str(Path(out_path).with_suffix(".qa.csv"))
    stats = {"ok": 0, "blocked": 0, "cached": 0, "kept": 0}
    qa_rows = []
    start = time.time()
    done = 0
    for i, row in enumerate(rows):
        for col in cols:
            src = row.get(col, "") or ""
            target, issues, status = tr.translate(src, args.kind or "description", f"row {i} col {col}")
            row[col] = target
            stats[status] = stats.get(status, 0) + 1
            if issues or status == "blocked":
                qa_rows.append({"row": i, "column": col, "source": src, "target": target,
                                "status": status, "issues": summarize(issues)})
            done += 1
            if done % 20 == 0:
                log.info("progress %d cells (%.1f/s) %s", done, done / max(0.1, time.time() - start), stats)
    with open(out_path, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, dialect=dialect)
        w.writeheader()
        w.writerows(rows)
    with open(qa_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["row", "column", "source", "target", "status", "issues"])
        w.writeheader()
        w.writerows(qa_rows)
    log.info("done %d cells -> %s; %s", done, out_path, stats)
    return stats


def translate_txt(args, cfg, tr: Translator):
    text = open(args.input, "r", encoding="utf-8-sig", errors="replace").read()
    target, issues, status = tr.translate(text, args.kind or "scenario", args.input)
    out_path = args.out or str(Path(args.input).with_suffix(".zh.txt"))
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(target)
    log.info("done -> %s (%s, %s)", out_path, status, summarize(issues))
    return {status: 1}


def scan(args, cfg):
    p = args.input
    suffix = Path(p).suffix.lower()
    if suffix == ".jsonl":
        rows = read_jsonl(p)
        from collections import Counter
        kinds = Counter(r.get("kind", "") for r in rows)
        chars = sum(len(r.get("text", "")) for r in rows)
        print(json.dumps({"file": p, "records": len(rows), "kinds": kinds, "chars": chars,
                          "unique_texts": len({r.get("text", "") for r in rows})}, ensure_ascii=False, indent=2))
    elif suffix == ".csv":
        header, rows, bom, dialect = read_csv_table(p)
        cols = detect_text_columns(header, rows)
        print(json.dumps({"file": p, "rows": len(rows), "columns": header,
                          "text_columns": cols, "delimiter": dialect.delimiter, "bom": bom}, ensure_ascii=False, indent=2))
    else:
        text = open(p, "r", encoding="utf-8-sig", errors="replace").read()
        print(json.dumps({"file": p, "chars": len(text), "lines": text.count("\n") + 1}, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(HERE / "config.json"))
    ap.add_argument("--quiet", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sc = sub.add_parser("scan")
    sc.add_argument("--input", required=True)

    tr = sub.add_parser("translate")
    tr.add_argument("--input", required=True)
    tr.add_argument("--out", default="")
    tr.add_argument("--text-cols", default="")
    tr.add_argument("--kind", default="")
    tr.add_argument("--kinds", default="")
    tr.add_argument("--limit", type=int, default=0)
    tr.add_argument("--force", action="store_true")
    tr.add_argument("--soft", action="store_true",
                    help="keep translations with review warnings instead of falling back to English")

    args = ap.parse_args()
    logging.basicConfig(level=logging.WARNING if args.quiet else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config(args.config)
    if args.cmd == "scan":
        scan(args, cfg)
        return

    glossary = load_glossary(cfg["glossary"])
    tm = TM(cfg["tm"])
    client = None if cfg.get("provider") == "none" else ChatClient(LLMConfig.from_dict(cfg))
    if client:
        try:
            client.health()
        except Exception as e:
            raise SystemExit(f"LLM server not reachable at {cfg['base_url']}: {e}")
    args.force = getattr(args, "force", False)
    cfg["force"] = args.force
    if getattr(args, "soft", False):
        cfg["fail_closed"] = False
    tr = Translator(cfg, glossary, tm, client)

    suffix = Path(args.input).suffix.lower()
    if suffix == ".jsonl":
        translate_jsonl(args, cfg, tr)
    elif suffix == ".csv":
        translate_csv(args, cfg, tr)
    else:
        translate_txt(args, cfg, tr)


if __name__ == "__main__":
    main()
