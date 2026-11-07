#!/usr/bin/env python3
"""Import official medicine registries into a *separate* offline KALE database.

Live sources: openFDA labels (targeted by existing generic names), Canada DPD.
Offline exports: FDA zipped JSON, and official CSV/XLSX from the 9 agencies.
No login scraping, no inferred authorization, no clinical substitutions.

Examples:
  python3 tools/regulatory_sync.py fda --max-terms 200
  python3 tools/regulatory_sync.py canada
  python3 tools/regulatory_sync.py import --regulator EMA --file Article57.xlsx
  python3 tools/regulatory_sync.py fda-json --file ~/Downloads/fda-labels/
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from regulatory_core import AGENCIES, DB, open_writer, write_record

HTTP_LIMIT=90_000_000
FIELD_LIMIT=12000
FDA_URL="https://api.fda.gov/drug/label.json"
CANADA_BASE="https://health-products.canada.ca/api/drug/"
ALIASES={"parasetamol":"acetaminophen","asetaminofen":"acetaminophen",
         "adrenalin":"epinephrine","salbutamol":"albuterol"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def download_json(url, byte_limit=HTTP_LIMIT):
    if not url.startswith(("https://api.fda.gov/","https://health-products.canada.ca/api/drug/")):
        raise ValueError("Sadece sabit resmi API adresleri destekleniyor")
    req=urllib.request.Request(url,headers={"User-Agent":"KALE-Regulatory-Offline-Importer/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as response:
        length=response.headers.get("Content-Length","")
        if length.isdigit() and int(length)>byte_limit:
            raise ValueError("Resmi API yaniti bellek sinirini asiyor")
        data=response.read(byte_limit+1)
    if len(data)>byte_limit:
        raise ValueError("Resmi API yaniti cok buyuk")
    return json.loads(data)


def fda_label_to_row(item):
    if not isinstance(item,dict):
        return None
    meta=item.get("openfda") or {}
    def join(x):
        if isinstance(x,list):
            return ", ".join(str(v) for v in x[:15])
        return str(x or "")
    name=join(meta.get("brand_name") or meta.get("generic_name") or item.get("purpose"))
    ingredient=join(meta.get("generic_name") or meta.get("substance_name"))
    if not name:
        return None
    ref=str(item.get("set_id") or item.get("id") or "")
    if not ref:
        return None
    sections={}
    fields=("indications_and_usage","purpose","warnings","boxed_warning",
            "do_not_use","when_using","contraindications","adverse_reactions",
            "drug_interactions","pregnancy","nursing_mothers","pediatric_use",
            "geriatric_use","storage_and_handling","inactive_ingredient",
            "dosage_and_administration","stop_use","ask_doctor")
    for field in fields:
        value=item.get(field)
        if isinstance(value,list):
            sections[field]="\n\n".join(str(x) for x in value[:15])[:FIELD_LIMIT]
        elif isinstance(value,str):
            sections[field]=value[:FIELD_LIMIT]
    return dict(regulator="FDA",source_id=ref,name=name,ingredients=ingredient,
      status="ABD resmi etiket kaydı; FDA ruhsat statüsü bu veriden doğrulanmadı",
      market="ABD",updated=str(item.get("effective_time") or ""),
      url="https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid="+urllib.parse.quote(ref),
      kind="FDA SPL drug label (raw English)",
      form=join(meta.get("dosage_form")),sections=sections)


def fda_targets(db_path, limit):
    # The existing clinical data is read-only. Never attempt to rewrite it.
    if not db_path.is_file():
        raise FileNotFoundError("Mevcut KALE ilaç DB bulunamadı: "+str(db_path))
    with sqlite3.connect("file:"+str(db_path)+"?mode=ro",uri=True) as con:
        names=[str(x[0] or "").strip() for x in con.execute(
            "SELECT DISTINCT generic_name FROM medicines WHERE trim(generic_name)<>'' ORDER BY generic_name")]
    targets=[]
    seen=set()
    for n in names:
        if len(n)>65 or len(n)<3 or any(c in n for c in "\n\r;|"):
            continue
        norm=n.casefold()
        norm=ALIASES.get(norm,n)
        if norm.casefold() in seen:
            continue
        seen.add(norm.casefold())
        targets.append(norm)
        if limit and len(targets)>=limit:
            break
    return targets


def query_fda_label(term,key=""):
    # API can return broad results, but they are stored as unverified
    # source candidates and are NOT merged into a Turkish drug record.
    q='openfda.generic_name:"'+term.replace('"',"")+'"'
    args={"search":q,"limit":"5"}
    if key:
        args["api_key"]=key
    url=FDA_URL+"?"+urllib.parse.urlencode(args)
    try:
        data=download_json(url,5_000_000)
    except urllib.error.HTTPError as e:
        if e.code==404:
            return []
        raise
    return [x for x in data.get("results",[]) if isinstance(x,dict)]


def do_fda(conn, max_terms, api_key, pause):
    terms=fda_targets(ROOT/"data/kale.db",max_terms)
    print("KALE mevcut ilaç adları:",len(terms),"arama — FDA etiketi ABD için")
    count=0
    fails=0
    quota_hit=False
    for i,term in enumerate(terms,1):
        try:
            for label in query_fda_label(term,api_key):
                row=fda_label_to_row(label)
                if row and write_record(conn,imported_at=now(),**row):
                    count+=1
            if i%20==0:
                conn.commit()
                print(f"FDA {i}/{len(terms)} sorgu, {count} kaynak kaydı")
        except urllib.error.HTTPError as exc:
            if exc.code in (429,403):
                print("FDA kota / yetki hatası; mevcut kayıtlar korunuyor:",exc, file=sys.stderr)
                quota_hit=True
                break
            fails+=1
            print("FDA isteği başarısız:",term,exc, file=sys.stderr)
        except (urllib.error.URLError,ValueError,TimeoutError) as exc:
            fails+=1
            print("FDA erişilemedi:",term,exc,file=sys.stderr)
        time.sleep(max(.05,pause))
    conn.commit()
    return count, "KISMİ — kota veya ağ hatası" if (fails or quota_hit) else "Sorgular bitti; birebir eşleşme doğrulanmadı"


def canada_rows():
    def get(kind):
        endpoint=CANADA_BASE+kind+"/?lang=en&type=json"
        result=download_json(endpoint,HTTP_LIMIT)
        return result if isinstance(result,list) else [result]
    print("Health Canada DPD: ürün verileri alınıyor...")
    products=get("drugproduct")
    print("Health Canada ürün sayısı:",len(products))
    print("Health Canada: etkin maddeler alınıyor...")
    ingredients=get("activeingredient")
    print("Health Canada: ürün statüleri alınıyor...")
    statuses=get("status")
    by_ingredient=defaultdict(list)
    by_status={}
    for x in ingredients:
        if not isinstance(x,dict):
            continue
        code=str(x.get("drug_code") or "")
        ing=str(x.get("ingredient_name") or "")
        if code and ing:
            by_ingredient[code].append(ing+" "+str(x.get("strength") or "")+" "+str(x.get("strength_unit") or ""))
    for x in statuses:
        if isinstance(x,dict) and x.get("drug_code"):
            by_status[str(x["drug_code"])]=str(x.get("status") or "")
    for x in products:
        if not isinstance(x,dict) or not x.get("drug_code"):
            continue
        # DPD also covers animals/disinfectants. Keep human medicines only.
        if str(x.get("class_name") or "").strip().lower()!="human":
            continue
        code=str(x["drug_code"])
        din=str(x.get("drug_identification_number") or "")
        status=by_status.get(code) or "Kanada ruhsat durumu belirtilmedi"
        product=str(x.get("brand_name") or "").strip()
        if not product:
            continue
        yield dict(regulator="HEALTH_CANADA",source_id="DPD-"+code,
          name=product,ingredients="; ".join(by_ingredient[code])[:500],
          status=status,market="Kanada",updated=str(x.get("last_update_date") or ""),
          url="https://health-products.canada.ca/dpd-bdpp/",
          kind="Health Canada DPD (Human)",
          sections={"drug_identification_number":din,
                    "company":str(x.get("company_name") or ""),
                    "descriptor":str(x.get("descriptor") or ""),
                    "drug_product_code":code})


def do_canada(conn):
    count=0
    for row in canada_rows():
        if write_record(conn,imported_at=now(),**row):
            count+=1
        if count%5000==0 and count:
            conn.commit()
            print("Kanada ürünleri kaydedildi:",count)
    conn.commit()
    return count,"DPD kaynak kaydı aktarıldı; Türkiye ürün eşdeğerliği doğrulanmadı"


def read_csv(path):
    # Official exports can have UTF-8 BOM or occasionally semicolon-separated CSV.
    with path.open("r",encoding="utf-8-sig",errors="replace",newline="") as f:
        sample=f.read(4096)
        f.seek(0)
        try:
            dialect=csv.Sniffer().sniff(sample,delimiters=",;\t")
        except csv.Error:
            dialect="excel"
        yield from csv.DictReader(f,dialect=dialect)


def read_xlsx(path):
    # XLSX reader uses stdlib only (no pandas/LibreOffice required on Termux).
    ns="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(path) as z:
        texts=[]
        if "xl/sharedStrings.xml" in z.namelist():
            with z.open("xl/sharedStrings.xml") as src:
                for event,element in ET.iterparse(src,events=("end",)):
                    if element.tag==ns+"si":
                        texts.append("".join(n.text or "" for n in element.iter(ns+"t")))
                        element.clear()
        sheets=sorted(p for p in z.namelist() if p.startswith("xl/worksheets/sheet") and p.endswith(".xml"))
        if not sheets:
            raise ValueError("XLSX içinde çalışma sayfası bulunamadı")
        with z.open(sheets[0]) as src:
            header=None
            for event,element in ET.iterparse(src,events=("end",)):
                if element.tag!=ns+"row":
                    continue
                values={}
                for cell in element.findall(ns+"c"):
                    ref=cell.get("r") or "A1"
                    letters="".join(c for c in ref if c.isalpha())
                    ix=0
                    for ch in letters.upper():
                        ix=ix*26+ord(ch)-64
                    ix-=1
                    v=cell.find(ns+"v")
                    inline=cell.find(ns+"is")
                    text=v.text if v is not None and v.text else ""
                    if cell.get("t")=="s" and text.isdigit():
                        num=int(text)
                        text=texts[num] if num<len(texts) else ""
                    if inline is not None:
                        text="".join(n.text or "" for n in inline.iter(ns+"t"))
                    if 0<=ix<120:
                        values[ix]=str(text)
                if header is None:
                    # EMA exports can have several title/metadata rows.
                    words=" ".join(values.values()).lower()
                    if len(values)<3 or not any(a in words for a in ("product","medicine","trade name","brand name","ürün","ilaç","active substance","scientific name","inn")):
                        element.clear()
                        continue
                    header=[values.get(i,"") for i in range(max(values)+1)]
                else:
                    row={name:values.get(i,"") for i,name in enumerate(header) if name}
                    if any(row.values()):
                        yield row
                element.clear()


FIELDS={
 "name":("product name","product short name","medicine name","medicinal product","trade name",
         "brand name","brand_name","artg name","name of medicine","ilaç adı","urun adi",
         "ürün adı","tradeName","prequalified product","product"),
 "ingredient":("active substance","active ingredient","active substances","active substance(s)",
               "active ingredient name","scientific name","scientificname","generic name",
               "inn","inn name","inn, dosage form and strength","etkin madde","etken madde","generic_name","active_substance"),
 "code":("registration number","authorization number","marketing authorisation number",
         "marketing authorization number","ruhsat no","ruhsat numarası","pl number",
         "register number","regno","artg number","who reference number",
         "approval number","product licence","license number","drug_identification_number"),
 "status":("authorisation status","authorization status","marketing status",
           "product status","status","ruhsat durumu","approval status","licence status"),
 "form":("pharmaceutical form","dosage form","form","route of administration",
         "pharmaceuticalform","dosage_form"),
 "market":("country of authorisation","country of authorization","country","market"),
 "updated":("date","updated","date of authorisation","date of authorization",
             "approval date","küb onay tarihi","kt onay tarihi","last update date"),
 "url":("product url","source url","document url","url","link","kub document",
         "kt document","küb dokümanı","kt dokümanı"),
}

def norm(s):
    return " ".join(str(s or "").casefold().replace("_"," ").split())


def pick(row,aliases):
    clean={norm(k):str(v or "").strip() for k,v in row.items()}
    for alias in aliases:
        if norm(alias) in clean and clean[norm(alias)]:
            return clean[norm(alias)]
    for alias in aliases:
        for key,val in clean.items():
            if key.startswith(norm(alias)) and val:
                return val
    return ""


def generic_row(data,regulator):
    name=pick(data,FIELDS["name"])
    if not name:
        return None
    ingredient=pick(data,FIELDS["ingredient"])
    form=pick(data,FIELDS["form"])
    code=pick(data,FIELDS["code"])
    if not code:
        code=hashlib.sha256((name+"|"+ingredient+"|"+form+
                json.dumps(data,sort_keys=True,ensure_ascii=False)).encode()).hexdigest()[:26]
    details={}
    for key,val in list(data.items())[:35]:
        label="export_"+hashlib.sha1(str(key).encode()).hexdigest()[:12]
        if val and len(details)<20:
            details[label]=str(key)+": "+str(val)[:1500]
    return dict(regulator=regulator,source_id=code,name=name,ingredients=ingredient,
      form=form,status=pick(data,FIELDS["status"]) or "Kaynakta ruhsat statüsü belirtilmemiş",
      market=pick(data,FIELDS["market"]) or AGENCIES[regulator][0],
      updated=pick(data,FIELDS["updated"]),url=pick(data,FIELDS["url"]),
      kind="Official export: original fields (no clinical validation)",sections=details)


def do_import(conn,path,regulator):
    if regulator not in AGENCIES:
        raise ValueError("Desteklenmeyen kurum")
    if not path.is_file() or path.stat().st_size>300_000_000:
        raise ValueError("Dosya bulunamadı veya çok büyük (300MB üstü)")
    rows=read_xlsx(path) if path.suffix.lower()==".xlsx" else read_csv(path)
    count=0
    skipped=0
    for i,data in enumerate(rows):
        if i>=300000:
            raise ValueError("300 bin kayıt sınırı; kısmi kayıtlar korunur")
        row=generic_row(data,regulator)
        if not row:
            skipped+=1
            continue
        if write_record(conn,imported_at=now(),**row):
            count+=1
        if count and count%5000==0:
            conn.commit()
    conn.commit()
    print("İçe alınamayan ürün adı satırları:",skipped)
    return count,"Resmî dosyadan aktarıldı; sütun doğrulaması gerekli"


def do_fda_json(conn,path):
    if path.is_dir():
        files=sorted(path.glob("*.zip"))+sorted(path.glob("*.json"))
    elif path.is_file():
        files=[path]
    else:
        raise ValueError("FDA arşiv yolu bulunamadı")
    if not files:
        raise ValueError("FDA JSON/ZIP dosyası yok")
    count=0
    for file in files:
        print("FDA arşiv:",file.name)
        if file.suffix.lower()==".zip":
            with zipfile.ZipFile(file) as z:
                entries=[x for x in z.infolist() if x.filename.endswith(".json")]
                if not entries or any(x.file_size>250_000_000 for x in entries):
                    raise ValueError("FDA ZIP büyük veya JSON içermiyor")
                for entry in entries:
                    with z.open(entry) as raw:
                        records=json.load(raw).get("results",[])
                    for item in records:
                        row=fda_label_to_row(item)
                        if row and write_record(conn,imported_at=now(),**row):
                            count+=1
        elif file.suffix.lower()==".json":
            if file.stat().st_size>250_000_000:
                raise ValueError("FDA JSON boyut sınırı")
            with file.open(encoding="utf-8") as raw:
                records=json.load(raw).get("results",[])
            for item in records:
                row=fda_label_to_row(item)
                if row and write_record(conn,imported_at=now(),**row):
                    count+=1
        conn.commit()
    return count,"FDA etiket arşivinden aktarıldı; FDA ruhsat kararı değildir"


def main(argv=None):
    p=argparse.ArgumentParser(description="KALE ilaç resmi kurum kaynakları (read-only ana katalog)")
    p.add_argument("source",choices=("fda","canada","import","fda-json"))
    p.add_argument("--regulator",choices=list(AGENCIES))
    p.add_argument("--file",type=Path)
    p.add_argument("--max-terms",type=int,default=250,
                   help="FDA eski ilaç DB adlarından sorgu sayısı; 0 tümü")
    p.add_argument("--pause",type=float,default=.4)
    args=p.parse_args(argv)
    if args.source=="import" and (not args.file or not args.regulator):
        p.error("import için --regulator ve --file zorunlu")
    if args.source=="fda-json" and not args.file:
        p.error("fda-json için --file zorunlu")
    print("Yalnız internet olan ilk veri hazırlığında indirir; çalışma zamanı tamamen offline.")
    print("Ana ilaç veritabanı değişmeyecek:",ROOT/"data/kale.db")
    with open_writer() as conn:
        if args.source=="fda":
            agency="FDA"
            count,status=do_fda(conn,args.max_terms,os.environ.get("OPENFDA_API_KEY",""),args.pause)
        elif args.source=="canada":
            agency="HEALTH_CANADA"
            count,status=do_canada(conn)
        elif args.source=="import":
            agency=args.regulator
            count,status=do_import(conn,args.file,agency)
        else:
            agency="FDA"
            count,status=do_fda_json(conn,args.file)
        conn.execute("""INSERT INTO sync_runs VALUES (?,?,?,?,?)
             ON CONFLICT(regulator) DO UPDATE SET source_name=excluded.source_name,
               synced_at=excluded.synced_at,records_seen=excluded.records_seen,result=excluded.result""",
           (agency,args.source,now(),count,status))
        conn.commit()
    print("KAYDEDİLDİ:",agency,count,"kaynak ürün kaydı. Dosya:",DB)
    print("Bu sayı 707 Türkçe kaydın doğrulandığı anlamına gelmez.")
    if status.startswith("KISMİ"):
        raise RuntimeError("Bazı FDA sorguları tamamlanmadı; aktarım kısmi. Resmî API kotasını ve interneti kontrol et.")


if __name__=="__main__":
    try:
        main()
    except (OSError,ValueError,RuntimeError,sqlite3.Error,zipfile.BadZipFile,
            urllib.error.URLError,urllib.error.HTTPError) as exc:
        print("RESMİ KAYNAK SENKRONİZASYONU TAMAMLANMADI:",exc,file=sys.stderr)
        sys.exit(1)
