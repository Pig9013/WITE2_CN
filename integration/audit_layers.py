# -*- coding: utf-8 -*-
"""审计译名分层：同一英文串在 jsonl / 场景 CSV / 覆盖层 里是否被写成不同值。

用法：
    python integration/audit_layers.py            # 生成 audit/layer-conflicts.json，打印摘要
    python integration/audit_layers.py --check    # 有未登记的冲突则 exit 2（构建链用）

判定：
    * override_vs_lower  覆盖层最后套用，若与 jsonl/CSV 的值不同，等于悄悄压掉下游修订
                         —— 这是「只修了一个层」导致实际没生效的那一类，--check 硬失败。
    * lower_multi        jsonl 与 CSV（或不同 jsonl 文件）之间同一键有多个值
                         —— 多为不同语境，仅供人工排期，--check 不失败。
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data" / "scenario_csv" / "translations"
CSVDIR = PROJECT / "build" / "scenario_csv_zh"
OVERRIDES = PROJECT / "glossary" / "master_overrides.json"
ALLOW = PROJECT / "glossary" / "layer_allow.json"
OUT = PROJECT / "audit" / "layer-conflicts.json"


def game_csv_root() -> Path | None:
    for name in ("settings.local.json", "settings.json"):
        p = PROJECT / "mod" / name
        if not p.exists():
            continue
        try:
            cfg = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for key in ("game_path", "install_path", "game_dir", "wite2_path"):
            if cfg.get(key):
                return Path(cfg[key]) / "Dat" / "CSV"
    return None


def add(layer: dict, key: str, value: str, where: str) -> None:
    if not key or not value or key == value:
        return
    layer.setdefault(key, {}).setdefault(value, set()).add(where)


def load_jsonl(layer: dict) -> None:
    for p in sorted(DATA.glob("*.zh.jsonl")):
        if p.name.endswith(".qa.jsonl"):
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            add(layer, o.get("text"), o.get("translation"), p.name)


def load_csv(layer: dict) -> None:
    root = game_csv_root()
    if root is None:
        return
    for zh in sorted(CSVDIR.glob("*/*.zh.csv")):
        orig = root / zh.parent.name / (zh.name[:-7] + ".csv")
        if not orig.exists():
            continue
        try:
            srows = list(csv.reader(orig.read_text(encoding="utf-8-sig").splitlines()))
            zrows = list(csv.reader(zh.read_text(encoding="utf-8-sig").splitlines()))
        except Exception:
            continue
        for s, z in zip(srows[1:], zrows[1:]):
            for a, b in zip(s, z):
                if a and b and a != b:
                    add(layer, a, b, zh.name)


def load_overrides() -> dict:
    if not OVERRIDES.exists():
        return {}
    return json.loads(OVERRIDES.read_text(encoding="utf-8"))


def load_allow() -> set:
    if not ALLOW.exists():
        return set()
    try:
        return set(json.loads(ALLOW.read_text(encoding="utf-8")).get("keys", []))
    except Exception:
        return set()


def main() -> int:
    check = "--check" in sys.argv
    jsonl, csv_layer = {}, {}
    load_jsonl(jsonl)
    load_csv(csv_layer)
    ov = load_overrides()
    allow = load_allow()

    conflicts = []
    for key, value in ov.items():
        lower = {}
        lower.update({v: sorted(w) for v, w in jsonl.get(key, {}).items()})
        for v, w in csv_layer.get(key, {}).items():
            lower.setdefault(v, []).extend(sorted(w))
        if not lower:
            continue
        if value in lower:
            continue
        conflicts.append({
            "key": key,
            "kind": "override_vs_lower",
            "override": value,
            "lower": lower,
        })
    for key in set(jsonl) | set(csv_layer):
        if key in ov:
            continue
        values = {}
        values.update({v: sorted(w) for v, w in jsonl.get(key, {}).items()})
        for v, w in csv_layer.get(key, {}).items():
            values.setdefault(v, []).extend(sorted(w))
        if len(values) > 1:
            conflicts.append({"key": key, "kind": "lower_multi", "values": values})

    hard = [c for c in conflicts if c["kind"] == "override_vs_lower" and c["key"] not in allow]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "counts": {
            "override_vs_lower": sum(1 for c in conflicts if c["kind"] == "override_vs_lower"),
            "lower_multi": sum(1 for c in conflicts if c["kind"] == "lower_multi"),
            "allowlisted": len(allow),
        },
        "conflicts": sorted(conflicts, key=lambda c: (c["kind"], c["key"])),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    n_ov = sum(1 for c in conflicts if c["kind"] == "override_vs_lower")
    n_multi = sum(1 for c in conflicts if c["kind"] == "lower_multi")
    print(f"Layer audit: override-vs-lower {n_ov}, lower-multi {n_multi} -> {OUT.relative_to(PROJECT)}")
    if check and hard:
        print(f"Layer guard: FAIL ({len(hard)} un-unified key(s))")
        for c in hard[:10]:
            print(f"  - {c['key']}: override={c['override']!r} lower={list(c['lower'])!r}")
        return 2
    print(f"Layer guard: OK ({n_ov} override conflicts, {len(allow)} allowlisted)")

    # --- Staffel/Gruppe 守卫（v1.9.10）---
    # N./JG 51 是中队、I./JG 51 是大队；场景表若把阿拉伯 Staffel 也写成「大队」，
    # 中文化后两支部队撞名。判据与修复都在 integration/fix_airgroup_staffel.py。
    fixer = PROJECT / "integration" / "fix_airgroup_staffel.py"
    if fixer.exists():
        import subprocess
        r = subprocess.run([sys.executable, str(fixer), "--check"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        for line in (r.stdout or "").splitlines():
            if line.strip():
                print(line.strip())
        if r.returncode != 0:
            print("Staffel guard: FAIL (阿拉伯数字 Staffel 被译成「大队」，跑 python integration/fix_airgroup_staffel.py)")
            if check:
                return 2
        else:
            print("Staffel guard: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
