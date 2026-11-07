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

# --- 美术路径守卫：地形/图块/美术目录名一旦进词典，引擎按中文名拼资源路径必失败 ---
# v1.6.5 的黑格事故：CLEAR→晴朗 让 //Tiles//CLEAR//CLEAR_001.tga 变成不存在；
# 2026-11-06 的小河事故：MINOR//→次要 让 //Tiles//RIVER//MINOR//R0_001.tga 失效。
# 键清单由 mod/scan_art_tokens.py 扫描 Dat\Art 生成，改美术目录后需重跑。
art_tokens_path = root.parent / 'glossary' / 'art_tokens.json'
if not art_tokens_path.exists():
    raise SystemExit('缺少 glossary/art_tokens.json；先跑 python mod/scan_art_tokens.py')
art_tokens = json.loads(art_tokens_path.read_text(encoding='utf8'))
self_named_dirs = set(art_tokens['self_named_tile_dirs'])
path_tokens = set(art_tokens['path_tokens'])
TOKEN_SHAPE = _re.compile(r'^[A-Za-z0-9_./]+$')
art_bad = []
for key, value in entries.items():
    if key in self_named_dirs or key in path_tokens:
        art_bad.append((key, value, 'tile-dir or path token'))
    elif '//' in key and TOKEN_SHAPE.fullmatch(key):
        art_bad.append((key, value, 'looks like a resource path'))
if art_bad:
    for key, value, why in art_bad[:10]:
        print('  ART-TOKEN %r => %r (%s)' % (key, value, why))
    raise SystemExit('refuse: %d art/path token key(s) in dictionary' % len(art_bad))
kept = sorted(k for k in entries if k in set(art_tokens['tile_dirs']))
if kept:
    print('Art-dir keys kept (template hardcodes the name):', ', '.join(kept[:15]))
print('Art-path guard: OK (%d self-named dirs, %d path tokens)' % (len(self_named_dirs), len(path_tokens)))

# --- 译名脏值守卫：翻译过程残留一旦进词典就直接上屏 ---
# v1.9.10 实例：Debden→德宾dden（地名保留英文，避免不准确的音译）、
# Harrowbeer→哈罗贝尔回车符 / 哈罗贝尔回答问题时，请注意…、
# Fin. Air Base→结束。机场（Fin.=芬兰被当成 finish）、HQ Hun.→司令部霍恩。（Hun.=匈牙利被当成 Horn）。
# 判据只认「翻译过程话术」与「句读开头的脏值」，不碰正常译文；修复工具
# integration/fix_name_artifacts.py 会同时清 jsonl 语料层与场景 CSV 显示层。
ARTIFACT_PAT = _re.compile(r'最终译文|不在翻译范围|请注意|回答问题时|保留英文|避免不准确|回车符|换行符|hya ')
LEAD_PUNCT = _re.compile(r'^[。，、]|^\.[\u4e00-\u9fff]')  # .50英寸 是口径，不是脏值；.机枪营 才是
dirty = [(k, v) for k, v in entries.items()
         if isinstance(v, str) and (ARTIFACT_PAT.search(v) or LEAD_PUNCT.search(v))]
if dirty:
    for key, value in dirty[:10]:
        print('  NAME-ARTIFACT %r => %r' % (key, value))
    raise SystemExit('refuse: %d 条译名含翻译过程残留/元话语' % len(dirty))
print('Name-artifact guard: OK')
# --- 搁置清单守卫：清单里的键必须真的不在词典，否则「搁置=显示英文」失效 ---
pending_path = root.parent / 'glossary' / 'pending_sources.json'
if pending_path.exists():
    pending_keys = json.loads(pending_path.read_text(encoding='utf8')).get('keys', [])
    leaked = sorted(k for k in pending_keys if k in entries)
    if leaked:
        raise SystemExit('refuse: %d shelved key(s) still translated, e.g. %r' % (len(leaked), leaked[:5]))
    print('Pending-source guard: OK (%d shelved)' % len(pending_keys))

# --- 分层守卫：同一键在 jsonl / 场景 CSV / 覆盖层必须只有一个译文 ---
# v1.9.9 血案：覆盖层最后套用，压掉了设备表的新译名；只改一层时游戏里看不到变化。
# 检查交给 integration/audit_layers.py（它是分层一致性的唯一判据）。
import subprocess as _sp
import sys as _sys
_audit = root.parent / 'integration' / 'audit_layers.py'
if _audit.exists() and (root / 'settings.local.json').exists():
    _r = _sp.run([_sys.executable, str(_audit), '--check'], capture_output=True, text=True,
                 encoding='utf-8', errors='replace')
    for _line in (_r.stdout or '').splitlines():
        if _line.strip():
            print(_line.strip())
    if _r.returncode != 0:
        raise SystemExit('refuse: 分层一致性检查未通过（python integration/audit_layers.py 查详情）')

