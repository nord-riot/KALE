#!/usr/bin/env python3
"""KALE v1.8 offline server snapshot / SHA-256 verification / guarded restore.

Stdlib-only. Includes data sources and editorial review files but deliberately
excludes large, replaceable raster MBTiles. Browser localStorage is separate.
The resulting ZIP is NOT encrypted and may contain names/medical review notes.
"""
import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
FORMAT = 'KALE-SERVER-SNAPSHOT-v1'
MAX_FILES = 140
MAX_SINGLE = 32 * 1024 * 1024
MAX_TOTAL = 125 * 1024 * 1024
PREFIX = 'KALE-SERVER-BACKUP-'


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def safe_name(name):
    """Whitelisted relative paths only; neither zip-slip nor symlink escape."""
    if not isinstance(name, str) or '\\' in name or '\x00' in name or name.startswith('/'):
        return False
    p = PurePosixPath(name)
    if len(p.parts) != 2 or any(x in ('.','..','') for x in p.parts):
        return False
    if p.parts[0] == 'data':
        return (re.fullmatch(r'[A-Za-z0-9_-]{1,80}\.(?:json|psv|db|sqlite3)', p.parts[1]) is not None)
    if p.parts[0] == 'review':
        return (re.fullmatch(r'[A-Za-z0-9_.-]{1,100}\.(?:xlsx|csv|md|txt)', p.parts[1]) is not None)
    return False


def collect(root=ROOT):
    files = {}
    for folder in ('data','review'):
        for path in sorted((root / folder).iterdir()):
            if not path.is_file() or path.is_symlink():
                continue
            rel = f'{folder}/{path.name}'
            if not safe_name(rel):
                continue
            if path.stat().st_size > MAX_SINGLE:
                raise ValueError(f'Dosya çok büyük: {rel}')
            if rel == 'data/kale.db' or rel == 'data/doctor_reviews.sqlite3':
                # SQLite online snapshot avoids torn copies while reads occur.
                with tempfile.TemporaryDirectory() as tmp:
                    staged = Path(tmp) / 'snapshot.sqlite3'
                    with sqlite3.connect(f'file:{path}?mode=ro',uri=True) as source, sqlite3.connect(staged) as target:
                        source.backup(target)
                    blob = staged.read_bytes()
            else:
                blob = path.read_bytes()
            files[rel] = blob
    if 'data/kale.db' not in files or 'data/content.json' not in files:
        raise ValueError('Gerekli KALE veri dosyaları eksik')
    if len(files) > MAX_FILES or sum(map(len, files.values())) > MAX_TOTAL:
        raise ValueError('Güvenlik sınırı aşıldı')
    return files


def validate_sqlite(payload):
    with tempfile.NamedTemporaryFile(suffix='.db') as temp:
        temp.write(payload);temp.flush()
        with sqlite3.connect(f'file:{temp.name}?mode=ro',uri=True) as c:
            if c.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Bozuk SQLite yedeği')
            if c.execute('SELECT COUNT(*) FROM medicines').fetchone()[0] < 707:
                raise ValueError('İlaç arşivi eksik SQLite yedeği')
            if c.execute('SELECT COUNT(*) FROM entries').fetchone()[0] < 146:
                raise ValueError('Rehber arşivi eksik SQLite yedeği')


