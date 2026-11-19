#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""审计全部剧本的空军指挥部名能否在载入期保住原文（指针身份）。

背景：引擎载入剧本时把航空队/航空军名查表缓存进单位对象，「可用航空作战群」
按名字对象指针筛选（v1.10.1 实机 A/B 证实）。1.10.7 起 native 钩子在场景载入段
（w_weather.dat 之后、LockIn 之前）把名字类字符串直接返回原文，因此与剧本无关。
本脚本逐剧本核对每个指挥部名的归属：

  guard   前缀守卫（Luftflotte/Luftwaffe/Flieger 且不含 skip 词）已直接返回原文
  pinned  词典条目是恒等（值 == 键），恒等规则直接返回原文
  window  词典有译文且与键不同 -> 只能靠载入窗口；必须通过 name_like 且不超预算
  absent  词典无条目 -> 原样透传，天然安全
  unsafe  有译文但过不了 name_like（窗口兜不住）—— 必须为 0

无 Dat\\CSV 的剧本（DLC）名字在加密的 .scn 里，离线无法枚举，标为「窗口兜底」。

用法：
  python integration/audit_air_hq.py                     # 人读矩阵
  python integration/audit_air_hq.py --check             # 构建守卫：有问题退出 1
  python integration/audit_air_hq.py --json OUT          # 机器可读
