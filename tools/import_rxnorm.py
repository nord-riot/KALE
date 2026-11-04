#!/usr/bin/env python3
"""Import NLM RxNorm prescribable release to KALE as *names only*.

Download the license-free Current Prescribable Content release from:
https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html

This script does NOT import clinical indications, warnings or usage instructions.
RxNorm is US drug terminology, not a register of Turkish licensed products.
"""
import argparse
import csv
import hashlib
import sqlite3
import sys
import zipfile
from pathlib import Path
from medicines_core import DB, initialize, norm, put

ALLOWED={'IN', 'PIN', 'MIN', 'SCD', 'SBD', 'SCDG', 'SBDG', 'SCDGP', 'SBDGP', 'GPCK', 'BPCK'}

def iter_rrf(p):
    if p.suffix.lower()=='.zip':
        with zipfile.ZipFile(p) as archive:
            filenames=[n for n in archive.namelist() if n.upper().endswith('/RXNCONSO.RRF') or n.upper()=='RXNCONSO.RRF']
            if len(filenames)!=1:raise ValueError('ZIP içinde tek RXNCONSO.RRF bulunmalı')
            from io import TextIOWrapper
            with archive.open(filenames[0]) as raw:
                with TextIOWrapper(raw,encoding='utf-8',errors='replace',newline='') as f:
                    yield from csv.reader(f,delimiter='|')
    else:
        with p.open(encoding='utf-8',errors='replace',newline='') as f:
            yield from csv.reader(f,delimiter='|')

def import_rxnorm(conn, source, limit=0):
    initialize(conn)
    total=0;seen=set();bad=0
    for v in iter_rrf(source):
        if len(v)<17:bad+=1;continue
        rxcui,language,sab,tty,name=v[0],v[1],v[11],v[12],v[14].strip()
        if language!='ENG' or sab!='RXNORM' or tty not in ALLOWED or not rxcui.isdigit() or not name:continue
        if rxcui in seen:continue
        seen.add(rxcui)
        row={'id':'rx_'+rxcui,'name':name,'generic_name':name if tty in ('IN','PIN','MIN') else '',
             'category':'RxNorm / '+tty,'source':'NLM RxNorm / ABD ilaç adı dizini',
             'source_url':'https://rxnav.nlm.nih.gov/REST/rxcui/'+rxcui+'/allProperties.json?prop=names',
             'locale':'en','review_status':'SADECE İSİM DİZİNİ'}
        if put(conn,row):total+=1
        if limit and total>=limit:break
    return total,bad

def main():
    ap=argparse.ArgumentParser(description='KALE RxNorm isim dizini içe aktarıcı')
    ap.add_argument('source',type=Path,help='RxNorm release ZIP veya RXNCONSO.RRF')
    ap.add_argument('--db',type=Path,default=DB)
    ap.add_argument('--max',type=int,default=0,help='Test için limit (0: tümü)')
    args=ap.parse_args()
    if args.max<0:ap.error('--max negatif olamaz')
    if not args.db.exists():ap.error('Önce tools/build_db.py ile veritabanını oluşturun')
    with sqlite3.connect(args.db) as conn:
        with conn:
            added,bad=import_rxnorm(conn,args.source,args.max)
    print(f'RxNorm: {added} isim eklendi/güncellendi; {bad} hatalı satır, DB={args.db.stat().st_size} bayt')

if __name__=='__main__':main()
