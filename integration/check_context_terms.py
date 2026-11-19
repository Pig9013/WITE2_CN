#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语境术语守卫：锁定玩家高频界面的定译，防止大小写变体/批量复用把已修好的译法改回去。

背景（v1.10.6）：v1.6.3 用「大小写/标点归一」批量复用旧译，给同一句英文的不同大小写
各建了一条键。后来人工只改了大写键（reference_overrides / ui_extra.csv），小写变体
仍是旧错译；界面一旦查小写，玩家看到的就是「行政点伤害」「非俄罗斯部队」这类东西。
本脚本把「必须一致的成对键」和「绝不能出现的旧值」写成可执行断言。

用法：
  python integration/check_context_terms.py --check     构建期调用，失败退出码 1
  python integration/check_context_terms.py --report    只打印现状，不判失败
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TERMS = ROOT / 'glossary' / 'context_terms.json'
DICT = ROOT / 'mod' / 'payload' / 'translations.json'


def load_dict():
    data = json.loads(DICT.read_text(encoding='utf-8'))
    if isinstance(data, dict) and 'entries' in data:
        data = data['entries']
    return {k: v for k, v in data.items() if isinstance(v, str)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--report', action='store_true')
    args = ap.parse_args()
    check = args.check and not args.report

    spec = json.loads(TERMS.read_text(encoding='utf-8'))
    entries = load_dict()
    errors = []
    checked = 0

    allowed = set()
    for a, b in spec.get('allow_divergence', {}).get('pairs', []):
        allowed.add((a, b))
        allowed.add((b, a))

    for gname, group in spec['groups'].items():
        for key, want in group['terms'].items():
            checked += 1
            got = entries.get(key)
            if got is None:
                errors.append('缺键 %s（应译「%s」）' % (key, want))
            elif got != want:
                errors.append('%s：「%s」应为「%s」' % (key, got, want))
            if not group.get('check_case_variants'):
                continue
            for sib in {key.lower(), key.upper()}:
                if sib == key or sib not in entries:
                    continue
                if entries[sib] != want and (key, sib) not in allowed:
                    errors.append('大小写变体不一致 %s=「%s」/ %s=「%s」（应同为「%s」）'
                                  % (key, want, sib, entries[sib], want))

    for bad, why in spec.get('banned_values', {}).items():
        hits = [k for k, v in entries.items() if v == bad]
        if hits:
            errors.append('禁用旧译「%s」仍出现在 %d 个键：%s（%s）'
                          % (bad, len(hits), ', '.join(repr(h) for h in hits[:5]), why))

    csv_checked = 0
    for group in spec['groups'].values():
        for rule in group.get('csv_rows', []):
            for path in sorted(ROOT.glob(rule['glob'])):
                with path.open(encoding='utf-8-sig', newline='') as fh:
                    for row in csv.DictReader(fh):
                        if all(row.get(k) == v for k, v in rule['match'].items()):
                            csv_checked += 1
                            got = row.get(rule['column'])
                            if got != rule['expect']:
                                errors.append('%s：%s=「%s」应为「%s」（%s）'
                                              % (path.relative_to(ROOT), rule['column'],
                                                 got, rule['expect'], rule['why']))

    print('Context-term guard: %d 条术语、%d 行剧本 CSV' % (checked, csv_checked))
    if errors:
        for e in errors:
            print('  ✗ ' + e)
        if check:
            print('refuse: 语境术语与定译不一致（glossary/context_terms.json）')
            return 1
        return 0
    print('  全部一致')
    return 0


if __name__ == '__main__':
    sys.exit(main())