游戏目录缺省取 mod/settings.local.json 的 game_path。
"""
import argparse, csv, io, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP = ('field', 'flak', 'jaeger', 'fallschirm', 'battalion', 'regiment',
        'division', 'company', 'battery', 'abteilung')
PREFIX = ('luftflotte', 'luftwaffe', 'flieger')
FORBID = set('<>%{}":\\/|=')
WINDOW_BUDGET = 200      # text_hook.c 的 load_window 初值
NAME_MAX = 72            # name_like 的长度上限


def read_text(path):
    raw = Path(path).read_bytes()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        text = raw.decode('cp1252', errors='replace')
    return text.lstrip('\ufeff')


def read_rows(path):
    return list(csv.DictReader(io.StringIO(read_text(path))))


def name_guard(name):
    low = name.lower()
    if not low.startswith(PREFIX):
        return False
    return not any(w in low for w in SKIP)


def name_like(name):
    if len(name) > NAME_MAX:
        return False
    return not any(ch in FORBID or ord(ch) < 32 for ch in name)


def classify(name, entries):
    if name_guard(name):
        return 'guard'
    if name not in entries:
        return 'absent'
    if entries[name] == name:
        return 'pinned'
    return 'window' if name_like(name) else 'unsafe'


def scenario_hq(csv_dir, scenario, generic_units):
    units = dict(generic_units)
    p = csv_dir / scenario / 'Units.csv'
    if p.exists():
        for row in read_rows(p):
            units[row['ID']] = row.get('Name', '')
    hq, aogs = set(), set()
    p = csv_dir / scenario / 'AOGs.csv'
    if p.exists():
        for row in read_rows(p):
            name = (row.get('Name') or '').strip()
            if name and not name.startswith('*'):
                aogs.add(name)
            ref = (row.get('AirHq') or '').strip()
            if ref and ref != '0' and ref in units:
                hq.add(units[ref])
    return hq, aogs


def collect(game, entries, pinned_names):
    scen_dir = game / 'Dat' / 'Scen'
    csv_dir = game / 'Dat' / 'CSV'
    generic_units = {}
    p = csv_dir / 'Generic' / 'Units.csv'
    if p.exists():
        for row in read_rows(p):
            generic_units[row['ID']] = row.get('Name', '')
    rows, problems = [], []
    for scn in sorted(scen_dir.glob('*.scn')):
        name = scn.stem
        if not (csv_dir / name).is_dir():
            rows.append({'scenario': name, 'csv': False})
            continue
        hq, aogs = scenario_hq(csv_dir, name, generic_units)
        counts = {'guard': 0, 'pinned': 0, 'window': 0, 'absent': 0, 'unsafe': 0}
        detail = []
        for h in sorted(hq):
            kind = classify(h, entries)
            counts[kind] += 1
            detail.append({'name': h, 'kind': kind,
                           'value': entries.get(h) if kind != 'absent' else None})
            if kind == 'unsafe':
                problems.append('%s: 指挥部 %r 译作 %r，过不了 name_like（窗口兜不住）'
                                % (name, h, entries.get(h)))
        aog_counts = {'guard': 0, 'pinned': 0, 'window': 0, 'absent': 0, 'unsafe': 0}
        for a in aogs:
            aog_counts[classify(a, entries)] += 1
        for kind in ('window', 'unsafe'):
            for a in sorted(x for x in aogs if classify(x, entries) == kind):
                problems.append('%s: AOG %r 的译名未钉死（%s，%r），请加入 glossary/aog_identity.json'
                                % (name, a, kind, entries.get(a)))
        rows.append({'scenario': name, 'csv': True, 'hq': len(hq), 'counts': counts,
                     'detail': detail, 'aogs': len(aogs), 'aog_counts': aog_counts,
                     'aog_names': sorted(aogs)})
    return rows, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game')
    ap.add_argument('--json')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    game = args.game
    if not game:
        local = ROOT / 'mod' / 'settings.local.json'
        if local.exists():
            game = json.loads(read_text(local)).get('game_path')
    if not game or not Path(game).is_dir():
        sys.exit('need --game DIR (or mod/settings.local.json game_path)')
    game = Path(game)
    entries = json.loads(read_text(ROOT / 'mod' / 'payload' / 'translations.json'))

    rows, problems = collect(game, entries, set())
    with_csv = [r for r in rows if r['csv']]
    without = [r for r in rows if not r['csv']]
    window_names = sorted({d['name'] for r in with_csv for d in r['detail'] if d['kind'] == 'window'})
    aog_refs = sum(r['aogs'] for r in with_csv)
    aog_union = sorted({a for r in with_csv for a in r['aog_names']})
    aog_bad = [a for a in aog_union if classify(a, entries) not in ('guard', 'pinned')]

    if args.check:
        max_win = max((r['counts']['window'] for r in with_csv), default=0)
        longest = max((len(n) for n in window_names), default=0)
        print('Air HQ guard: %d scenarios (%d with CSV, %d DLC), %d window names '
              '(max %d per scenario, budget %d; longest %d, limit %d); '
              'AOG %d refs / %d distinct, %d not pinned'
              % (len(rows), len(with_csv), len(without), len(window_names),
                 max_win, WINDOW_BUDGET, longest, NAME_MAX,
                 aog_refs, len(aog_union), len(aog_bad)))
        for p in problems:
            print('  ' + p)
        return 1 if problems else 0

    print('游戏目录:', game)
    print('剧本数: %d（有 CSV %d，无 CSV %d）' % (len(rows), len(with_csv), len(without)))
    print()
    print('| 剧本 | CSV | 指挥部 | guard | pinned | window | absent | 靠窗口的译名 |')
    print('|' + '---|' * 8)
    for r in rows:
        if not r['csv']:
            print('| %s | 无 | — | — | — | — | — | DLC：载入窗口兜底，离线不可枚举 |' % r['scenario'])
            continue
        c = r['counts']
        win = ', '.join(d['name'] for d in r['detail'] if d['kind'] == 'window')
        print('| %s | 有 | %d | %d | %d | %d | %d | %s |' % (
            r['scenario'], r['hq'], c['guard'], c['pinned'], c['window'],
            c['absent'], win or '—'))
    print()
    totals = {k: sum(r['counts'][k] for r in with_csv) for k in ('guard', 'pinned', 'window', 'absent', 'unsafe')}
    print('合计（去重前）:', ', '.join('%s %d' % (k, v) for k, v in totals.items()))
    print('需窗口的去重译名 %d 个: %s' % (len(window_names), ', '.join(window_names)))
    print('空军单位（AOG）: %d 条引用、去重 %d 名，恒等或前缀守卫 %d 名，未钉死 %d 名' % (
        aog_refs, len(aog_union), len(aog_union) - len(aog_bad), len(aog_bad)))
    print('窗口预算: 单剧本最多 %d 个（钩子 %d），最长名字 %d 字符（上限 %d）' % (
        max((r['counts']['window'] for r in with_csv), default=0), WINDOW_BUDGET,
        max((len(n) for n in window_names), default=0), NAME_MAX))
    if problems:
        print('问题 %d 条:' % len(problems))
        for p in problems:
            print('  -', p)
    else:
        print('结论: 有 CSV 的剧本每个指挥部都有确定归属，unsafe = 0。')
    if args.json:
        Path(args.json).write_text(json.dumps(
            {'game': str(game), 'rows': rows, 'problems': problems,
             'window_names': window_names, 'aog_refs': aog_refs,
             'aog_union': aog_union}, ensure_ascii=False, indent=1), encoding='utf-8')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
