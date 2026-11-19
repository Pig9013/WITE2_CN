"""Package existing translations verbatim; never invoke a model or edit source text."""
import csv
import json
import struct
import hashlib
import os
import re
import shutil
from pathlib import Path

MOD = Path(__file__).resolve().parent
PROJECT = MOD.parent


def find_game():
    """Resolve the game without assuming this machine's drive or Steam library."""
    candidates = []
    env = os.environ.get('WITE2_GAME')
    if env:
        candidates.append(Path(env))
    settings = MOD / 'settings.json'
    if settings.exists():
        try:
            value = json.loads(settings.read_text(encoding='utf-8')).get('game_path')
            if value:
                candidates.append(Path(value))
        except Exception:
            pass
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as key:
            steam = winreg.QueryValueEx(key, 'SteamPath')[0]
        candidates.append(Path(steam) / 'steamapps' / 'common' / "Gary Grigsby's War in the East 2")
        libraries = Path(steam) / 'steamapps' / 'libraryfolders.vdf'
        if libraries.exists():
            for line in libraries.read_text(encoding='utf-8', errors='replace').splitlines():
                match = re.search(r'"path"\s+"([^"]+)"', line)
                if match:
                    candidates.append(Path(match.group(1).replace('\\\\', '\\')) /
                                      'steamapps' / 'common' / "Gary Grigsby's War in the East 2")
    except Exception:
        pass
    for candidate in candidates:
        if (candidate / 'WarInTheEast2.exe').exists():
            return candidate
    raise FileNotFoundError('找不到游戏；请设置环境变量 WITE2_GAME 或在 mod\\settings.json 填写 game_path。')


def _pe_sections(data):
    """Return (virtual_address, span, raw_offset) for every PE section."""
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    if data[pe:pe + 4] != b'PE\0\0':
        raise ValueError('not a PE file')
    count = struct.unpack_from('<H', data, pe + 6)[0]
    opt = struct.unpack_from('<H', data, pe + 20)[0]
    table = pe + 24 + opt
    sections = []
    for index in range(count):
        base = table + index * 40
        vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', data, base + 8)
        sections.append((va, max(vsize, rawsize), rawptr))
    return sections


def verify_addr_sources(game, specs):
    """Read the game EXE back and confirm every registered address still holds its source string."""
    exe = Path(game) / 'WarInTheEast2.exe'
    data = exe.read_bytes()
    sections = _pe_sections(data)
    problems = []
    for rva_text, text, expect, note in specs:
        if expect is None:
            problems.append('%s: no source string recorded' % rva_text)
            continue
        rva = int(rva_text, 16)
        offset = None
        for va, span, rawptr in sections:
            if va <= rva < va + span:
                offset = rawptr + (rva - va)
                break
        if offset is None or offset + 2 > len(data):
            problems.append('%s: address outside every section' % rva_text)
            continue
        chars = []
        pos = offset
        while pos + 1 < len(data) and data[pos:pos + 2] != b'\0\0' and len(chars) < 400:
            chars.append(data[pos:pos + 2].decode('utf-16le', 'replace'))
            pos += 2
        actual = ''.join(chars)
        if actual != expect:
            problems.append('%s: expected %r, found %r' % (rva_text, expect, actual))
    if problems:
        raise SystemExit('address override check failed (game EXE may have changed):\n  ' + '\n  '.join(problems))
    print('Address sources verified: %d' % len(specs))


