"""Finalize integrity metadata and offline-only launcher configuration."""
from pathlib import Path
import hashlib
import json
import shutil

root=Path(__file__).resolve().parent
(root/'logs').mkdir(exist_ok=True)
files=[root/'WitE2CN_Text.dll']+[p for p in (root/'payload').rglob('*') if p.is_file() and p.name not in ('checksums.json','compat.json')]
checksums={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
(root/'payload'/'checksums.json').write_text(json.dumps(checksums,indent=2),encoding='utf8')
(root/'settings.json').write_text('{}\n',encoding='utf8')
print('Integrity metadata:',len(checksums),'files')

# --- 片段键守卫：纯数字 / 序数 / 罗马数字不得进词典（会污染表格数字列） ---
import re as _re
_dict = json.loads((root/'payload'/'translations.json').read_text(encoding='utf8'))
_bad = [k for k in _dict if _re.fullmatch(r'\d+', k) or _re.fullmatch(r'\d+(st|nd|rd|th)', k, _re.I) or _re.fullmatch(r'[IVXLC]+', k)]
if _bad:
    raise SystemExit('refuse: %d fragment key(s) in dictionary, e.g. %r' % (len(_bad), _bad[:5]))
print('Fragment-key guard: OK')