def make_backup(root=ROOT,output_dir=None, keep=14):
    root=Path(root)
    output_dir=Path(output_dir or root / 'backups').resolve()
    output_dir.mkdir(parents=True,exist_ok=True,mode=0o700)
    files=collect(root)
    validate_sqlite(files['data/kale.db'])
    name=PREFIX+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(3)+'.zip'
    dest=output_dir/name
    manifest={'format':FORMAT,'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'app':'KALE','files':{k:{'bytes':len(v),'sha256':digest(v)} for k,v in files.items()},
              'encrypted':False,'note':'Özel inceleme notları içerebilir; erişim kısıtlı saklayın. Tarayıcı verileri bu dosyada DEĞİL.'}
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
    fd=os.open(dest,flags,0o600)
    try:
        with os.fdopen(fd,'wb') as fh,zipfile.ZipFile(fh,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
            for path,blob in files.items():z.writestr(path,blob)
            z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf8'))
        verify_backup(dest)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    prune(output_dir,keep)
    return dest, len(files)


def verify_backup(path):
    path=Path(path)
    if path.stat().st_size > MAX_TOTAL:
        raise ValueError('ZIP çok büyük')
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)>MAX_FILES+1 or len(names)!=len(set(names)) or 'manifest.json' not in names:
            raise ValueError('ZIP içinde yinelenen/eksik dosya')
        for info in z.infolist():
            if info.is_dir() or info.file_size>MAX_SINGLE or info.compress_size>MAX_TOTAL:
                raise ValueError('Arşivde izin verilmeyen tür/boyut')
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Arşivde sembolik bağlantı')
        m=json.loads(z.read('manifest.json'))
        if not isinstance(m,dict) or m.get('format')!=FORMAT:
            raise ValueError('KALE yedek biçimi yanlış')
        declared=m.get('files')
        if not isinstance(declared,dict) or not declared or set(declared)!=(set(names)-{'manifest.json'}):
            raise ValueError('Dosya manifestosu uyuşmuyor')
        if 'data/kale.db' not in declared or 'data/content.json' not in declared:
            raise ValueError('KALE çekirdek dosyaları yok')
        data={};size=0
        for name,entry in declared.items():
            if not safe_name(name):raise ValueError('Geçersiz dosya yolu: '+name)
            if not isinstance(entry,dict) or type(entry.get('bytes'))!=int:
                raise ValueError('Geçersiz manifest girdisi')
            info=z.getinfo(name)
            if info.file_size!=entry['bytes'] or info.file_size>MAX_SINGLE:
                raise ValueError('Dosya boyutu uyuşmuyor')
            size+=info.file_size
            if size>MAX_TOTAL:raise ValueError('Aşırı dosya toplamı')
            blob=z.read(name)
            if digest(blob)!=entry.get('sha256'):raise ValueError('SHA-256 uyuşmuyor: '+name)
            data[name]=blob
        validate_sqlite(data['data/kale.db'])
        src=json.loads(data['data/content.json'].decode('utf8'))
        if not isinstance(src,dict) or len(src.get('entries',[]))<146:
            raise ValueError('Rehber JSON eksik veya geçersiz')
    return m,data


def prune(folder,keep):
    if keep is None or keep<1:return
    archives=sorted((x for x in Path(folder).glob(PREFIX+'*.zip') if x.is_file() and not x.is_symlink()),reverse=True)
    for archive in archives[keep:]:archive.unlink()


def restore(path,root=ROOT,apply=False,confirm=''):
    root=Path(root)
    manifest,files=verify_backup(path)
    if not apply:
        return {'verified_files':len(files),'restored':False,'created_utc':manifest['created_utc']}
    if confirm!='GERI_YUKLE':raise ValueError('--confirm GERI_YUKLE olmadan geri yükleme yapılmaz.')
    # The service MUST be stopped. Do not run against a live database.
    backup_dir=(root/'backups').resolve()
    backup_dir.mkdir(parents=True,exist_ok=True,mode=0o700)
    safety,_=make_backup(root,backup_dir,keep=None)
    staged={}
    try:
        for name,blob in files.items():
            dest=root/name
            if dest.exists() and dest.is_symlink():raise ValueError('Hedef sembolik bağlantı: '+name)
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.parent.resolve().is_relative_to(root.resolve()):raise ValueError('Güvenlik: hedef klasör dışarıda')
            fd,temp=tempfile.mkstemp(prefix='.kale-restore-',dir=dest.parent)
            staged[dest]=Path(temp)
            with os.fdopen(fd,'wb') as fh:
                fh.write(blob);fh.flush();os.fsync(fh.fileno())
            os.chmod(temp,0o600 if name.endswith(('.sqlite3','.db')) else 0o640)
        for target,temp in staged.items():os.replace(temp,target)
    finally:
        for f in staged.values():f.unlink(missing_ok=True)
    return {'verified_files':len(files),'restored':True,'safety_backup':str(safety)}


def main():
    parser=argparse.ArgumentParser(description='KALE yerel sunucu yedekleme / geri yükleme (internet gerekmez)')
    sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('create',help='Sunucu veri yedeği oluştur');p.add_argument('--output-dir',type=Path);p.add_argument('--keep',type=int,default=14)
    p=sub.add_parser('verify',help='SHA-256 ve SQLite bütünlüğü denetle');p.add_argument('file',type=Path)
    p=sub.add_parser('restore',help='Geri yükleme (varsayılan dry-run)');p.add_argument('file',type=Path);p.add_argument('--apply',action='store_true');p.add_argument('--confirm',default='')
    args=parser.parse_args()
    if args.action=='create':
        path,n=make_backup(output_dir=args.output_dir,keep=args.keep)
        print(f'YEDEK HAZIR: {path} · {n} dosya · ZIP şifreli DEĞİL, gizli saklayın')
    elif args.action=='verify':
        m,files=verify_backup(args.file);print(f'DOĞRULANDI: {len(files)} dosya · {m["created_utc"]} · SHA-256 / SQLite OK')
    else:print(json.dumps(restore(args.file,apply=args.apply,confirm=args.confirm),ensure_ascii=False,indent=2))

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,sqlite3.Error,zipfile.BadZipFile,json.JSONDecodeError) as exc:
        print('HATA: '+str(exc),file=sys.stderr);sys.exit(2)
