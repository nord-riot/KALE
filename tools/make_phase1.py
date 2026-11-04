#!/usr/bin/env python3
"""Compiles 71 *unreviewed* Turkish clinical editorial summaries for KALE phase 1.
Never promotes draft statements to verified drug labels or clinical approvals.
"""
import csv
import json
import sqlite3
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/phase1_editorial_source.psv'
OUT=ROOT/'data/medicine_phase1_tr.json'
PHASES=ROOT/'review/ilac_10_faz_plani.csv'
DB=ROOT/'data/kale.db'
COLS=('name','indications','effects','side_effects','allergies','contraindications','interactions','warnings')
CLASS_NOTES={
    'Metotreksat':'Gebelikte kullanılmaz; gebelik planlaması ve emzirme için güncel resmî ürün talimatı zorunludur.',
    'Lisinopril':'Gebelikte fetüse zarar verebildiğinden kullanılmaz; emzirme ayrıca değerlendirilmelidir.',
    'Benazepril':'Gebelikte fetüse zarar verebildiğinden kullanılmaz; emzirme ayrıca değerlendirilmelidir.',
    'Kaptopril':'Gebelikte fetüse zarar verebildiğinden kullanılmaz; emzirme ayrıca değerlendirilmelidir.',
    'Kandesartan':'Gebelikte fetüse zarar verebildiğinden kullanılmaz; emzirme ayrıca değerlendirilmelidir.',
    'Nalokson':'Şüpheli opioid aşırı dozunda gebelik dâhil acil bakım geciktirilmemelidir; 112 aranmalıdır.',
}

def main():
    raw=SRC.read_text(encoding='utf8').splitlines()
    rows=[]
    for idx,line in enumerate(raw,1):
        if not line.strip(): continue
        parts=line.split('|')
        if len(parts)!=len(COLS):raise ValueError(f'{idx}: wrong field count {len(parts)}')
        row=dict(zip(COLS,parts))
        for field in COLS:
            if len(row[field].strip())<(3 if field=='name' else 18):raise ValueError(f'{idx}: missing {field}')
        rows.append(row)
    if len(rows)!=71:raise ValueError(f'Expected 71 new Turkish drafts, got {len(rows)}')
    names=[r['name'] for r in rows]
    if len(names)!=len(set(names)):raise ValueError('Duplicate medicine name')
    with sqlite3.connect(str(DB)) as conn:
        existing={r[0]:r[1] for r in conn.execute('SELECT name,review_status FROM medicines')}
    if len(existing)!=707:raise ValueError(f'Expected initial 707 records, got {len(existing)}')
    for name in names:
        if existing.get(name) not in ('SADECE İSİM DİZİNİ','FAZ 1 TÜRKÇE TASLAK — DOKTOR / ECZACI ONAYI BEKLİYOR'):
            raise ValueError(f'Not eligible for new phase 1: {name} / {existing.get(name)}')
    common_pregnancy='Gebelik, emzirme, çocuklar ve yaşlılarda uygunluk ürün/form ve hastalığa göre değişir; resmî KÜB/KT ve hekim değerlendirmesi gerekir.'
    groups={}
    for catalog in ('medicines_index.json','medicines_extra.json'):
        for group, entries in json.loads((ROOT/'data'/catalog).read_text(encoding='utf8')).items():
            for entry in entries: groups.setdefault(entry,group)
    for row in rows:
        if row['name'] not in groups: raise ValueError('Category missing for '+row['name'])
        row.update({
            'category':groups[row['name']],
            'generic_name':row['name'], 'active_ingredients':row['name'],
            'inactive_ingredients':'Ürün markası, formu ve üretici bilinmediğinden yardımcı maddeler, laktoz/boya/koruyucu gibi olası alerjenler belirlenemedi. Ambalaj ve güncel KÜB/KT kontrol edilmeli.',
            'pregnancy':CLASS_NOTES.get(row['name'],common_pregnancy),
            'storage':'Saklama sıcaklığı, ışık/nem koşulları ve açıldıktan sonraki süre ürün ve formuna göre değişir; ambalajındaki güncel saklama talimatı esas alınmalıdır.',
            'source':'KALE Faz 1 Türkçe editoryal taslak; ilaç/ürün bazında kaynak doğrulaması yapılmadı',
            'source_url':('https://dailymed.nlm.nih.gov/dailymed/fda/fdaDrugXsl.cfm?setid=9b34b1d8-d125-41a2-9f6f-3fab67b573bd&type=display' if row['name']=='Metotreksat' else ('https://www.fda.gov/consumers/consumer-updates/access-naloxone-can-save-life-during-opioid-overdose' if row['name']=='Nalokson' else 'https://medlineplus.gov/druginformation.html')),
            'source_updated':'', 'locale':'tr', 'phase':1,
            'review_status':'FAZ 1 TÜRKÇE TASLAK — DOKTOR / ECZACI ONAYI BEKLİYOR',
            'medical_review_approved':False,
        })
        row['allergies'] += ' Yardımcı maddelerin alerjenliği markaya ve formülasyona göre değişir; bu envanterde doğrulanmadı.'
        row['warnings'] += ' Bu metin reçete veya uygulama talimatı değildir; doz, hasta uygunluğu ve ürün doğrulaması yapılmadı.'
    OUT.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # Keep 707 fixed drug entries; phase 1 chosen from those missing info, rest divided into nine comparable batches.
    remaining=sorted((n for n in existing if n not in names),key=lambda n:n.casefold())
    batches=[names]
    for i in range(9):
        start=i*len(remaining)//9
        end=(i+1)*len(remaining)//9
        batches.append(remaining[start:end])
    flat=[name for batch in batches for name in batch]
    assert len(flat)==707 and len(set(flat))==707
    PHASES.parent.mkdir(parents=True,exist_ok=True)
    with PHASES.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['faz','sira','ilac_adi','faz_durumu','mevcut_aciklama','doktor_onayi'])
        for p,batch in enumerate(batches,1):
            for ix,n in enumerate(batch,1):
                w.writerow([p,ix,n,'İLK FAZ TAMAMLANDI' if p==1 else 'PLANLANDI',
                    'Yeni Türkçe taslak' if p==1 else ('Eski Türkçe taslak mevcut; yeniden incelenecek' if existing[n]!='SADECE İSİM DİZİNİ' else 'Yalnız isim dizini'),
                    'BEKLİYOR'])
    print('Phase plan:',[len(batch) for batch in batches], 'Rows:',len(flat))
    print('Produced:',OUT,PHASES)

if __name__=='__main__':main()