def build():
    entries = {}
    provenance = {}

    def _is_ui(origin):
        return any(x in origin for x in (
            'ui_extra', 'ui_14b', 'ui_full', 'ui_ops', 'ui_en_zh',
            'ui_extra.csv', 'launcher_ui_values', 'mod_full/payload/translation.csv'))

    def add(src, dst, origin):
        if not isinstance(src, str) or not isinstance(dst, str):
            return
        # UI 标签是权威层：场景 CSV 的同名键（如人名 Major）不得覆盖界面军衔 Major=少校
        prev = provenance.get(src)
        if prev and _is_ui(prev) and not _is_ui(origin):
            return
        if src and dst and src != dst and '\0' not in src + dst:
            entries[src] = dst
            provenance[src] = origin
            # The game displays some hotkey/UI descriptions in lower or upper
            # case. The text hook is exact-match, so add the case variants for
            # UI-origin entries (scenario prose is intentionally not expanded).
            ui_origin = any(x in origin for x in (
                'ui_extra', 'ui_14b', 'ui_full', 'ui_ops', 'ui_en_zh',
                'ui_extra.csv', 'launcher_ui_values', 'mod_full/payload/translation.csv'))
            if ui_origin and ' ' in src:
                entries.setdefault(src.lower(), dst)
                entries.setdefault(src.upper(), dst)
                provenance.setdefault(src.lower(), origin)
                provenance.setdefault(src.upper(), origin)

    for folder, names in [
        ('data/scenario_csv/translations', ['place', 'leader', 'equipment', 'unit', 'airgroup', 'aog', 'event']),
        ('data/translations', ['info_descriptions', 'scenarios_14b', 'ui_14b', 'ui_full', 'ui_extra', 'ui_ops', 'hotkey_suffix', 'hotkey_raw']),
    ]:
        for name in names:
            path = PROJECT / folder / (name + '.zh.jsonl')
            if not path.exists():
                continue
            for line in path.read_text(encoding='utf-8-sig').splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get('qa_status') == 'blocked':
                    continue
                add(row.get('text'), row.get('translation'), str(path.relative_to(PROJECT)))

    for rel, sc, dc in [
        ('build/translation.csv', 'English Key', 'Translated Text'),
        ('data/translations/unit_names_en_zh.csv', 'en', 'zh'),
        ('mod/assets/translation.csv', 'English Key', 'Translated Text'),
        ('glossary/ui_en_zh.csv', 'en', 'zh'),
        ('glossary/ui_extra.csv', 'en', 'zh'),
        ('glossary/launcher_ui_values.csv', 'en', 'zh'),
    ]:
        path = PROJECT / rel
        if path.exists():
            for row in csv.DictReader(path.open(encoding='utf-8-sig', newline='')):
                add(row.get(sc), row.get(dc), rel)

    # The already assembled scenario translations are the final existing output.
    # Read them as a dictionary; never import them back into scenario structures.
    game = find_game()
    audit = []
    for translated in sorted((PROJECT/'build/scenario_csv_zh').glob('*/*.zh.csv')):
        scenario = translated.parent.name
        name = translated.name.replace('.zh.csv', '.csv')
        original = game/'Dat'/'CSV'/scenario/name
        backup = PROJECT/'csv_swap_backup'/scenario/name
        if backup.exists():
            original = backup
        if not original.exists():
            continue
        raw = original.read_bytes()
        try:
            source_rows = list(csv.reader(raw.decode('utf-8-sig').splitlines(keepends=True)))
        except UnicodeDecodeError:
            source_rows = list(csv.reader(raw.decode('cp1252').lstrip('\ufeff').splitlines(keepends=True)))
        dest_rows = list(csv.reader(translated.open(encoding='utf-8-sig',newline='')))
        if len(source_rows)!=len(dest_rows) or source_rows[0]!=dest_rows[0]:
            raise ValueError('Scenario CSV structure mismatch: '+str(translated))
        changes=0
        for a,b in zip(source_rows[1:],dest_rows[1:]):
            if len(a)!=len(b):
                raise ValueError('Scenario CSV column mismatch: '+str(translated))
            for src,dst in zip(a,b):
                if src!=dst and src and dst:
                    add(src,dst,str(translated.relative_to(PROJECT)))
                    changes+=1
        audit.append({'file':str(translated.relative_to(PROJECT)), 'rows':len(source_rows), 'changes':changes})

    # 最后一道：glossary/master_overrides.json 优先级最高，一处改、处处生效。
    master = PROJECT / 'glossary' / 'master_overrides.json'
    if master.exists():
        try:
            overrides = json.loads(master.read_text(encoding='utf-8'))
            for src, dst in overrides.items():
                if isinstance(src, str) and isinstance(dst, str) and src and dst:
                    entries[src] = dst
                    provenance[src] = 'glossary/master_overrides.json'
        except Exception:
            pass

    # 丢弃层：技术性字符串（语言代码、编码名）与美术路径标识符不进词典，保留原文。
    # 必须放在覆盖层**之后**：两层同时存在的键否则会被覆盖层复活 —— v1.6.5 的 82
    # 条地形枚举词、2026-11-06 的小河 MINOR// 都是这个顺序缺陷漏回来的。
    drops = PROJECT / 'glossary' / 'master_drops.json'
    if drops.exists():
        try:
            drop_keys = json.loads(drops.read_text(encoding='utf-8'))
        except ValueError as exc:
            raise SystemExit('master_drops.json 解析失败：%s' % exc)
        for key in drop_keys:
            entries.pop(key, None)
            provenance.pop(key, None)

    # 搁置层：缺权威型号出处、暂不翻译的条目 —— 保留英文原文，等查到出处再译。
    # 与 master_drops 的区别：drops 是「永不翻译」（技术串/美术路径），pending 是「待补证」，
    # 补到出处后把键移出清单重跑即可回到词典，不需要改代码。
    pending = PROJECT / 'glossary' / 'pending_sources.json'
    if pending.exists():
        try:
            pending_keys = json.loads(pending.read_text(encoding='utf-8'))['keys']
        except (ValueError, KeyError, TypeError) as exc:
            raise SystemExit('pending_sources.json 解析失败：%s' % exc)
        shelved = [k for k in pending_keys if entries.pop(k, None) is not None]
        for key in pending_keys:
            provenance.pop(key, None)
        print('Shelved (kept in English): %d/%d %s' % (len(shelved), len(pending_keys), shelved[:5]))

    # 美术令牌钉死层：引擎会把 //Tiles//ROAD//POOR//POOR_001.tga 这类路径里的令牌
    # （POOR/AVERAGE/GOOD）当普通字符串交给本地化查表函数。精确表没有这些键时，钩子的
    # 归一化第二索引（忽略大小写与空白）会把它接回界面词 'Poor'→差，路径随即变成中文
    # 目录，图块加载失败、引擎静默跳过 —— 2026-11-17「道路显示开关失效」即此。
    # v1.9.7 只把这些键从词典里删掉；归一化索引是后来才加的，把它们全部复活了。
    # 处置：会撞上归一化键的全大写美术令牌，钉成恒等条目（值=原文），精确命中先返回原文。
    def _norm_key(text):
        return ''.join(ch.lower() for ch in text if ch not in ' \t\r\n\u00a0\u3000')

    art_tokens_path = PROJECT / 'glossary' / 'art_tokens.json'
    pinned = []
    if art_tokens_path.exists():
        art = json.loads(art_tokens_path.read_text(encoding='utf-8'))
        art_token_names = (set(art.get('tile_dirs', [])) | set(art.get('art_dirs', [])) |
                           set(art.get('self_named_tile_dirs', {})) | set(art.get('path_tokens', {})))
        norm_owner = {}
        for key in entries:
            norm_owner.setdefault(_norm_key(key), key)
        for token in sorted(art_token_names):
            if not re.fullmatch(r'[A-Z0-9_]+', token) or token in entries:
                continue
            other = norm_owner.get(_norm_key(token))
            if other is None or other == token:
                continue
            entries[token] = token
            provenance[token] = 'art token pin (glossary/art_tokens.json)'
            pinned.append('%s<-%s' % (token, other))
    if pinned:
        print('Art-token pins: %d %s' % (len(pinned), ', '.join(pinned)))

    # AOG 名字钉死层：引擎在载入场景时就把航空作战群（AOG）名字交给本地化查表函数并
    # 缓存进对象，而「空中指令设置」面板筛选可用航空作战群时，比对的是航空队（Unit）
    # 的原文英文名。AOG 名字一旦被译成中文，两边永不相等，列表就是 0 行 —— 2026-11-19
    # 实机 A/B（passthru 全英文时列表出现、全中文时为空）与 trace（load 阶段
    # "Luftflotte N" exact zh、面板阶段 "GND ATTACK : Luftflotte 4" 仍 en）证实。
    # 这类名字是引擎内部标识符，只能保持原文；清单由 integration/gen_aog_identity.py
    # 从各想定的 Dat\CSV\<scenario>\AOGs.csv 生成。
    aog_identity_path = PROJECT / 'glossary' / 'aog_identity.json'
    if aog_identity_path.exists():
        aog_data = json.loads(aog_identity_path.read_text(encoding='utf-8'))
        aog_names = aog_data.get('names', [])
        aog_pinned = 0
        aog_absent = 0
        for name in aog_names:
            if name in entries:
                entries[name] = name
                provenance[name] = 'aog identity pin (glossary/aog_identity.json)'
                aog_pinned += 1
            elif name in provenance:
                aog_absent += 1
        print('AOG identity pins: %d/%d' % (aog_pinned, len(aog_names)))

    # Reject unsafe formatter inputs without changing the saved translation text.
    rejected=[]
    token = re.compile(r'%(?:%|[-+ 0#]*\d*(?:\.\d+)?(?:I64|ll|l|h)?[sSdiuoxXfFeEgGcCp])')
    for src,dst in list(entries.items()):
        reason=''
        if token.findall(src)!=token.findall(dst):
            reason='format placeholders differ'
        elif len(dst.encode('utf-16le'))//2>=1536:
            reason='exceeds engine formatter capacity'
        elif re.search(r'\.(?:txt|dll|exe|csv|scn|bmp|tga|wav|wmv|ttf|dat|json)$',src,re.I):
            reason='resource filename, not display text'
        if reason:
            rejected.append({'source':src,'translation':dst,'reason':reason,'origin':provenance[src]})
            del entries[src]

    # 地址特化层：同一条英文字面量在引擎里可能既当界面标签、又当数据/资源标识符——
    # 'CITY' 在 0x561C90 一带是 //Tiles// 地形目录名，在 0x54B60C 却是「分配支援单位」
    # 对话框的列头；'DIS' 在战斗详情是「紊乱」、在撤编筛选是「解散」。词典只有一张，
    # 按文本区分不了，这类冲突改为按源串地址（PE 内 RVA）特化：键写成 '@@RVA:XXXXXX'，
    # 钩子 translate() 比对指针偏移后只对那一份字面量生效。见 docs\同串异义与地址特化.md
    addr_path = PROJECT / 'glossary' / 'addr_overrides.json'
    addr_added = 0
    skip_added = 0
    if addr_path.exists():
        addr_data = json.loads(addr_path.read_text(encoding='utf-8'))
        specs = []
        for rva_text, spec in sorted(addr_data.get('entries', {}).items()):
            text = spec[0] if isinstance(spec, list) else spec
            expect = spec[1] if isinstance(spec, list) and len(spec) > 1 else None
            note = spec[2] if isinstance(spec, list) and len(spec) > 2 else ''
            specs.append((rva_text, text, expect, note))
        verify_addr_sources(game, specs)
        for rva_text, text, expect, note in specs:
            key = '@@RVA:%06X' % int(rva_text, 16)
            entries[key] = text
            provenance[key] = 'address override %s (%s)' % (rva_text, note)
            addr_added += 1
        # 地址跳过层：字面量被拼进美术路径（//Gui//AOG-%s flag.tga 等），翻译后文件名
        # 不存在，引擎静默丢图。这些地址登记为「原样返回」，钩子按源串指针识别后
        # 直接返回原文，不参与文本翻译。条目为 [原文, 说明]。
        skip_specs = []
        for rva_text, spec in sorted(addr_data.get('skip', {}).items()):
            expect = spec[0] if isinstance(spec, list) else spec
            note = spec[1] if isinstance(spec, list) and len(spec) > 1 else ''
            skip_specs.append((rva_text, expect, expect, note))
        if skip_specs:
            verify_addr_sources(game, skip_specs)
            for rva_text, text, expect, note in skip_specs:
                key = '@@SKIP:%06X' % int(rva_text, 16)
                entries[key] = text
                provenance[key] = 'address skip %s (%s)' % (rva_text, note)
                skip_added += 1
    if addr_added:
        print('Address overrides: %d' % addr_added)
    if skip_added:
        print('Address skips: %d' % skip_added)

    payload = MOD / 'payload'
    payload.mkdir(exist_ok=True)
    (payload / 'translations.json').write_text(json.dumps(entries, ensure_ascii=False), encoding='utf8')
    blob = bytearray(b'W2CNMAP1' + struct.pack('<I', len(entries)))
    for src, dst in sorted(entries.items()):
        a, b = src.encode('utf-16le'), dst.encode('utf-16le')
        blob += struct.pack('<II', len(a)//2, len(b)//2) + a + b
    (payload / 'translations.bin').write_bytes(blob)
    audit_dir = PROJECT / 'audit'
    audit_dir.mkdir(exist_ok=True)
    (audit_dir / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf8')
    (audit_dir / 'translation-audit.json').write_text(json.dumps({'accepted':len(entries),'rejected':rejected,'csv_structure':audit},ensure_ascii=False,indent=2),encoding='utf8')

    overlay=payload/'overlay'
    (overlay/'Dat'/'Fonts').mkdir(parents=True,exist_ok=True)
    shutil.copy2(PROJECT/'build'/'WitE2CN.ttf',overlay/'Dat'/'Fonts'/'WitE2CN.ttf')
    shutil.copy2(MOD/'assets'/'GuiFonts.json',overlay/'Dat'/'GuiFonts.json')
    for p in (PROJECT/'build'/'scen_zh').glob('*.txt'):
        dest=overlay/'Dat'/'Scen'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    # Description CSVs are read directly by the game. Keep every row/extra cell;
    # use the existing translations verbatim, indexed by source file and id.
    descriptions={}
    for line in (PROJECT/'data'/'translations'/'info_descriptions.zh.jsonl').read_text(encoding='utf8').splitlines():
        row=json.loads(line)
        if row.get('qa_status')!='blocked' and row.get('translation'):
            descriptions[(row.get('source'),row.get('row_id'))]=row['translation']
    # unitInfo.csv 的正文是单位百科：引擎按单字节代码页直接读文件，中文显示不出来
    # （v1.2.2 实机确认 UTF-8/GBK 两方案均失败）。它的正确状态是「游戏原版英文」，
    # 由 mod\restore_unit_info.py 原样放回；这里绝不能按 id 列改写正文——该列只有
    # 0/12 两个值，会让 1,168 行共用同一个键、整表覆盖成同一句
    # （见 docs\师徽显示修复_v1.9.11.md）。
    verbatim={'unitInfo.csv','deviceInfo.csv','groundInfo.csv','leaderInfo.csv'}
    for p in (game/'Dat'/'Info').glob('*.csv'):
        if p.name in verbatim:
            # 这几张表的正文列是引擎直接读的单字节文本，按 id 改写会整列塌成一句
            # （deviceInfo/groundInfo/leaderInfo 的 id 列全为 0）；正确状态是原版字节。
            dest=overlay/'Dat'/'Info'/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest)
            continue
        raw=p.read_bytes()
        try:
            decoded=raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            # These original files are Windows-1252. Preserve every field while
            # re-encoding the mod copy as UTF-8 to make the existing Chinese usable.
            decoded=raw.decode('cp1252')
        rows=list(csv.reader(decoded.splitlines(keepends=True)))
        if not rows or 'text' not in rows[0] or 'id' not in rows[0]:continue
        ti=rows[0].index('text');ii=rows[0].index('id');count=0
        for row in rows[1:]:
            if len(row)>max(ti,ii) and (p.name,row[ii]) in descriptions:
                row[ti]=descriptions[(p.name,row[ii])];count+=1
        if count:
            dest=overlay/'Dat'/'Info'/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('w',encoding='utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8',newline='') as f:
                csv.writer(f).writerows(rows)

    expected_hash=hashlib.sha256((game/'WarInTheEast2.exe').read_bytes()).hexdigest()
    allchars=set(''.join(entries.keys())+''.join(entries.values()))
    for p in overlay.rglob('*'):
        if p.is_file() and p.suffix in ('.txt','.csv'):
            if p.name in verbatim:
                # 原版百科表照原字节显示（cp1252 或 UTF-8），字形仍必须进字库
                try:allchars.update(p.read_text(encoding='utf-8-sig'))
                except UnicodeDecodeError:allchars.update(p.read_text(encoding='cp1252'))
                continue
            try:allchars.update(p.read_text(encoding='utf-8-sig'))
            except UnicodeDecodeError:continue
    (payload/'font-characters.txt').write_text(''.join(sorted(allchars)),encoding='utf8')
    skip={}
    for rel in ['Dat/translation.csv','Dat/Scen/translation.csv']:
        p=game/rel
        if p.exists() and p.read_bytes()==(PROJECT/'build'/'translation.csv').read_bytes():
            skip[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    version_file=PROJECT/'VERSION'
    mod_version=version_file.read_text(encoding='utf-8').strip() if version_file.exists() else 'dev'
    (payload/'package.json').write_text(json.dumps({'game_sha256':expected_hash,'old_generated_tables':skip,'translations':len(entries),'mod_version':mod_version},indent=2),encoding='utf8')
    print('Packaged', len(entries), 'existing translations;', len(blob), 'bytes')


if __name__ == '__main__':
    build()
