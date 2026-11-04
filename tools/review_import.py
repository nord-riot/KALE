#!/usr/bin/env python3
"""KALE doctor-review importer. Python stdlib only; no network; no web write API.

Reads the specific KALE 707-medication Excel template (OOXML). Review metadata
is stored in a separate database. It NEVER changes clinical draft text and
NEVER treats a spreadsheet cell as independently verified medical advice.
"""
import argparse
import csv
import hashlib
import json
import posixpath
import re
import sqlite3
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MAIN_DB = ROOT / 'data' / 'kale.db'
REVIEWS_DB = ROOT / 'data' / 'doctor_reviews.sqlite3'
NS = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      'p': 'http://schemas.openxmlformats.org/package/2006/relationships'}
MAIN = '{'+NS['x']+'}'
REVIEW_COLS = {'K':'indications','L':'effects','M':'side_effects','N':'allergies',
               'O':'contraindications','P':'interactions','Q':'warnings',
               'R':'pregnancy','S':'inactive_ingredients','T':'storage'}
DECISIONS = {'ONAYLA': 'ONAYLA', 'ONAYLANDI': 'ONAYLA', 'ONAY': 'ONAYLA',
             'DÜZELT': 'DÜZELT', 'DÜZELTİLECEK': 'DÜZELT', 'REDDET': 'REDDET',
             'RED': 'REDDET', 'BEKLİYOR': '', '': ''}


def norm(v):
    return ' '.join(str(v if v is not None else '').strip().split())


def normalized_status(v):
    return norm(v).upper().replace('İ','İ')


