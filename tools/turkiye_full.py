#!/usr/bin/env python3
"""Official-source Türkiye offline map + BRouter installer for KALE.

This tool is intentionally separate from KALE's offline runtime. Run ONLINE once
before an emergency. Never bulk-download OSM's public raster tile service.
"""
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAPS=ROOT/'data/maps'
ROUTING=ROOT/'data/routing'
SEGMENTS=ROUTING/'segments4'
VECTOR_URL='https://data.bbbike.org/osm/mbtiles/region/europe/turkey/turkey.osm.mbtiles-shortbread.zip'
ROUTER_URL='https://github.com/abrensch/brouter/releases/download/v1.7.10/brouter-1.7.10.zip'
ROUTER_SHA256='023fec3ba997758e8cd7ab9e1bae52e962af3f00b57683e3de86b84ffad01532'
SEGMENT_BASE='https://brouter.de/brouter/segments4/'
NAMES=[f'E{x}_N{y}.rd5' for x in (25,30,35,40,45) for y in (35,40)]
USER_AGENT='KALE-offline-map-installer/2.1 (manual download; pre-disaster)'

def stream(url,path):
    """Retry/resume large downloads; do not treat partial HTTP bodies as complete."""
    path.parent.mkdir(parents=True,exist_ok=True)
    part=path.with_name(path.name+'.part')
    meta_file=path.with_name(path.name+'.part.meta')
    # A partial download can only be resumed if the origin returned a validator.
    existing=part.stat().st_size if part.exists() else 0
    etag=meta_file.read_text().strip() if meta_file.exists() else ''
    if existing and not etag:
        print('Kısmi indirme için doğrulayıcı yok; dosya güvenle yeniden indiriliyor:',path.name)
        part.unlink(missing_ok=True);existing=0
    headers={'User-Agent':USER_AGENT,'Accept-Encoding':'identity'}
    if existing:
        headers.update({'Range':f'bytes={existing}-','If-Range':etag})
    req=urllib.request.Request(url,headers=headers)
    try:
        response=urllib.request.urlopen(req,timeout=90)
    except urllib.error.HTTPError as exc:
        if exc.code!=416:raise
        part.unlink(missing_ok=True);meta_file.unlink(missing_ok=True)
        return stream(url,path)
    with response as src:
        code=src.status
        content_range=src.headers.get('Content-Range','')
        actual_validator=src.headers.get('ETag') or src.headers.get('Last-Modified') or ''
        resume=(bool(existing) and code==206 and content_range.startswith(f'bytes {existing}-')
                and actual_validator==etag)
        if existing and not resume:
            print('Sunucu devam etmeyi doğrulamadı, dosya yeniden indiriliyor:',path.name)
            part.unlink(missing_ok=True);existing=0
        if not existing and code==206:
            raise ValueError('HTTP 206 beklenmeyen kısmi yanıt.')
        if code not in (200,206):raise ValueError(f'HTTP {code} beklenmeyen indirme yanıtı.')
        if not resume:
            if not actual_validator:meta_file.unlink(missing_ok=True)
            else:meta_file.write_text(actual_validator)
        length=src.headers.get('Content-Length')
        expected=int(length) if length and length.isdigit() else None
        received=0
        with part.open('ab' if resume else 'wb') as dst:
            while True:
                block=src.read(1024*1024)
                if not block:break
                dst.write(block);received+=len(block)
                if received%(32*1024*1024)<len(block):
                    print(f'{path.name}: {(received+existing)/1048576:.0f} MiB',flush=True)
            dst.flush();os.fsync(dst.fileno())
    if expected is not None and expected!=received:
        raise ValueError(f'Eksik indirme: beklenen {expected}, alınan {received} bayt. Yeniden dene.')
    if received+existing<1024:raise ValueError('Şüpheli küçük dosya, kurulum durduruldu.')
    os.replace(part,path);meta_file.unlink(missing_ok=True)
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
    return path.stat().st_size,digest.hexdigest()


