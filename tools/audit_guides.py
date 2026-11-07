#!/usr/bin/env python3
"""KALE content coverage QA. Read-only; no DB writes or network access."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED={
    'web/assets/field-guides.json': ('guides',28),
    'web/assets/shelter-water.json': ('cards',18),
    'web/assets/food-energy-winter.json': ('cards',24),
    'web/assets/first-aid.json': ('cards',24),
    'web/assets/poisonous-plants.json': ('plants',28),
    'web/assets/dangerous-mushrooms.json': ('mushrooms',16),
}
ERRORS=[]

def read(path):
    with (ROOT/path).open(encoding='utf-8') as file:
        return json.load(file)

def validate():
    core=read('data/content.json').get('entries',[])
    additions=read('data/guide-expansions.json').get('items',[])
    amap={(x['id'],x['title']):x for x in additions}
    if len(core)!=146 or len(additions)!=146:
        ERRORS.append('146 ana rehber sayısı değişmiş.')
    for item in core:
        extra=amap.get((item.get('id'),item.get('title')))
        if not extra or len(extra.get('extra',''))<1000:
            ERRORS.append('Ana rehberin ayrıntısı eksik: '+str(item.get('id')))
    print(f'Ana bilgi merkezi: {len(core)} kayıt, {len(additions)} ayrıntı')
    total=len(core)
    for path,(key,expected) in EXPECTED.items():
        items=read(path).get(key,[])
        if len(items)!=expected:
            ERRORS.append(f'{path}: beklenen {expected}, bulunan {len(items)}')
        for item in items:
            sections=item.get('details',[])
            if not isinstance(sections,list) or len(sections)<3 or any(
                not isinstance(part,dict) or not part.get('heading') or
                len(str(part.get('text','')))<100 for part in sections
            ):
                ERRORS.append(f'{path} eksik ayrıntı: {item.get("id")}')
            if not item.get('warning') and path!='web/assets/first-aid.json':
                ERRORS.append(f'{path} risk uyarısı eksik: {item.get("id")}')
        total+=len(items)
        print(f'{path}: {len(items)}/{expected} kayıt kontrol edildi')
    print(f'TOPLAM: {total} rehber/doğa kaydı')
    if ERRORS:
        print('HATALAR:')
        for error in ERRORS: print(' -',error)
        return 1
    print('OK: Kapsam ve veri yapısı geçti; bu test uzman onayı veya tıbbi doğruluk testi değildir.')
    return 0

if __name__=='__main__':
    try:sys.exit(validate())
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print('İçerik denetimi çalışmadı:',exc,file=sys.stderr)
        sys.exit(2)
