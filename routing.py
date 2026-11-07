"""KALE — secure local-only BRouter gateway and offline pack inventory.

No route is ever invented: results come only from a *running* local BRouter
server backed by user-installed OSM .rd5 segments. No remote routing service.
"""
from __future__ import annotations
import json
import math
import os
import socket
import sqlite3
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

BASE=Path(__file__).resolve().parent
MAP_DIR=BASE/'data'/'maps'
ROUTING_DIR=BASE/'data'/'routing'
ROUTER_HOST='127.0.0.1'
ROUTER_PORT=int(os.environ.get('KALE_BROUTER_PORT','17777'))
PROFILES={'walk':'shortest','bike':'fastbike','car':'car-vario'}
SEGMENTS=tuple(f'E{x}_N{y}.rd5' for x in (25,30,35,40,45) for y in (35,40))

class RoutingError(ValueError):
    def __init__(self,message,status=400):
        super().__init__(message);self.status=status


def inspect_street_map():
    p=MAP_DIR/'turkiye-street.mbtiles'
    if not p.is_file():return {'installed':False,'message':'Türkiye sokak haritası henüz yüklenmedi.'}
    try:
        with sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True,timeout=2) as con:
            meta=dict(con.execute('SELECT name,value FROM metadata'))
            if meta.get('format','').lower() not in ('pbf','mvt'):
                return {'installed':False,'message':'Sokak haritası vektör PBF/MVT MBTiles olmalı.'}
            if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='tiles'").fetchone():
                return {'installed':False,'message':'MBTiles karo tablosu yok.'}
            try:
                if not con.execute('SELECT 1 FROM tiles LIMIT 1').fetchone():
                    return {'installed':False,'message':'Harita dosyası boş.'}
            except sqlite3.Error:
                return {'installed':False,'message':'Harita karoları okunamadı.'}
            return {'installed':True,'name':meta.get('name','Türkiye OSM vektör haritası')[:120],
                    'format':'pbf','minzoom':max(0,min(17,int(meta.get('minzoom','0')))),
                    'maxzoom':max(0,min(17,int(meta.get('maxzoom','14')))),
                    'size_bytes':p.stat().st_size,'attribution':'© OpenStreetMap contributors (ODbL)','id':'sokak'}
    except (sqlite3.Error,OSError,ValueError):
        return {'installed':False,'message':'MBTiles bozuk veya okunamadı.'}


def read_vector_tile(z,x,y):
    if not inspect_street_map().get('installed'):return None
    if not (0<=z<=17 and 0<=x<2**z and 0<=y<2**z):return None
    p=MAP_DIR/'turkiye-street.mbtiles'
    try:
        with sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True,timeout=2) as con:
            row=con.execute('SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?',
                            (z,x,2**z-1-y)).fetchone()
            if not row:return None
        raw=bytes(row[0])
        if len(raw)>2_500_000:return None
        # Most MBTiles vector tiles contain gzip payload; send them unchanged with
        # Content-Encoding rather than pretending compressed bytes are raw PBF.
        compressed=raw[:2]==b'\x1f\x8b'
        if compressed:
            import gzip
            # Bounded decompression to avoid gzip bombs from untrusted archives.
            with gzip.GzipFile(fileobj=__import__('io').BytesIO(raw)) as f:
                result=f.read(5_000_001)
            if len(result)>5_000_000:return None
            raw=result
        if len(raw)>5_000_000 or not raw:return None
        return 'application/vnd.mapbox-vector-tile',raw
    except (sqlite3.Error,OSError,EOFError,ValueError):return None


