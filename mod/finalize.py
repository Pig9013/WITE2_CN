"""Finalize integrity metadata and offline-only launcher configuration."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
(root / 'logs').mkdir(exist_ok=True)

dict_path = root / 'payload' / 'translations.json'
entries = json.loads(dict_path.read_text(encoding='utf8'))

# --- 片段键守卫：纯数字 / 序数 / 罗马数字不得进词典（会污染表格数字列） ---
import re as _re

fragment = [k for k in entries
            if _re.fullmatch(r'\d+', k)
            or _re.fullmatch(r'\d+(st|nd|rd|th)', k, _re.I)
            or _re.fullmatch(r'[IVXLC]+', k)]
if fragment:
    raise SystemExit('refuse: %d fragment key(s) in dictionary, e.g. %r' % (len(fragment), fragment[:5]))
print('Fragment-key guard: OK')

# --- 国籍守卫：无国籍的兵种后缀键不得译出国籍 ---
# 兵种后缀是全局共用字符串：'Infantry Division' 一旦译成'罗马尼亚步兵师'，
# 所有用该后缀拼名的部队都会变成罗马尼亚步兵师（v1.3.0 的'保加利亚步兵师'同源）。
TYPE_TAIL = _re.compile(r'(Division|Brigade|Regiment|Battalion|Corps|Army|Company|Battery|Flotilla|Detachment|Group)$', _re.I)
NAT_STEM = _re.compile(
    r'\b(Rum\w*|Roman\w*|Hun\w*|Hung\w*|Ital\w*|Fin\w*|Finn\w*|Bul\w*|Bulg\w*|'
    r'Slov\w*|Croat\w*|Yug\w*|Span\w*|Ger\w*|Sov\w*|Soviet\w*|Rus\w*|Russian\w*|'
    r'Blue|RSI)\b', _re.I)
NAT_CODE = _re.compile(r'\b(US|BR|CA|AU|AUS|SA|NZ|IN|PO|FF|BZ|SS)\b')
NAT_IN_VALUE = ('罗马尼亚', '匈牙利', '意大利', '芬兰', '保加利亚',
                '斯洛伐克', '克罗地亚', '南斯拉夫', '西班牙', '德国', '苏联')

poisoned = []
for key, value in entries.items():
    if not isinstance(value, str) or len(key) > 45 or len(key.split()) > 6:
        continue
    if any(ch in key for ch in ',.;<>'):
        continue
    if not TYPE_TAIL.search(key.strip()) or NAT_STEM.search(key) or NAT_CODE.search(key):
        continue
    hit = [n for n in NAT_IN_VALUE if n in value]
    if hit:
        poisoned.append((key, value, hit[0]))
if poisoned:
    for key, value, nat in poisoned[:10]:
        print('  POISONED %r => %r (%s)' % (key, value, nat))
    raise SystemExit('refuse: %d nationality-poisoned type key(s); '
                     'a shared suffix must not carry a nationality' % len(poisoned))
print('Nationality guard: OK')

files = [root / 'WitE2CN_Text.dll'] + [
    p for p in (root / 'payload').rglob('*')
    if p.is_file() and p.name not in ('checksums.json', 'compat.json')]
checksums = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
(root / 'payload' / 'checksums.json').write_text(json.dumps(checksums, indent=2), encoding='utf8')
(root / 'settings.json').write_text('{}\n', encoding='utf8')
print('Integrity metadata:', len(checksums), 'files')