def install_map(dry_run=False):
    target=MAPS/'turkiye-street.mbtiles'
    if target.exists():
        sys.path.insert(0,str(ROOT))
        from routing import inspect_street_map
        if inspect_street_map().get('installed'):
            print('Sokak haritası doğrulandı, tekrar indirilmiyor:',target);return
        raise ValueError('Sokak dosyası var ama bozuk: '+str(target)+' (silmeden önce yedekle).')
    archive=MAPS/'turkiye-shortbread.zip'
    if dry_run:print('İNDİR:',VECTOR_URL,'=>',archive);return
    if not archive.exists():
        size,sha=stream(VECTOR_URL,archive);print('İndirilen harita ZIP',size,'bytes SHA256',sha)
    # One .mbtiles entry only; never use extractall on an external ZIP.
    with zipfile.ZipFile(archive) as z:
        members=[i for i in z.infolist() if i.filename.lower().endswith('.mbtiles') and not i.is_dir()]
        if len(members)!=1:raise ValueError('Tek MBTiles dosyası bulunamadı.')
        info=members[0]
        if not 1_000_000<=info.file_size<=2_000_000_000:raise ValueError('Beklenmeyen MBTiles boyutu.')
        MAPS.mkdir(parents=True,exist_ok=True)
        temp=MAPS/'turkiye-street.mbtiles.incoming'
        if temp.exists():raise FileExistsError('Önceki geçici haritayı kontrol et.')
        try:
            with z.open(info) as src,temp.open('wb') as dst:
                shutil.copyfileobj(src,dst,8*1024*1024)
                dst.flush();os.fsync(dst.fileno())
            with sqlite3.connect(temp.as_uri()+'?mode=ro&immutable=1',uri=True) as c:
                fmt=dict(c.execute('SELECT name,value FROM metadata')).get('format','').lower()
                if fmt not in ('pbf','mvt'):raise ValueError('Harita PBF vektör MBTiles değil.')
                if not c.execute('SELECT 1 FROM tiles LIMIT 1').fetchone():raise ValueError('Karo tablosu boş.')
            os.replace(temp,target)
        finally:temp.unlink(missing_ok=True)
    archive.unlink(missing_ok=True)  # Veri çıkarıldı, ilk kurulumda boş alanı geri kazan.
    print('Gerçek sokak haritası kuruldu:',target,'| MiB:',round(target.stat().st_size/1048576,1))

def install_segments(dry_run=False,region='all'):
    names=NAMES if region=='all' else ['E25_N35.rd5','E25_N40.rd5','E30_N35.rd5','E30_N40.rd5']
    for name in names:
        path=SEGMENTS/name
        if path.exists() and path.stat().st_size>1024:
            print('VAR:',name);continue
        if dry_run:print('İNDİR:',SEGMENT_BASE+name);continue
        size,sha=stream(SEGMENT_BASE+name,path)
        print('Rota:',name,'size',size,'SHA256',sha)

def install_engine(dry_run=False):
    jar=ROUTING/'brouter.jar'
    if jar.exists() and (ROUTING/'profiles2/lookups.dat').exists():
        print('BRouter motoru kurulu.');return
    if dry_run:print('İNDİR:',ROUTER_URL);return
    path=ROUTING/'brouter-release.zip'
    if not path.exists():
        size,sha=stream(ROUTER_URL,path);print('BRouter ZIP',size,'SHA256',sha)
    # GitHub release asset's upstream SHA-256 (tag v1.7.10); never install unverified Java code.
    check=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):check.update(part)
    if check.hexdigest()!=ROUTER_SHA256:
        raise ValueError('BRouter sürüm SHA-256 doğrulaması başarısız. Arşiv güvenilir değil: '+str(path))
    with zipfile.ZipFile(path) as z:
        entries=z.infolist();jars=[e for e in entries if not e.is_dir() and e.filename.lower().endswith('.jar')
            and 'brouter' in Path(e.filename).name.lower() and e.file_size<=50_000_000]
        if len(jars)!=1:raise ValueError('Yayın paketindeki BRouter JAR sayısı beklenen değil; paket yapısı değişmiş olabilir.')
        if jars[0].file_size>50_000_000:raise ValueError('Jar aşırı büyük.')
        ROUTING.mkdir(parents=True,exist_ok=True)
        with z.open(jars[0]) as src,jar.open('wb') as dst:shutil.copyfileobj(src,dst)
        profiles=[e for e in entries if '/profiles2/' in ('/'+e.filename) and e.filename.endswith(('.brf','.dat')) and not e.is_dir()]
        if len(profiles)<3:
            jar.unlink(missing_ok=True);raise ValueError('Profil/lookup dosyaları eksik; otomatik kurulum yapılmadı.')
        for info in profiles:
            if info.file_size>8_000_000:raise ValueError('Profil boyutu şüpheli.')
            dest=ROUTING/'profiles2'/Path(info.filename).name
            dest.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as src,dest.open('wb') as out:shutil.copyfileobj(src,out)
    (ROUTING/'customprofiles').mkdir(exist_ok=True)
    path.unlink(missing_ok=True)
    print('BRouter ve profilleri hazır:',jar)

def main():
    p=argparse.ArgumentParser(description='KALE Türkiye sokak haritası ve offline rota dosyaları')
    p.add_argument('action',choices=['all','map','segments','engine','check'])
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--region',choices=['all','ege'],default='all')
    a=p.parse_args()
    if a.action=='check':
        sys.path.insert(0,str(ROOT))
        from routing import inspect_street_map,get_routing_status
        print(json.dumps({'map':inspect_street_map(),'routing':get_routing_status()},ensure_ascii=False,indent=2));return
    if a.action in ('all','map'):install_map(a.dry_run)
    if a.action in ('all','segments'):install_segments(a.dry_run,a.region)
    if a.action in ('all','engine'):install_engine(a.dry_run)
    if a.dry_run:print('DRY RUN: Dosya indirilmedi veya değiştirilmedi.')
    else:print('İndirme bitti. Rota için ikinci Termux oturumunda python3 tools/run_brouter.py çalıştır.')

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,zipfile.BadZipFile,sqlite3.Error,urllib.error.URLError) as e:
        print('HATA:',e,file=sys.stderr);sys.exit(1)