def get_routing_status(probe=False):
    directory=ROUTING_DIR/'segments4'
    files=[{'name':name,'size_bytes':(directory/name).stat().st_size} for name in SEGMENTS if (directory/name).is_file() and (directory/name).stat().st_size>1024]
    enabled=(len(files)==len(SEGMENTS))
    out={'segments_found':len(files),'segments_required':len(SEGMENTS),'bytes':sum(f['size_bytes'] for f in files),
         'files':files,'full_turkey_data':enabled,'engine':'BRouter (yerel Java servisi)','engine_online':False,
         'note':'Rota ancak gerçek OSM bölge verileri ve yerel BRouter servisi çalışıyorsa hesaplanır.'}
    if probe:
        try:
            with socket.create_connection((ROUTER_HOST,ROUTER_PORT),timeout=.5):out['engine_online']=True
        except OSError:pass
    out['ready']=enabled and out['engine_online']
    return out


def validate_coordinates(lat,lon):
    if type(lat) not in (int,float) or type(lon) not in (int,float):raise RoutingError('Sayısal koordinat gerekli.')
    if not all(math.isfinite(x) for x in (lat,lon)) or not (35<=lat<=43.5 and 25<=lon<=47):
        raise RoutingError('Rota noktası Türkiye kapsama alanı dışında.')
    return lat,lon


def calculate_route(start_lat,start_lon,end_lat,end_lon,mode='walk', opener=urlopen):
    if mode not in PROFILES:raise RoutingError('Geçersiz rota türü.')
    a,b=validate_coordinates(start_lat,start_lon),validate_coordinates(end_lat,end_lon)
    if math.hypot(a[0]-b[0],a[1]-b[1])<0.00003:raise RoutingError('Başlangıç ve hedef çok yakın.')
    params=urlencode({'lonlats':f'{a[1]:.6f},{a[0]:.6f}|{b[1]:.6f},{b[0]:.6f}',
                      'profile':PROFILES[mode],'alternativeidx':'0','format':'geojson'})
    # Host is hardcoded LOOPBACK. Never expose BRouter itself to Wi-Fi devices.
    url=f'http://{ROUTER_HOST}:{ROUTER_PORT}/brouter?'+params
    try:
        with opener(url,timeout=22) as response:
            data=response.read(4_000_001)
        if len(data)>4_000_000:raise RoutingError('Rota yanıtı aşırı büyük.',502)
        result=json.loads(data)
    except (OSError,URLError,HTTPError,TimeoutError):
        raise RoutingError('BRouter çalışmıyor veya rota hesaplanamadı. Termux kurulumunu kontrol et.',503)
    except (ValueError,UnicodeDecodeError):
        raise RoutingError('Rota motoru geçersiz yanıt verdi.',502)
    if not isinstance(result,dict) or result.get('type')!='FeatureCollection':
        raise RoutingError('Rota bulunamadı veya motor hata döndürdü.',422)
    features=result.get('features',[])
    lines=[item for item in features if isinstance(item,dict) and item.get('geometry',{}).get('type')=='LineString']
    if not lines:raise RoutingError('Kullanılabilir yol güzergâhı bulunamadı.',422)
    route=lines[0];coords=route['geometry'].get('coordinates',[])
    if not isinstance(coords,list) or not 2<=len(coords)<=60000:
        raise RoutingError('Rota geometrisi geçersiz.',502)
    for pt in coords:
        if not (isinstance(pt,list) and len(pt)>=2 and all(type(v) in (int,float) and math.isfinite(v) for v in pt[:2])
                and -180<=pt[0]<=180 and -90<=pt[1]<=90):
            raise RoutingError('Rota koordinatı geçersiz.',502)
    props=route.get('properties',{}) or {}
    def safeval(key):
        try:
            v=float(props.get(key,0))
            return round(v,1) if 0<=v<10**9 and math.isfinite(v) else None
        except (ValueError,TypeError):return None
    return {'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'LineString','coordinates':coords},'properties':{'profile':mode,'track_length_m':safeval('track-length'),'total_time_s':safeval('total-time')}}],
            'source':'Yerel BRouter + OSM; mevcut trafik/kapanış/tehlike bilgisi yok.'}
