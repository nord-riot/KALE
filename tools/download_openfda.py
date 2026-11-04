#!/usr/bin/env python3
"""Download official openFDA drug/label ZIP partitions to a local folder.

Network is used ONLY when this script is explicitly run. It downloads actual FDA
labels, not a guessed drug list. Run import_openfda.py afterwards. Large dataset!
"""
import argparse
import json
import shutil
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

INDEX='https://api.fda.gov/download.json'

def files_from_manifest(doc):
    section=doc['results']['drug']['label']
    return section['partitions']

def main():
    p=argparse.ArgumentParser(description='Resmî openFDA ilaç etiketlerini toplu indir')
    p.add_argument('--destination',type=Path,default=Path('data/openfda-zip'))
    p.add_argument('--max-parts',type=int,default=1,help='İlk N parça; 0=hepsi (çok büyük olabilir)')
    p.add_argument('--list',action='store_true',help='Yalnızca indirilecek parçaları listele')
    args=p.parse_args()
    if args.max_parts<0:p.error('--max-parts negatif olamaz')
    with urllib.request.urlopen(INDEX,timeout=40) as res:
        doc=json.load(res)
    partitions=files_from_manifest(doc)
    if args.max_parts:partitions=partitions[:args.max_parts]
    print('Kaynak güncelleme:',doc.get('meta',{}).get('last_updated','bilinmiyor'))
    print('Seçilen parça:',len(partitions))
    if args.list:
        for x in partitions:print(x['file'],x.get('size_mb','?'),'MB')
        return
    args.destination.mkdir(parents=True,exist_ok=True)
    for i,record in enumerate(partitions,1):
        url=record['file']
        parsed=urllib.parse.urlsplit(url)
        if parsed.scheme!='https' or parsed.hostname!='download.open.fda.gov' or not parsed.path.endswith('.zip'):
            raise ValueError('Geçersiz indirme adresi: '+url)
        dest=args.destination/Path(parsed.path).name
        if dest.exists() and zipfile.is_zipfile(dest) and zipfile.ZipFile(dest).testzip() is None:
            print(f'[{i}/{len(partitions)}] Mevcut ZIP geçerli, atlandı: {dest.name}');continue
        temp=dest.with_suffix('.zip.part')
        print(f'[{i}/{len(partitions)}] İndiriliyor: {dest.name}',flush=True)
        with urllib.request.urlopen(url,timeout=90) as src, temp.open('wb') as out:
            shutil.copyfileobj(src,out,length=1024*1024)
        if not zipfile.is_zipfile(temp):
            temp.unlink(missing_ok=True);raise ValueError('İndirilen dosya ZIP değil')
        with zipfile.ZipFile(temp) as z:
            if z.testzip():temp.unlink(missing_ok=True);raise ValueError('ZIP bozuk')
        temp.replace(dest)
        print(f'OK {dest.stat().st_size/1048576:.1f} MiB',flush=True)
    print('Tamam. İçe aktarma: python3 tools/import_openfda.py '+str(args.destination))

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as e:
        print('HATA:',e,file=sys.stderr);sys.exit(1)
