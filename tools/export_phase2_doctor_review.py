#!/usr/bin/env python3
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'review/doktor_kontrol_listesi.csv'
target=ROOT/'review/doktor_kontrol_faz2.csv'
with source.open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f)
    fields=reader.fieldnames
    rows=[r for r in reader if r['phase']=='2']
assert len(rows)==70, f'Expected 70 phase 2 review rows, got {len(rows)}'
with target.open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields)
    writer.writeheader();writer.writerows(rows)
print('Phase 2 independent review rows:',len(rows),target)