def content_hash(m):
    record={k:str(m[k] or '') for k in ['id','name',*REVIEW_COLS.values()]}
    return hashlib.sha256(json.dumps(record,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def get_cells_from_xlsx(path):
    path=Path(path)
    if path.stat().st_size>25_000_000:
        raise ValueError('Excel dosyası izin verilen boyuttan büyük.')
    with zipfile.ZipFile(path) as z:
        try:
            work=ET.fromstring(z.read('xl/workbook.xml'))
            rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        except KeyError as e:raise ValueError('Geçersiz Excel paketi') from e
        rel_map={r.attrib['Id']:r.attrib['Target'] for r in rels}
        sheet=None
        for s in work.findall('x:sheets/x:sheet',NS):
            if s.attrib.get('name')=='DOKTOR LİSTESİ':sheet=s
        if sheet is None:raise ValueError('DOKTOR LİSTESİ adlı çalışma sayfası bulunamadı.')
        rel_id=sheet.attrib['{'+NS['r']+'}id']
        target=rel_map[rel_id].lstrip('/')
        if not target.startswith('xl/'):
            target=posixpath.normpath('xl/'+target)
        if not target.startswith('xl/worksheets/'):
            raise ValueError('Excel çalışma sayfası yolu geçersiz.')
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            strings=ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in strings.findall('x:si',NS):
                shared.append(''.join(t.text or '' for t in si.findall('.//x:t',NS)))
        root=ET.fromstring(z.read(target))
        records=[]
        for row in root.findall('x:sheetData/x:row',NS):
            number=int(row.attrib.get('r','0'))
            if number<7:continue
            if number>10000:raise ValueError('Fazla Excel satırı; beklenen en fazla 707 kayıt.')
            d={}
            for cell in row.findall('x:c',NS):
                address=cell.attrib.get('r','')
                match=re.match(r'^([A-Z]{1,3})\d+$',address)
                if not match:continue
                key=match.group(1)
                if key not in {'B','F','G','H','I','X','Y','AA',*REVIEW_COLS}:continue
                typ=cell.attrib.get('t')
                if typ=='inlineStr':
                    obj=cell.find('x:is',NS)
                    value=''.join(t.text or '' for t in obj.findall('.//x:t',NS)) if obj is not None else ''
                else:
                    element=cell.find('x:v',NS)
                    value=(element.text or '') if element is not None else ''
                    if typ=='s' and value:value=shared[int(value)]
                d[key]=value
            if d.get('Y'):
                records.append(d)
        return records


def parse_date(raw):
    val=norm(raw)
    if not val:raise ValueError('İnceleme tarihi eksik')
    if re.fullmatch(r'\d{4,5}(?:\.0)?',val):
        day=(datetime(1899,12,30)+timedelta(days=int(float(val)))).date()
    else:
        day=None
        for fmt in ('%Y-%m-%d','%d.%m.%Y','%d/%m/%Y','%d-%m-%Y'):
            try:day=datetime.strptime(val,fmt).date();break
            except ValueError:pass
        if day is None:raise ValueError('Tarih YYYY-MM-DD veya GG.AA.YYYY olmalı')
    if day.year<2020 or day>datetime.now(timezone.utc).date()+timedelta(days=1):
        raise ValueError('İnceleme tarihi gerçekçi aralıkta değil')
    return day.isoformat()


def validate_records(rows, medicines):
    if len(rows)!=len(medicines):
        raise ValueError(f'Excel {len(rows)} kayıt içeriyor; KALE kataloğu {len(medicines)} kayıt içeriyor. Yanlış ya da eksik sürüm.')
    errors=[];changes=[];seen=set()
    for row in rows:
        mid=norm(row.get('Y'))
        if mid in seen:errors.append('Mükerrer kayıt ID: '+mid);continue
        seen.add(mid)
        m=medicines.get(mid)
        if m is None:errors.append('Katalogda olmayan kayıt: '+mid);continue
        if norm(row.get('B'))!=norm(m['name']):errors.append(m['name']+': Excel adı uyuşmuyor');continue
        state=normalized_status(row.get('F'))
        decision=DECISIONS.get(state)
        if decision is None:errors.append(m['name']+': geçersiz doktor kararı '+state);continue
        if not decision:continue
        # Reject reviews against stale or modified drafts. Doctor corrections belong in the notes;
        # the underlying medical text must be separately updated and reviewed again.
        for col,field in REVIEW_COLS.items():
            if norm(row.get(col))!=norm(m[field]):
                errors.append(m['name']+': '+col+' klinik taslak alanı katalogla eşleşmiyor');break
        else:
            reviewer=norm(row.get('G'));notes=norm(row.get('I'))
            if len(reviewer)<5:errors.append(m['name']+': hekim/eczacı ismi eksik');continue
            try:review_date=parse_date(row.get('H'))
            except ValueError as e:errors.append(m['name']+': '+str(e));continue
            if len(notes)<10:errors.append(m['name']+': klinik değerlendirme notu (en az 10 karakter) gerekli');continue
            doc=norm(row.get('X'))
            doc_status=normalized_status(row.get('AA'))
            if decision=='ONAYLA':
                if len(doc)<12 or 'medlineplus.gov/druginformation' in doc.lower():
                    errors.append(m['name']+': Onay için ürüne özgü KÜB/KT belge bağlantısı veya belge kodu gerekiyor');continue
                if doc_status not in ('DOĞRULANDI','TAMAM','KONTROL EDİLDİ'):
                    errors.append(m['name']+': Onay için KÜB/KT kontrol durumu DOĞRULANDI olmalı');continue
            changes.append({'medicine_id':mid,'name':m['name'],'decision':decision,
                'reviewer':reviewer,'reviewed_on':review_date,'note':notes,
                'product_document':doc,'document_checked':doc_status,
                'draft_sha256':content_hash(m)})
    if seen!=set(medicines):errors.append('Excel kayıtları KALE katalog ID kümesiyle eşleşmiyor')
    if errors:raise ValueError('İçe aktarma iptal edildi ('+str(len(errors))+' hata):\n - '+'\n - '.join(errors[:25]))
    return changes


def init_review_db(db):
    with sqlite3.connect(db) as c:
        c.execute('''CREATE TABLE IF NOT EXISTS doctor_reviews (
            medicine_id TEXT PRIMARY KEY, decision TEXT NOT NULL,
            reviewer TEXT NOT NULL, reviewed_on TEXT NOT NULL,
            note TEXT NOT NULL, product_document TEXT NOT NULL,
            document_checked TEXT NOT NULL, draft_sha256 TEXT NOT NULL,
            imported_at TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS review_audit (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,medicine_id TEXT NOT NULL,
            previous_decision TEXT,decision TEXT NOT NULL,imported_at TEXT NOT NULL,
            source_file TEXT NOT NULL,draft_sha256 TEXT NOT NULL)''')


def save_reviews(db,changes,filename):
    init_review_db(db)
    now=datetime.now(timezone.utc).isoformat(timespec='seconds')
    updates=0
    with sqlite3.connect(db) as c:
        for r in changes:
            prev=c.execute('SELECT decision,reviewer,reviewed_on,note,product_document,document_checked,draft_sha256 FROM doctor_reviews WHERE medicine_id=?',(r['medicine_id'],)).fetchone()
            values=tuple(r[k] for k in ('decision','reviewer','reviewed_on','note','product_document','document_checked','draft_sha256'))
            if prev==values:continue
            c.execute('''INSERT INTO doctor_reviews VALUES(?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(medicine_id) DO UPDATE SET decision=excluded.decision,
                       reviewer=excluded.reviewer, reviewed_on=excluded.reviewed_on,
                       note=excluded.note,product_document=excluded.product_document,
                       document_checked=excluded.document_checked,
                       draft_sha256=excluded.draft_sha256, imported_at=excluded.imported_at''',
                (r['medicine_id'],*values,now))
            c.execute('INSERT INTO review_audit(medicine_id,previous_decision,decision,imported_at,source_file,draft_sha256) VALUES(?,?,?,?,?,?)',
                (r['medicine_id'],prev[0] if prev else None,r['decision'],now,filename,r['draft_sha256']))
            updates+=1
    return updates


def csv_guard(value):
    s=str(value if value is not None else '')
    return "'"+s if s.lstrip().startswith(('=','+','-','@','\t','\r')) else s


def export_audit(db,dest):
    if not db.exists():raise ValueError('İnceleme veritabanı bulunamadı')
    with sqlite3.connect(db) as c,open(dest,'w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f)
        writer.writerow(['KALE kayıt ID','Karar','İnceleyen','İnceleme tarihi','Doktor notu','Ürün belgesi','KÜB/KT kontrolü','Metin parmak izi','İçe aktarım tarihi'])
        for r in c.execute('SELECT * FROM doctor_reviews ORDER BY medicine_id'):
            writer.writerow([csv_guard(x) for x in r])


def main():
    p=argparse.ArgumentParser(description='KALE doktor Excel inceleme kararlarını offline doğrular/aktarır')
    p.add_argument('xlsx',nargs='?',help='KALE_707_Ilac_Doktor_Inceleme_Formatli.xlsx')
    p.add_argument('--apply',action='store_true',help='Kontrol edilen kararları yan inceleme DB içine yaz')
    p.add_argument('--export-audit',metavar='CSV',help='Yan inceleme DB kayıtlarını CSV dışa aktar')
    args=p.parse_args()
    if args.export_audit:
        export_audit(REVIEWS_DB,args.export_audit)
        print('İnceleme listesi dışa aktarıldı:',args.export_audit);return
    if not args.xlsx:p.error('Excel dosyası gerekli')
    with sqlite3.connect(f'file:{MAIN_DB}?mode=ro',uri=True) as c:
        c.row_factory=sqlite3.Row
        medicines={r['id']:dict(r) for r in c.execute('SELECT * FROM medicines')}
    rows=get_cells_from_xlsx(args.xlsx)
    changes=validate_records(rows,medicines)
    counts={k:sum(x['decision']==k for x in changes) for k in ('ONAYLA','DÜZELT','REDDET')}
    print(f'Excel: {len(rows)} ilaç; işaretlenmiş inceleme: {len(changes)}; kararlar: {counts}')
    if not args.apply:
        print('ÖN İNCELEME — Veritabanında değişiklik yapılmadı. Uygulamak için --apply ekleyin.')
    else:
        n=save_reviews(REVIEWS_DB,changes,Path(args.xlsx).name)
        print(f'{n} inceleme kararı kaydedildi. Klinik ilaç metinleri DEĞİŞMEDİ. Yan DB: {REVIEWS_DB}')


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,sqlite3.Error,zipfile.BadZipFile,ET.ParseError) as e:
        print('HATA:',e,file=sys.stderr);sys.exit(2)
