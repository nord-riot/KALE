#!/usr/bin/env python3
"""KALE v1.2 local-only, schema-validated editorial import.

NO HTTP WRITE ENDPOINT. Run from the host terminal with KALE service stopped:
  python3 tools/import_guides.py /path/to/KALE-rehber-duzenleme.json          # dry-run
  python3 tools/import_guides.py /path/to/KALE-rehber-duzenleme.json --apply  # backup+publish

Only core guide entries are touched. Medicines and doctor reviews are preserved.
"""
import argparse
import copy
import datetime as dt
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data'/'kale.db'
CATALOG=ROOT/'data'/'content.json'


def normalize(value):
    txt=str(value or '').replace('İ','I').replace('ı','i').lower()
    return ''.join(ch for ch in unicodedata.normalize('NFKD',txt) if not unicodedata.combining(ch))


def valid_url(value):
    if not isinstance(value,str) or len(value)>700:return False
    u=urlsplit(value)
    return u.scheme=='https' and bool(u.hostname) and not u.username and not u.password


def validate(content, previous):
    if not isinstance(content,dict) or content.get('format')!='KALE-EDITOR-v1':
        raise ValueError('KALE editör JSON biçimi bekleniyor.')
    records=content.get('entries')
    if not isinstance(records,list) or not 1<=len(records)<=5000:
        raise ValueError('Rehber listesi geçersiz veya aşırı büyük.')
    old={x['id']:x for x in previous['entries']}
    seen=set();checked=[];changes=0;added=0
    for r in records:
        if not isinstance(r,dict) or type(r.get('id')) is not int or r['id']<1 or r['id']>1000000 or r['id'] in seen:
            raise ValueError('Geçersiz veya yinelenen rehber ID.')
        seen.add(r['id'])
        for key,limit in [('title',160),('category',50),('body',20000),('tags',500),('warning',1500)]:
            v=r.get(key,'')
            if not isinstance(v,str) or len(v)>limit or (key in ('title','category','body') and not v.strip()):
                raise ValueError(f"ID {r['id']}: {key} boş veya sınırı aşıyor.")
        for key in ('sources','regions'):
            if not isinstance(r.get(key),list) or len(r[key])>20:
                raise ValueError(f"ID {r['id']}: {key} listesi geçersiz.")
        if any(not valid_url(u) for u in r['sources']):
            raise ValueError(f"ID {r['id']}: kaynak adresleri yalnız HTTPS olmalı.")
        if any(not isinstance(s,str) or len(s)>100 for s in r['regions']):
            raise ValueError(f"ID {r['id']}: bölge etiketi geçersiz.")
        # Preserve metadata and never let an editor confer medical approval.
        prior=old.get(r['id']);row=copy.deepcopy(prior) if prior else {
            'id':r['id'],'diagram':'','priority':'normal',
            'last_reviewed':None,'origin':'KALE içerik atölyesi'}
        edited=any(r.get(k)!=row.get(k) for k in ('title','category','body','tags','warning','sources','regions'))
        for key in ('title','category','body','tags','warning','sources','regions'):
            row[key]=copy.deepcopy(r[key])
        if edited or prior is None:
            row['review_status']='taslak—uzman onayı bekliyor'
            row['last_reviewed']=None
            row['origin']='KALE v1.2 editör'
            changes+=1
            if prior is None: added+=1
        checked.append(row)
    if not set(old).issubset(seen):
        raise ValueError('Mevcut rehberler silinemez veya eksik bırakılamaz.')
    return sorted(checked,key=lambda x:x['id']),changes,added


def apply(data):
    if not DB.is_file():raise FileNotFoundError('KALE veritabanı bulunamadı.')
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup_dir=ROOT/'backups';backup_dir.mkdir(exist_ok=True)
    backup_json=backup_dir/f'content-before-{stamp}.json'
    backup_db=backup_dir/f'kale-before-{stamp}.db'
    if backup_json.exists() or backup_db.exists():raise FileExistsError('Yedek dosya adı çakıştı, tekrar dene.')
    # Backup source files before any mutation.
    shutil.copy2(CATALOG,backup_json)
    shutil.copy2(DB,backup_db)
    tmp_db=DB.with_suffix('.publish.tmp');tmp_json=CATALOG.with_suffix('.publish.tmp')
    if tmp_db.exists() or tmp_json.exists():raise RuntimeError('Önceki geçici yayın dosyası duruyor; kontrol et.')
    try:
        # SQLite online backup copies a consistent view even if a journal exists.
        with sqlite3.connect(DB) as source,sqlite3.connect(tmp_db) as target:
            source.backup(target)
        with sqlite3.connect(tmp_db) as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('DELETE FROM entries')
            for r in data['entries']:
                c.execute('''INSERT INTO entries (
                  id,category,title,body,tags,warning,diagram,review_status,last_reviewed,
                  sources_json,regions_json,priority,origin,search_text
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
                   r['id'],r['category'],r['title'],r['body'],r['tags'],r.get('warning',''),r.get('diagram',''),
                   r['review_status'],r.get('last_reviewed'),json.dumps(r['sources'],ensure_ascii=False),
                   json.dumps(r.get('regions',[]),ensure_ascii=False),r.get('priority','normal'),
                   r.get('origin',''),normalize(' '.join((r['title'],r['category'],r['body'],r['tags'])))
                ))
            c.execute('UPDATE metadata SET value=? WHERE key=?',(json.dumps(data.get('version'),ensure_ascii=False),'version'))
            if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('SQLite bütünlük denetimi başarısız.')
            if c.execute('SELECT COUNT(*) FROM medicines').fetchone()[0]<707:raise RuntimeError('İlaç arşivi beklenenden küçük!')
            c.commit()
        tmp_json.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        # Server must be stopped to avoid stale read-only immutable handles.
        os.replace(tmp_db,DB)
        os.replace(tmp_json,CATALOG)
    finally:
        tmp_db.unlink(missing_ok=True);tmp_json.unlink(missing_ok=True)
    return backup_json,backup_db


def run(argv=None):
    p=argparse.ArgumentParser(description='KALE rehber taslaklarını güvenli biçimde içe aktar')
    p.add_argument('file',type=Path);p.add_argument('--apply',action='store_true',help='Yedekleyip veritabanına yayımla')
    args=p.parse_args(argv)
    if args.file.stat().st_size>3_000_000:raise ValueError('Dosya 3 MB sınırını aşıyor.')
    source=json.loads(CATALOG.read_text('utf-8'))
    incoming=json.loads(args.file.read_text('utf-8'))
    entries,changed,new=validate(incoming,source)
    if not changed:
        print('Değişiklik yok.');return 0
    output=copy.deepcopy(source)
    output['entries']=entries
    output['version']='1.2.0';output['build_date']=dt.datetime.now(dt.timezone.utc).date().isoformat()
    print(f'DOĞRULANDI: {len(entries)} rehber, {changed} değişiklik ({new} yeni), tıbbi onay verilmedi.')
    if not args.apply:
        print('ÖN İZLEME: hiçbir dosya değiştirilmedi. Yayınlamak için KALE servisini durdurup --apply kullan.');return 0
    jb,db=apply(output)
    print(f'YAYINLANDI: {len(entries)} rehber. İlaç ve doktor verileri korundu. Yedekler: {jb.name}, {db.name}.')
    print('KALE servisini tekrar başlat. Offline tarayıcılar yeniden önbellek hazırlamalıdır.')
    return 0

if __name__=='__main__':
    try:sys.exit(run())
    except (OSError,ValueError,sqlite3.Error,RuntimeError) as e:
        print('HATA:',e,file=sys.stderr);sys.exit(1)
