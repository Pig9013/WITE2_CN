"""Finalize integrity metadata and offline-only launcher configuration."""
from pathlib import Path
import hashlib
import json
import shutil

root=Path(__file__).resolve().parent
(root/'logs').mkdir(exist_ok=True)
files=[root/'WitE2CN_Text.dll']+[p for p in (root/'payload').rglob('*') if p.is_file() and p.name!='checksums.json']
checksums={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
(root/'payload'/'checksums.json').write_text(json.dumps(checksums,indent=2),encoding='utf8')
(root/'settings.json').write_text('{}\n',encoding='utf8')
print('Integrity metadata:',len(checksums),'files')
