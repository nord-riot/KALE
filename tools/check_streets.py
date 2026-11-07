#!/usr/bin/env python3
"""KALE actual offline OSM street diagnostics (not just an empty map shell).

Prints whether a local MBTiles file, a real İzmir map tile, and the
Shortbread street layers are present. Does not need internet or extra packages.
"""
from __future__ import annotations
import math
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from routing import inspect_street_map, read_vector_tile


def varint(data, pos):
    out=0
    for shift in range(0,70,7):
        if pos>=len(data):
            raise ValueError("Kesik protobuf veri")
        b=data[pos];pos+=1
        out|=(b&0x7f)<<shift
        if not b&0x80:
            return out,pos
    raise ValueError("Geçersiz protobuf varint")


def layers(blob):
    """Read only MVT Tile.layers and Layer.name, no geospatial dependency."""
    names=[]
    pos=0
    while pos<len(blob):
        key,pos=varint(blob,pos)
        field,wire=key>>3,key&7
        if wire==0:
            _,pos=varint(blob,pos)
        elif wire in (1,5):
            pos+=8 if wire==1 else 4
        elif wire==2:
            length,pos=varint(blob,pos)
            if length>len(blob)-pos:
                raise ValueError("Bozuk MVT katmanı")
            data=blob[pos:pos+length]
            pos+=length
            if field!=3:
                continue
            cursor=0
            while cursor<len(data):
                inner,cursor=varint(data,cursor)
                kind,itype=inner>>3,inner&7
                if itype==0:
                    _,cursor=varint(data,cursor)
                elif itype in (1,5):
                    cursor+=8 if itype==1 else 4
                elif itype==2:
                    size,cursor=varint(data,cursor)
                    if size>len(data)-cursor:
                        raise ValueError("Kesik MVT layer")
                    if kind==1:
                        names.append(data[cursor:cursor+size].decode('utf8','replace'))
                    cursor+=size
                else:
                    raise ValueError("Beklenmeyen MVT wire type")
        else:
            raise ValueError("MVT wire type bozuk")
        if pos>len(blob):
            raise ValueError("MVT sonunu aşan alan")
    return names


def xy(lat,lon,z):
    latitude=math.radians(lat)
    n=2**z
    return int((lon+180)/360*n),int((1-math.asinh(math.tan(latitude))/math.pi)/2*n)


def main():
    info=inspect_street_map()
    print("Türkiye OSM sokak paketi:", "KURULU" if info['installed'] else "EKSİK")
    print("Açıklama:",info.get('message') or info.get('name') or 'Yok')
    if not info['installed']:
        print("ÇÖZÜM (internet varken): cd ~/KALE && python3 tools/turkiye_full.py map")
        return 2
    print("Paket:",round(info['size_bytes']/2**20,1),"MiB",
          "Zoom:",info['minzoom'],"-",info['maxzoom'])
    locations=[
        ("İzmir",38.4237,27.1428),
        ("İstanbul",41.0082,28.9784),
        ("Ankara",39.9334,32.8597),
    ]
    working=0
    for city,lat,lon in locations:
        found=False
        for z in (14,13,12,11,10):
            if not(info['minzoom']<=z<=info['maxzoom']):
                continue
            x,y=xy(lat,lon,z)
            result=read_vector_tile(z,x,y)
            if result is None:
                continue
            names=layers(result[1])
            has_roads=any(n in names for n in ('streets','transportation','street_polygons'))
            print(f"{city}: z={z}, {len(result[1])} bayt, katmanlar: {', '.join(names)}")
            if has_roads:
                working+=1
                found=True
            break
        if not found:
            print(city+": Sokak katmanı doğrulanamadı.")
    if not working:
        print("HATA: Harita dosyası var, ancak gerçek sokak karosu okunamadı.")
        return 3
    print("SONUÇ: Gerçek vektör sokak karosu okundu. Telefonda")
    print("http://127.0.0.1:8090/harita.html adresini aç, yakınlığı 13–14 yap.")
    return 0


if __name__=="__main__":
    try:
        sys.exit(main())
    except (ValueError,OSError,KeyError) as exc:
        print("Harita veri denetimi başarısız:",exc,file=sys.stderr)
        sys.exit(4)
