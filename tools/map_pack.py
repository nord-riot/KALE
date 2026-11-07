#!/usr/bin/env python3
"""Validate/install one *already obtained*, licensed raster MBTiles archive.

No tile scraping, remote URLs or network connections. This is deliberately local.
"""
import argparse
import hashlib
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'data/maps/turkiye.mbtiles'
RASTER={'png','jpg','jpeg','webp'}
MAX_BYTES=12*1024**3


def tile_type(blob):
    if blob.startswith(b'\x89PNG\r\n\x1a\n'):return 'png'
    if blob.startswith(b'\xff\xd8\xff'):return 'jpeg'
    if blob.startswith(b'RIFF') and blob[8:12]==b'WEBP':return 'webp'
    return None


def inspect(path):
    path=Path(path).expanduser()
    if not path.is_file() or not path.stat().st_size or path.stat().st_size>MAX_BYTES:
        raise ValueError('MBTiles dosyası yok/boş veya 12 GiB sınırını aşıyor.')
    # Use readonly non-immutable connection, respecting SQLite journal for integrity checks.
    with sqlite3.connect('file:'+str(path.resolve())+'?mode=ro',uri=True,timeout=10) as c:
        tables={x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'metadata','tiles'}.issubset(tables):raise ValueError('metadata ve tiles tabloları gerekli.')
        values=dict(c.execute('SELECT name,value FROM metadata'))
        fmt=str(values.get('format','')).lower()
        if fmt not in RASTER:raise ValueError('Vektör PBF desteklenmiyor; PNG/JPEG/WebP raster MBTiles gerekli.')
        cols={r[1] for r in c.execute('PRAGMA table_info(tiles)')}
        if not {'zoom_level','tile_column','tile_row','tile_data'}.issubset(cols):raise ValueError('MBTiles karo kolonları eksik.')
        count=c.execute('SELECT COUNT(*) FROM tiles').fetchone()[0]
        if not count:raise ValueError('Haritada karo yok.')
        zmin,zmax=c.execute('SELECT MIN(zoom_level),MAX(zoom_level) FROM tiles').fetchone()
        if not isinstance(zmin,int) or not isinstance(zmax,int) or zmin<0 or zmax>18:
            raise ValueError('Desteklenen zoom 0-18.')
        sample=c.execute('SELECT zoom_level,tile_column,tile_row,tile_data FROM tiles ORDER BY zoom_level LIMIT 1').fetchone()
        z,x,y,blob=sample
        if not (0<=x<2**z and 0<=y<2**z and len(blob)<=2_000_000):raise ValueError('Örnek karo boyutu/koordinatı hatalı.')
        seen=tile_type(bytes(blob))
        if not seen or (fmt=='png' and seen!='png') or (fmt in ('jpg','jpeg') and seen!='jpeg') or (fmt=='webp' and seen!='webp'):
            raise ValueError('Dosyadaki gerçek karo biçimi metadata ile eşleşmiyor.')
        integrity=c.execute('PRAGMA quick_check').fetchone()[0]
        if integrity!='ok':raise ValueError('SQLite bütünlük hatası.')
        return {'name':str(values.get('name','Yerel harita'))[:100],'format':fmt,'minzoom':zmin,'maxzoom':zmax,'tiles':count,'size_bytes':path.stat().st_size}


def sha256_digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(2*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def install(source,target=TARGET,replace=False):
    source=Path(source).expanduser().resolve(); target=Path(target).expanduser().resolve()
    details=inspect(source)
    target.parent.mkdir(parents=True,exist_ok=True)
    if source==target:
        return details, 'Paket zaten kurulu.'
    if target.exists() and not replace:raise FileExistsError('Önceki harita korunuyor. Değiştirmek için --replace kullan.')
    free=shutil.disk_usage(target.parent).free
    if free<source.stat().st_size+40*1024**2:
        raise OSError('Yeterli boş alan yok. Dosya boyutu + 40 MiB gerekli.')
    temp_path=None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent,prefix='.kale-map-',suffix='.tmp',delete=False) as t:
            temp_path=Path(t.name)
            with source.open('rb') as src:shutil.copyfileobj(src,t,1024*1024)
            t.flush();os.fsync(t.fileno())
        again=inspect(temp_path)
        if again!=details:raise ValueError('Kopyalanan dosya doğrulamadan geçemedi.')
        # Older map is kept as one recoverable backup when explicitly replacing.
        if target.exists():
            backup=target.with_suffix('.mbtiles.previous')
            if backup.exists():raise FileExistsError('Önceki harita yedeği zaten var. Elle kontrol et.')
            os.replace(target,backup)
            try:os.replace(temp_path,target)
            except Exception:
                os.replace(backup,target)
                raise
            return details,f'Harita kuruldu, eski harita yedeği: {backup}'
        os.replace(temp_path,target)
        return details,f'Harita kuruldu: {target}'
    finally:
        if temp_path:temp_path.unlink(missing_ok=True)


def main():
    p=argparse.ArgumentParser(description='KALE yerel raster MBTiles kontrol/kurulum')
    p.add_argument('file',type=Path,help='Önceden indirilmiş ve lisansı uygun MBTiles dosyası')
    p.add_argument('--install',action='store_true',help='Doğrulanan dosyayı data/maps/turkiye.mbtiles konumuna kopyala')
    p.add_argument('--sha256',help='Sağlayıcının yayınladığı beklenen 64 karakterlik SHA-256 değeri (isteğe bağlı)')
    p.add_argument('--replace',action='store_true',help='Önceki haritayı .previous yedeğiyle değiştir')
    a=p.parse_args()
    try:
        if a.sha256:
            expected=a.sha256.lower().strip()
            if len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected):
                raise ValueError('SHA-256 64 adet onaltılık karakter olmalıdır.')
            if sha256_digest(a.file)!=expected:raise ValueError('SHA-256 doğrulaması başarısız, harita kurulmadı.')
        if a.install:details,msg=install(a.file,replace=a.replace)
        else:details,msg=inspect(a.file),'ÖN KONTROL: Dosya değiştirilmedi.'
        print(msg)
        print(f"{details['name']} | {details['tiles']} karo | zoom {details['minzoom']}-{details['maxzoom']} | {details['size_bytes']/1024**2:.1f} MiB | {details['format']}")
    except (ValueError,sqlite3.Error,OSError) as e:
        p.exit(1,'HATA: '+str(e)+'\n')

if __name__=='__main__':main()
