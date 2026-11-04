#!/usr/bin/env python3
"""Produce precisely the 70 *unapproved* Turkish phase 2 medicine editorial drafts.

The general reference link is not evidence that individual clinical claims were
validated. No patient-specific doses, eligibility or treatment advice is emitted.
"""
import csv
import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/phase2_editorial_source.psv'
OUT=ROOT/'data/medicine_phase2_tr.json'
PHASES=ROOT/'review/ilac_10_faz_plani.csv'
DB=ROOT/'data/kale.db'
COLUMNS=('name','indications','effects','side_effects','allergies','contraindications','interactions','warnings','pregnancy')

def main():
    with PHASES.open(encoding='utf-8-sig',newline='') as f:
        all_phases=list(csv.DictReader(f))
    phase2=[r['ilac_adi'] for r in all_phases if r['faz']=='2']
    assert len(phase2)==70 and len(all_phases)==707
    with sqlite3.connect(DB) as conn:
        valid_names={r[0] for r in conn.execute('SELECT name FROM medicines')}
        existing_categories={r[0]:r[1] for r in conn.execute('SELECT name,category FROM medicines')}
    groups={}
    for file in ('medicines_index.json','medicines_extra.json'):
        for group,entries in json.loads((ROOT/'data'/file).read_text('utf8')).items():
            for name in entries: groups.setdefault(name,group)
    aliases={
        'Adrenalin (epinefrin)':'Adrenalin (epinefrin)',
        'Aspirin (asetilsalisilik asit)':'Asetilsalisilik asit',
        'Amoksisilin-klavulanik asit':'Amoksisilin + klavulanik asit',
        'Amoksisilin/klavulanat':'Amoksisilin + klavulanik asit',
        'Artemeter-lumefantrin':'Artemeter + lumefantrin',
        'Atovakuon-proguanil':'Atovakuon + proguanil',
        'Asetilsistein IV':'Asetilsistein',
        'Biktegravir':'Biktegravir (kombinasyon ürünü olabilir; tüm etken maddeler ürün bazında doğrulanmalı)',
    }
    drafts=[]
    for lineno,line in enumerate(SRC.read_text('utf8').splitlines(),1):
        if not line.strip():continue
        fields=line.split('|')
        if len(fields)!=len(COLUMNS):raise ValueError(f'Line {lineno}: expected {len(COLUMNS)} fields, got {len(fields)}')
        d={k:v.strip() for k,v in zip(COLUMNS,fields)}
        for key,value in d.items():
            if len(value)<(3 if key=='name' else 32):raise ValueError(f'Line {lineno}: missing/short {key}')
        name=d['name']
        if name not in valid_names:raise ValueError('Not in existing catalogue: '+name)
        d.update({
            'generic_name':aliases.get(name,name),'active_ingredients':aliases.get(name,name),'category':groups.get(name, existing_categories[name]),
            'inactive_ingredients':'Üretici/marka/form doğrulanmadı. Laktoz, jelatin, boya ve koruyucular dahil yardımcı maddeler bilinmiyor; gerçek ürünün güncel Türkiye KÜB/KT belgesi kontrol edilmelidir.',
            'storage':'Saklama koşulları tablet, damla, ampul ve soğuk zincir ürünlerinde değişir. Ürüne özgü ambalaj talimatı ve son kullanma tarihi doğrulanmalıdır.',
            'source':'KALE Faz 2 Türkçe editoryal taslak; kayda özel klinik kaynak ve Türkiye KÜB/KT doğrulaması yapılmadı',
            'source_url':'https://medlineplus.gov/druginformation.html',
            'source_updated':'','locale':'tr','phase':2,
            'review_status':'FAZ 2 TÜRKÇE TASLAK — DOKTOR / ECZACI ONAYI BEKLİYOR',
            'medical_review_approved':False,
        })
        d['allergies']+=' Ürüne özgü yardımcı madde alerjenleri bu aşamada tespit edilmedi.'
        d['warnings']+=' Bu kayıt reçete, doz veya kişiye özel güvenli kullanım kararı değildir; Türkiye ürün bilgisi ve hekim/eczacı onayı bekler.'
        drafts.append(d)
    names=[d['name'] for d in drafts]
    if len(drafts)!=70 or len(set(names))!=70 or set(names)!=set(phase2):
        raise ValueError('Phase 2 source must match the planned 70 names exactly. Missing='+str(set(phase2)-set(names))+' unexpected='+str(set(names)-set(phase2)))
    OUT.write_text(json.dumps(drafts,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # Preserve the phase allocation. Update only phase-2 status and description labels.
    for row in all_phases:
        if row['faz']=='2':
            row['faz_durumu']='FAZ 2 TÜRKÇE TASLAK TAMAMLANDI'
            row['mevcut_aciklama']='Yeni veya yeniden yazılmış Türkçe taslak — ürün bazlı doktor kontrolü bekliyor'
    with PHASES.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=all_phases[0].keys())
        writer.writeheader();writer.writerows(all_phases)
    print(f'Phase 2 OK: {len(drafts)} drafts, {len(set(phase2))} expected entries; all unapproved')

if __name__=='__main__':main()
