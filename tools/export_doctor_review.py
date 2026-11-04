#!/usr/bin/env python3
"""Create independent physician/pharmacist signoff checklist.
Reviewer notes never mutate or certify the live medication database.
"""
import csv
import json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
SRC=[BASE/'data/medicine_summaries_tr.json',BASE/'data/medicine_drafts_tr.json', BASE/'data/medicine_phase1_tr.json', BASE/'data/medicine_phase2_tr.json', BASE/'data/medicine_phase3_tr.json', BASE/'data/medicine_phase4_tr.json', BASE/'data/medicine_phase5_tr.json',BASE/'data/medicine_phase6_10_tr.json']
OUT=BASE/'review'/'doktor_kontrol_listesi.csv'
FIELDS=['phase','name','category','indications','effects','side_effects','allergies','contraindications',
        'interactions','warnings','pregnancy','inactive_ingredients','storage','source','source_url','reviewer_name','reviewer_profession',
        'turkish_kub_url','manufacturer_form_strength_checked','indications_checked','side_effects_checked',
        'allergies_and_inactive_ingredients_checked','contraindications_checked','interactions_checked',
        'pregnancy_children_checked','clinical_decision_APPROVE_REVISE_REJECT','reviewer_notes','review_date']
rows_by_name={}
for source in SRC:
    for row in json.loads(source.read_text(encoding='utf8')):
        rows_by_name[row['name']]={key:row.get(key,'') for key in FIELDS}
with (BASE/'review'/'ilac_10_faz_plani.csv').open(encoding='utf-8-sig',newline='') as f:
    phases={r['ilac_adi']:r['faz'] for r in csv.DictReader(f)}
for name,row in rows_by_name.items():row['phase']=phases.get(name,row.get('phase',''))
rows=list(rows_by_name.values())
OUT.parent.mkdir(exist_ok=True)
with OUT.open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS)
    w.writeheader();w.writerows(rows)
readme=OUT.parent/'DOKTOR_INCELEME_NOTU.txt'
readme.write_text('''KALE İLAÇ KAYITLARI — SAĞLIK PROFESYONELİ İNCELEME PAKETİ

Bu CSV 707 katalog kaydının Türkçe editoryal ön taslaklarını incelemek içindir. Son 303 kayıt yalnızca farmakolojik sınıf düzeyinde özetlenmiştir; ilaç-ürün etiketleriyle eşleştirilmemiştir. Kayıtların hiçbiri doktor onaylı değildir.
Kaynak URL'si genel referans sayfası olabilir; her ilaç için ürün-özgü güncel Türkiye KÜB/KT
metnini ve üretici, form, güç, etken madde ve yardımcı maddelerini bağımsız kontrol edin.

Karar alanı: APPROVE / REVISE / REJECT. Boş bırakılan alan onay değildir.
Tıbbi incelemede bağımsız kaynak URL'si, hekim/eczacı adı, tarih ve gerektiğinde düzeltme
notu kaydedilmelidir. Bu CSV tek başına KALE veritabanındaki onay durumunu DEĞİŞTİRMEZ.
Hasta bazlı tanı, reçete, doz ve ilaç önerisi için kullanılmaz.

Özellikle kritik: gebelik/emzirme, çocuklar, renal/hepatik bozukluklar, alerji,
ürün yardımcı maddeleri, etkileşimler, acil endikasyon ve benzer isimli ilaçlar.
''',encoding='utf8')
print('Review rows:',len(rows),'CSV:',OUT)
