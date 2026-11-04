"""KALE ilaç kataloğu: kaynağı ayrıştırılmış, offline ve yayınlanmamış etiket incelemesi gerektirir.
Clinical fields are stored verbatim; never infer a medicine is safe if a field is missing.
"""
import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data/kale.db'
SEED=ROOT/'data/medicines_index.json'
EXTRA=ROOT/'data/medicines_extra.json'
SUMMARIES=ROOT/'data/medicine_summaries_tr.json'
DRAFTS=ROOT/'data/medicine_drafts_tr.json'
PHASE1=ROOT/'data/medicine_phase1_tr.json'
PHASE2=ROOT/'data/medicine_phase2_tr.json'
PHASE3=ROOT/'data/medicine_phase3_tr.json'
PHASE4=ROOT/'data/medicine_phase4_tr.json'
PHASE5=ROOT/'data/medicine_phase5_tr.json'
PHASE6_10=ROOT/'data/medicine_phase6_10_tr.json'

SCHEMA='''
 CREATE TABLE IF NOT EXISTS medicines (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  generic_name TEXT NOT NULL DEFAULT '',
  brand_names TEXT NOT NULL DEFAULT '',
  active_ingredients TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT '',
  indications TEXT NOT NULL DEFAULT '',
  effects TEXT NOT NULL DEFAULT '',
  side_effects TEXT NOT NULL DEFAULT '',
  allergies TEXT NOT NULL DEFAULT '',
  contraindications TEXT NOT NULL DEFAULT '',
  warnings TEXT NOT NULL DEFAULT '',
  interactions TEXT NOT NULL DEFAULT '',
  inactive_ingredients TEXT NOT NULL DEFAULT '',
  pregnancy TEXT NOT NULL DEFAULT '',
  storage TEXT NOT NULL DEFAULT '',
  source TEXT NOT NULL DEFAULT '',
  source_url TEXT NOT NULL DEFAULT '',
  source_updated TEXT NOT NULL DEFAULT '',
  locale TEXT NOT NULL DEFAULT '',
  review_status TEXT NOT NULL DEFAULT '',
  search_text TEXT NOT NULL DEFAULT ''
 );
 CREATE INDEX IF NOT EXISTS idx_medicine_name ON medicines(name);
 CREATE INDEX IF NOT EXISTS idx_medicine_source ON medicines(source);
'''
FIELDS=[ 'id','name','generic_name','brand_names','active_ingredients','category', 'indications',
 'effects','side_effects','allergies','contraindications','warnings','interactions',
 'inactive_ingredients','pregnancy','storage','source','source_url','source_updated','locale',
 'review_status','search_text' ]


def norm(value):
    text=str(value or '').replace('İ','I').replace('ı','i').lower()
    return ''.join(ch for ch in unicodedata.normalize('NFKD',text) if not unicodedata.combining(ch))


def clean(value,limit=12000):
    if isinstance(value,list):value='\n'.join(str(x) for x in value)
    if value is None:return ''
    value=re.sub(r'\s+',' ',str(value)).strip()
    return value[:limit]+('… [Kaynak metin kesildi]' if len(value)>limit else '')


def initialize(conn):
    conn.executescript(SCHEMA)


def put(conn,row):
    row={f:clean(row.get(f,''),limit=20000 if f not in ('name','id','source_url','search_text') else 1600) for f in FIELDS}
    if not row['id'] or not row['name']:return False
    row['search_text']=norm(' '.join((row['name'],row['generic_name'],row['brand_names'],row['active_ingredients'],row['category'])))[:4000]
    conn.execute(f"INSERT OR REPLACE INTO medicines ({','.join(FIELDS)}) VALUES ({','.join('?' for _ in FIELDS)})",[row[f] for f in FIELDS])
    return True


def seed(conn):
    """Name-only drug index. Clinical claims only enter via separate sourced summaries."""
    seen=set();n=0
    for filepath in (SEED,EXTRA):
        indices=json.loads(filepath.read_text(encoding='utf-8'))
        for group,names in indices.items():
            for name in names:
                value=clean(name,160)
                keynorm=norm(value)
                if keynorm in seen:continue
                seen.add(keynorm)
                key='idx_'+hashlib.sha256(keynorm.encode()).hexdigest()[:20]
                if put(conn,{'id':key,'name':value,'generic_name':value,'active_ingredients':value,
                             'category':group,'source':'KALE ilaç adı dizini (bilgi doğrulanmadı)',
                             'locale':'tr','review_status':'SADECE İSİM DİZİNİ'}):n+=1
    return n


