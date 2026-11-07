#!/usr/bin/env python3
"""KALE offline bundle audit. No internet requests and no user data access."""
import ast
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'
DB=ROOT/'data/kale.db'

def check():
    sw=(WEB/'sw.js').read_text(encoding='utf-8')
    match=re.search(r'const CORE=(\[.*?\]);',sw,re.S)
    if not match:raise ValueError('sw.js CORE listesi okunamadı')
    core=ast.literal_eval(match.group(1))
    missing=[path for path in core if path not in ('/','/api/catalog') and not (WEB/path.lstrip('/')).is_file()]
    with sqlite3.connect('file:'+str(DB)+'?mode=ro',uri=True) as db:
        integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
        guides=db.execute('SELECT COUNT(*) FROM entries').fetchone()[0]
        medicines=db.execute('SELECT COUNT(*) FROM medicines').fetchone()[0]
    files=[WEB/path.lstrip('/') for path in core if path not in ('/','/api/catalog') and (WEB/path.lstrip('/')).is_file()]
    manifests={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    field=json.loads((WEB/'assets/field-guides.json').read_text('utf-8'))
    result={'field_guides':len(field.get('guides',[])),'application':'KALE','server_version':'2.3.0','resources_in_precache':len(core),'missing':missing,
            'sqlite_integrity':integrity,'guides':guides,'medicines':medicines,
            'precached_static_bytes':sum(p.stat().st_size for p in files),'file_sha256':manifests,
            'note':'Bu yalnız sunucu dosyalarının bütünlüğünü ölçer; tarayıcı önbelleği ve offline saha testi değildir.'}
    result['passed']=not missing and integrity=='ok' and guides>=146 and medicines>=707
    return result

if __name__=='__main__':
    r=check()
    if '--json' in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:
        print(f"KALE çevrimdışı paket denetimi: {'OK' if r['passed'] else 'HATA'}")
        print(f"{r['guides']} rehber · {r['medicines']} ilaç · {r['resources_in_precache']} önbellek kalemi · {r['precached_static_bytes']/1024/1024:.2f} MiB statik")
        if r['missing']:print('Eksik:',r['missing'])
        print(r['note'])
    sys.exit(0 if r['passed'] else 1)
