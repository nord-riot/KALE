#!/usr/bin/env python3
"""Translate/editorially summarize the *planned* 212 phase 3-5 medicines in Turkish.

NEVER certifies safety, dosage, brand matching, excipients, product labels or medical approval.
Seven fields are independently written per medicine; subsequent fields say explicitly
when no product-verified information is available.
"""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/phase3_5_editorial_source.psv'
PLAN=ROOT/'review/ilac_10_faz_plani.csv'
COLUMNS=('name','indications','effects','side_effects','contraindications','interactions','warnings')
COUNTS={3:71,4:71,5:70}
SPECIAL_SOURCE={
 'Clozapin':'https://medlineplus.gov/druginfo/meds/a691001.html',
 'Dabigatran':'https://medlineplus.gov/druginfo/meds/a610024.html'
}
# The following are editorial triage cues, not certified contraindication lists.
FETAL_DAMAGE={'Enalapril','Eprosartan','Fosinopril','İrbesartan','İzotretinoin','Griseofulvin','Ergotamin','Etinilestradiol','Fluorourasil','Kapetsitabin','Dasatinib','Eksimestan'}
HIGH_RISK_TERMS=('HASTANE','ONKOLOJİ','KEMOTERAPİ','OPİOİD','YÜKSEK RİSK','ÇOK YÜKSEK RİSK','YOĞUN BAKIM','ANTİDOT','KAN SULANDIRICI','ANTİPLATELET','KONTROLLÜ İLAÇ')
NAME_OVERRIDE={
 'Gepant':'Gepant ilaç sınıfı (tek etken madde değildir)',
 'Gonadotropin':'Gonadotropin ilaç sınıfı (tek etken madde değildir)',
 'Fluokinonid':'Etken madde adı doğrulama bekliyor (fluosinonid ile karışma riski)',
 'Klopidogrel bisülfat':'Klopidogrel (bisülfat tuzu; bağımsız ikinci etken madde değil)',
 'Fenobarbital sodyum':'Fenobarbital (sodyum tuzu, ürün formu doğrulanmalı)'
}
FORM_HINTS={'Budesonid inhaler':'İnhaler form; ağızdan alınan budesonidle karıştırılmamalı',
 'Budesonid rektal':'Rektal form; inhaler ile farklı kullanım',
 'Deksametazon göz damlası':'Göz damlası; sistemik tablet/ampulle karıştırılmamalı',
 'Dapson jel':'Cilt jeli; sistemik dapsondan farklı maruziyet',
 'Hidrokortizon krem':'Topikal krem; sistemik hidrokortizondan farklı',
 'Ketokonazol şampuan':'Şampuan; ağızdan ketokonazol ile farklı',
 'Klopidogrel bisülfat':'Klopidogrel tuz biçimi; çift doz riski',
 'İnsülin aspart':'Hızlı etkili insülin',
 'İnsülin lispro':'Hızlı etkili insülin',
 'İnsülin glulisin':'Hızlı etkili insülin',
 'İnsülin regular':'Kısa etkili insülin',
 'İnsülin glarjin':'Uzun etkili bazal insülin',
 'İnsülin degludek':'Çok uzun etkili bazal insülin',
 'İnsülin detemir':'Uzun etkili bazal insülin',
 'İnsülin NPH':'Orta etkili insülin süspansiyonu'}