def sourced_summaries(conn):
    """Incorporate Turkish clinical draft summaries without implying medical approval.

    Existing individually referenced summaries are distinct from unverified new drafts.
    Neither source_updated nor review date is set until editorial review actually occurs.
    """
    n=0
    for path,status in (
        (SUMMARIES,'KAYNAKLI TÜRKÇE ÖZET — UZMAN ONAYI YOK'),
        (DRAFTS,'TÜRKÇE TASLAK — DOKTOR / ECZACI ONAYI BEKLİYOR'),
        (PHASE1,'FAZ 1 TÜRKÇE TASLAK — DOKTOR / ECZACI ONAYI BEKLİYOR'),
        (PHASE2,'FAZ 2 TÜRKÇE TASLAK — DOKTOR / ECZACI ONAYI BEKLİYOR'),
        (PHASE3,'FAZ 3 TÜRKÇE TASLAK — DOKTOR / ECZACI ONAYI BEKLİYOR'),
        (PHASE4,'FAZ 4 TÜRKÇE TASLAK — DOKTOR / ECZACI ONAYI BEKLİYOR'),
        (PHASE5,'FAZ 5 TÜRKÇE TASLAK — DOKTOR / ECZACI ONAYI BEKLİYOR'),
        (PHASE6_10,'SINIF-TEMELLİ TÜRKÇE TASLAK — DOKTOR / ECZACI ONAYI BEKLİYOR'),
    ):
        if not path.exists():continue
        for rec in json.loads(path.read_text(encoding='utf-8')):
            if not rec.get('source_url','').startswith('https://'):
                raise ValueError(f'İlaç kaynak referansı eksik: {rec.get("name")}')
            key='idx_'+hashlib.sha256(norm(rec['name']).encode()).hexdigest()[:20]
            row={**rec,'id':key,'review_status':status,'locale':'tr',
                 'source_updated':rec.get('source_updated','')}
            if put(conn,row):n+=1
    return n


def label_to_row(rec):
    """Map sections in authentic openFDA drug/label JSON, without translating/summarizing."""
    if not isinstance(rec,dict):return None
    fd=rec.get('openfda') or {}
    def first(key):
        x=fd.get(key) or []
        return clean(x[0],300) if isinstance(x,list) and x else clean(x,300)
    def section(*names):
        return clean('\n'.join(clean(rec.get(x,[]),16000) for x in names if rec.get(x)),16000)
    name=first('brand_name') or first('generic_name') or section('openfda')
    if not name: name=section('active_ingredient')[:200]
    if not name:return None
    setid=clean(rec.get('set_id') or first('spl_set_id'),180)
    rid=clean(rec.get('id'),200)
    if not (setid or rid):
        return None  # retain provenance, don't invent an identifier
    key='fda_'+hashlib.sha256((setid or rid).encode()).hexdigest()[:24]
    effective=clean(rec.get('effective_time',''),20)
    if len(effective)==8 and effective.isdigit():effective=f'{effective[:4]}-{effective[4:6]}-{effective[6:]}'
    return {
       'id':key,'name':name,'generic_name':first('generic_name'),
       'brand_names':clean(fd.get('brand_name',[]),1500),
       'active_ingredients': section('active_ingredient') or clean(fd.get('substance_name',[]),500),
       'category':clean(fd.get('product_type',[]),180),
       'indications':section('indications_and_usage','uses'),
       'effects':section('purpose','clinical_pharmacology'),
       'side_effects':section('adverse_reactions','when_using'),
       'allergies':section('do_not_use','allergy'),
       'contraindications':section('contraindications','ask_doctor'),
       'warnings':section('boxed_warning','warnings','warnings_and_cautions','ask_doctor_or_pharmacist','stop_use'),
       'interactions':section('drug_interactions'),
       'inactive_ingredients':section('inactive_ingredient','inactive_ingredient_table'),
       'pregnancy':section('pregnancy','pregnancy_or_breast_feeding','use_in_specific_populations'),
       'storage':section('storage_and_handling'),
       'source':'openFDA / ABD ürün etiketi (İngilizce, klinik incelemesiz)',
       'source_url':f'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={setid}' if re.fullmatch(r'[0-9a-fA-F-]{36}',setid) else 'https://open.fda.gov/apis/drug/label/',
       'source_updated':effective,'locale':'en',
       'review_status':'KAYNAK ETİKETİ — UZMAN İNCELEMESİ YOK',
    }
