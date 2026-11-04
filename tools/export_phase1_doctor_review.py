#!/usr/bin/env python3
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'review/doktor_kontrol_listesi.csv'
target=ROOT/'review/doktor_kontrol_faz1.csv'
with source.open(encoding='utf-8-sig',newline='') as f:
    rdr=csv.DictReader(f)
    hdr=rdr.fieldnames
    rows=[r for r in rdr if r['phase']=='1']
assert len(rows)==71
with target.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=hdr)
    w.writeheader();w.writerows(rows)
print('FAZ1 review rows:',len(rows),target)