# --- 脏译名两层同步守卫：jsonl 与场景 CSV 任一残留都算失败 ---
_fixna = root.parent / 'integration' / 'fix_name_artifacts.py'
if _fixna.exists():
    _r2 = _sp.run([_sys.executable, str(_fixna), '--check'], capture_output=True, text=True,
                  encoding='utf-8', errors='replace')
    for _line in (_r2.stdout or '').splitlines():
        if _line.strip():
            print(_line.strip())
    if _r2.returncode != 0:
        raise SystemExit('refuse: 译名脏值未清（python integration/fix_name_artifacts.py 修）')

# --- 表头行守卫：*** NAME (n) *** 是列表分组行，星号/换行被破坏会让分组标题乱版 ---
# v1.9.9 实例：*** France (27)*** 被译成三行（'***\n法国 (27)\n***'），
# *** BELGIUM (9)*** 变成 '比 利 时 (9)'（星号丢失 + 字间空格）。
# 判据与**键本身的装饰形状**对齐：键以 N 个星号开头 → 译文开头也得有 ≥3 个；
# 键以星号结尾 → 译文结尾也得有 ≥3 个。数量不必相等（引擎只当文本显示），
# 但没有星号就等于丢掉了分组视觉分隔。修复工具：integration/fix_section_headers.py
STAR_LEAD = _re.compile(r'^\*+')
STAR_TAIL = _re.compile(r'\*+$')

def _star_runs(text):
    s = text.strip()
    lead = len(STAR_LEAD.match(s).group(0)) if STAR_LEAD.match(s) else 0
    trail = len(STAR_TAIL.search(s).group(0)) if STAR_TAIL.search(s) else 0
    return lead, trail

header_newline, header_unbalanced = [], []
for key, value in entries.items():
    if not isinstance(value, str):
        continue
    key_lead, key_trail = _star_runs(key)
    if key_lead < 3:
        continue
    if '\n' in value or '\r' in value:
        header_newline.append((key, value))
        continue
    val_lead, val_trail = _star_runs(value)
    if val_lead < 3 or (key_trail >= 3 and val_trail < 3):
        header_unbalanced.append((key, value))
if header_newline:
    for key, value in header_newline[:10]:
        print('  HEADER-NL %r => %r' % (key, value))
    raise SystemExit('refuse: %d section-header row(s) contain a line break' % len(header_newline))
if header_unbalanced:
    for key, value in header_unbalanced[:10]:
        print('  HEADER-MARK %r => %r' % (key, value))
    raise SystemExit('refuse: %d section-header row(s) lost their asterisk markers '
                     '(python integration/fix_section_headers.py)' % len(header_unbalanced))
print('Section-header guard: OK')

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

# --- 语言包守卫：四套语言包的键必须与简体底本逐条一致（键是英文原文，永远不翻译） ---
import struct as _struct

def read_bin(path):
    data = path.read_bytes()
    if data[:8] != b'W2CNMAP1':
        raise SystemExit('语言包格式错误：%s' % path)
    count = _struct.unpack('<I', data[8:12])[0]
    offset, keys = 12, []
    for _ in range(count):
        a, b = _struct.unpack('<II', data[offset:offset + 8]); offset += 8
        keys.append(data[offset:offset + a * 2].decode('utf-16le')); offset += a * 2 + b * 2
    if offset != len(data):
        raise SystemExit('语言包长度与条目数不符：%s' % path)
    return keys

language_root = root / 'payload' / 'variants'
if not language_root.exists():
    raise SystemExit('缺少语言包目录 payload/variants；先跑 python integration/build_variants.py')
base_keys = sorted(entries)
languages = []
for folder in sorted(p for p in language_root.iterdir() if p.is_dir()):
    dict_path = folder / 'translations.bin'
    if not dict_path.exists():
        raise SystemExit('语言包缺少 translations.bin：%s' % folder.name)
    keys = read_bin(dict_path)
    if sorted(keys) != base_keys:
        raise SystemExit('语言包键集合与简体底本不一致：%s' % folder.name)
    if folder.name != 'zh-CN':
        font = folder / 'overlay' / 'Dat' / 'Fonts' / 'WitE2CN.ttf'
        if not font.exists():
            raise SystemExit('语言包缺少字体：%s' % folder.name)
    languages.append(folder.name)
order = ['zh-CN', 'zh-TW', 'zh-HK', 'zh-MO']
languages.sort(key=lambda code: order.index(code) if code in order else 99)
print('Language packs:', ', '.join(languages))

package_path = root / 'payload' / 'package.json'
package = json.loads(package_path.read_text(encoding='utf8'))
package['languages'] = languages
package['default_language'] = 'zh-CN'
package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding='utf8')

files = [root / 'WitE2CN_Text.dll'] + [
    p for p in (root / 'payload').rglob('*')
    if p.is_file() and p.name not in ('checksums.json', 'compat.json')
    and p.relative_to(root / 'payload').as_posix() != 'translations.bin']
checksums = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
(root / 'payload' / 'checksums.json').write_text(json.dumps(checksums, indent=2), encoding='utf8')
(root / 'settings.json').write_text('{}\n', encoding='utf8')
print('Integrity metadata:', len(checksums), 'files')
