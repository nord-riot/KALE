#!/usr/bin/env python3
"""Import official openFDA drug/label bulk JSON / JSON.zip into KALE offline DB.
No network calls. Download zip archives from https://open.fda.gov/apis/drug/label/download/.
For large input files use optional ijson (`python3 -m pip install ijson`), JSON.load fallback
only for smaller archives. Medical text is stored verbatim and unverified, in source language.
"""
import argparse
import json
import sqlite3
import sys
import zipfile
from pathlib import Path
from medicines_core import DB, initialize, label_to_row, put


def source_files(path):
    if path.is_dir():
        for f in sorted(path.rglob('*')):
            if f.is_file() and (f.suffix.lower() in ('.zip','.json')):yield f
    elif path.is_file():yield path
    else:raise FileNotFoundError(path)


def json_records(stream, size):
    try:
        import ijson
        yield from ijson.items(stream, 'results.item')
    except ImportError:
        if size > 80*1024*1024:
            raise RuntimeError('Büyük JSON için ijson gerekir: python3 -m pip install ijson')
        payload=json.load(stream)
        if not isinstance(payload,dict) or not isinstance(payload.get('results'),list):
            raise ValueError('Beklenen openFDA drug/label JSON: {"results":[...]}')
        yield from payload['results']


def import_file(conn,path,max_count=0):
    n=0;ignored=0
    def process(stream,size):
        nonlocal n,ignored
        for raw in json_records(stream,size):
            row=label_to_row(raw)
            if row and put(conn,row):n+=1
            else:ignored+=1
            if max_count and n>=max_count:break
    if path.suffix.lower()=='.zip':
        with zipfile.ZipFile(path) as z:
            for item in z.infolist():
                if item.is_dir() or not item.filename.endswith('.json'):continue
                if item.file_size>2_000_000_000:raise ValueError('JSON güvenlik limiti aşıldı')
                with z.open(item) as stream:process(stream,item.file_size)
                if max_count and n>=max_count:break
    else:
        with path.open('rb') as stream:process(stream,path.stat().st_size)
    return n,ignored


def main(argv=None):
    ap=argparse.ArgumentParser(description='KALE openFDA çevrimdışı etiket aktarımı')
    ap.add_argument('source',type=Path,help='Bir JSON(.zip) dosyası veya dosya klasörü')
    ap.add_argument('--db',type=Path,default=DB,help='Çıktı SQLite dosyası (varsayılan data/kale.db)')
    ap.add_argument('--max',type=int,default=0,help='Dosya başına en fazla kayıt (0: sınır yok)')
    args=ap.parse_args(argv)
    if args.max<0:ap.error('--max negatif olamaz')
    if not args.db.exists():ap.error(f'KALE veritabanı bulunamadı: {args.db}')
    total=skipped=0
    with sqlite3.connect(args.db) as conn:
        initialize(conn)
        for path in source_files(args.source):
            try:
                with conn:
                    count,ignored=import_file(conn,path,args.max)
                total+=count;skipped+=ignored
                print(f'{path.name}: {count} etiket, {ignored} atlandı',flush=True)
            except (OSError,ValueError,RuntimeError,zipfile.BadZipFile,json.JSONDecodeError) as exc:
                print(f'HATA {path}: {exc}',file=sys.stderr)
                raise SystemExit(1)
    print(f'TOPLAM {total} etiket içe aktarıldı; {skipped} geçersiz kayıt atlandı. Veritabanı: {args.db.stat().st_size} bayt')

if __name__=='__main__':main()
