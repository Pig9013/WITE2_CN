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


def build():
    entries = {}
    provenance = {}
    def add(src, dst, origin):
        if not isinstance(src, str) or not isinstance(dst, str):
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
    for p in (game/'Dat'/'Info').glob('*.csv'):
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
            allchars.update(p.read_text(encoding='utf-8-sig'))
    (payload/'font-characters.txt').write_text(''.join(sorted(allchars)),encoding='utf8')
    skip={}
    for rel in ['Dat/translation.csv','Dat/Scen/translation.csv']:
        p=game/rel
        if p.exists() and p.read_bytes()==(PROJECT/'build'/'translation.csv').read_bytes():
            skip[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    (payload/'package.json').write_text(json.dumps({'game_sha256':expected_hash,'old_generated_tables':skip,'translations':len(entries)},indent=2),encoding='utf8')
    print('Packaged', len(entries), 'existing translations;', len(blob), 'bytes')


if __name__ == '__main__':
    build()