def main():
    with PLAN.open(encoding='utf-8-sig',newline='') as f:
        planned=list(csv.DictReader(f))
    assert len(planned)==707
    planned_by_phase={p:[r['ilac_adi'] for r in planned if int(r['faz'])==p] for p in COUNTS}
    parsed=[]
    for line_no,line in enumerate(SRC.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip():continue
        parts=line.split('|')
        if len(parts)!=len(COLUMNS):raise ValueError(f'{line_no}: {len(parts)} fields, expected {len(COLUMNS)}')
        x={k:v.strip() for k,v in zip(COLUMNS,parts)}
        if any(len(x[k]) < (3 if k=='name' else 30) for k in COLUMNS):
            raise ValueError(f'{line_no}: short or empty editorial field')
        if any('doz olarak' in x[k].lower() for k in COLUMNS):
            raise ValueError(f'{line_no}: please avoid dose instructions')
        parsed.append(x)
    expected=sum((planned_by_phase[p] for p in COUNTS),[])
    names=[x['name'] for x in parsed]
    if names!=expected:
        raise ValueError('Phase names do not match frozen 707-row plan (check order, spelling and count)')
    groups={}
    for file in ('medicines_index.json','medicines_extra.json'):
        for group, entries in json.loads((ROOT/'data'/file).read_text(encoding='utf8')).items():
            for name in entries: groups.setdefault(name,group)
    assert len(set(names))==212
    for phase,qty in COUNTS.items():
        rows=[]
        for x in parsed[sum(COUNTS[p] for p in COUNTS if p<phase):sum(COUNTS[p] for p in COUNTS if p<=phase)]:
            name=x['name']
            source_url=SPECIAL_SOURCE.get(name,'https://medlineplus.gov/druginformation.html')
            common='Gebelik, emzirme, çocuklar ve özel hasta gruplarında güvenlilik ürünün güncel KÜB/KT metniyle ve uzman tarafından ayrıca değerlendirilmelidir.'
            if name in FETAL_DAMAGE:
                common='Gebelikte ciddi risk veya kullanım yasağı söz konusu olabilir; ürün özelinde kesin uyarı ve gebelik planı uzman tarafından doğrulanmalıdır.'
            if name.startswith('İnsülin'):
                common='Gebelikte insülin tedavisi gerektiğinde izlem bireyselleştirilir; farklı insülin türleri kendi kendine değiştirilmez.'
            warning=x['warnings']
            if any(t in warning.upper() for t in HIGH_RISK_TERMS):
                warning='YÜKSEK ÖNCELİKLİ UYARI: '+warning
            if name in FORM_HINTS: warning+=' FORM AYRIMI: '+FORM_HINTS[name]+'.'
            rows.append({
                **x,'category':groups.get(name,'İlaç ve tedavi kayıtları'),
                'generic_name':NAME_OVERRIDE.get(name,name),
                'active_ingredients':NAME_OVERRIDE.get(name,name),
                'allergies':f'{name} veya gerçek ürünün herhangi bir yardımcı maddesine karşı daha önce ciddi alerjik reaksiyon varsa kullanılmamalıdır. Aynı ilaç ailesine geçmiş anafilaksi öyküsü mutlaka incelenmelidir. Bu kayıtta ürüne özgü alerjen listesi bulunmuyor.',
                'inactive_ingredients':'Üretici, marka, tuz, dozaj formu ve güç belirtilmedi. Laktoz, jelatin, boya, koruyucu ve diğer yardımcı maddeler ürün bazında doğrulanmadı; alerjen var/yok kararı verilemez.',
                'pregnancy':common,
                'storage':'Saklama sıcaklığı, soğuk zincir gereksinimi, açıldıktan sonra kullanım süresi ve son kullanma tarihi ürün formu/ambalajına göre doğrulanmalıdır.',
                'warnings':warning+' Bu açıklama klinik doğrulama bekleyen Türkçe editoryal taslaktır; etiket, reçete, güvenli ilaç seçimi veya doz talimatı değildir.',
                'source':f'KALE Faz {phase} Türkçe editoryal taslak — ilaca özel Türkiye KÜB/KT ve tam klinik doğrulama yapılmadı',
                'source_url':source_url,'source_updated':'','locale':'tr','phase':phase,
                'review_status':f'FAZ {phase} TÜRKÇE TASLAK — DOKTOR / ECZACI ONAYI BEKLİYOR',
                'medical_review_approved':False
            })
        assert len(rows)==qty and {x['name'] for x in rows}==set(planned_by_phase[phase])
        dest=ROOT/'data'/f'medicine_phase{phase}_tr.json'
        dest.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for r in planned:
        if int(r['faz']) in COUNTS:
            p=int(r['faz'])
            r['faz_durumu']=f'FAZ {p} TÜRKÇE TASLAK TAMAMLANDI — DOKTOR ONAYI YOK'
            r['mevcut_aciklama']='Yeni veya yeniden yazılmış Türkçe editoryal taslak — ürün doğrulaması bekliyor'
    with PLAN.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=planned[0].keys());writer.writeheader();writer.writerows(planned)
    print('Phases 3/4/5 OK:',COUNTS,'Total 212 entries, no medical approvals')

if __name__=='__main__':main()
