#!/usr/bin/env python3
"""生成 glossary/aog_identity.json —— 航空作战群（AOG）名字的「不译」清单。

为什么需要这张表：引擎在载入场景时就把 AOG 名字交给本地化查表函数并缓存进对象，
而「空中指令设置」面板做可用性筛选时，拿的是航空队（Unit）的原始英文名去比对。
AOG 名字一旦被译成中文，两边永远不相等，筛选结果就是 0 行 —— 2026-11-19 的
「可用航空作战群列表为空」即此。译文必须与引擎内部标识符一致，故 AOG 名字只能
保持原文；清单从各想定的 Dat\\CSV\\<scenario>\\AOGs.csv 的 Name 列生成。

用法：python integration\\gen_aog_identity.py [--game PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
MOD = PROJECT / 'mod'
OUT = PROJECT / 'glossary' / 'aog_identity.json'


def resolve_game(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get('WITE2_GAME')
    if env:
        return Path(env)
    settings = MOD / 'settings.json'
    if settings.exists():
        try:
            value = json.loads(settings.read_text(encoding='utf-8')).get('game_path')
            if value:
                return Path(value)
        except Exception:
            pass
    raise SystemExit('找不到游戏目录；请用 --game 指定，或设置环境变量 WITE2_GAME。')


def read_names(path: Path) -> list[str]:
    raw = path.read_bytes()
    for enc in ('utf-8-sig', 'cp1252'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return []
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    if 'Name' not in header:
        return []
    idx = header.index('Name')
    names = []
    for row in rows[1:]:
        if len(row) <= idx:
            continue
        name = row[idx].strip()
        if not name or name.startswith('*'):
            continue   # 分组表头行（**** Germany *****）不参与比对，保留中文
        names.append(name)
    return names


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--game')
    args = parser.parse_args()
    game = resolve_game(args.game)
    files = sorted((game / 'Dat' / 'CSV').glob('*/AOGs.csv'))
    if not files:
        raise SystemExit('没有找到 Dat\\CSV\\*\\AOGs.csv：%s' % game)
    names: set[str] = set()
    for path in files:
        names.update(read_names(path))
    data = {
        '_meta': {
            'purpose': 'AOG 名字必须与引擎内部标识符一致，不能翻译；本表由 integration/gen_aog_identity.py 生成',
            'generated_from': 'Dat/CSV/<scenario>/AOGs.csv Name 列（排除 **** 分组表头行）',
            'scenarios': len(files),
            'count': len(names),
        },
        'names': sorted(names),
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('AOG names: %d from %d scenario AOGs.csv -> %s' % (len(names), len(files), OUT))


if __name__ == '__main__':
    main()
