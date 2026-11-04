#!/usr/bin/env python3
"""Export three independent clinical review queues from latest drafts, no automatic approval."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'review/doktor_kontrol_listesi.csv'
with src.open(encoding='utf-8-sig',newline='') as f:
    rdr=csv.DictReader(f);fields=rdr.fieldnames;all_rows=list(rdr)
for p,expected in ((3,71),(4,71),(5,70)):
    rows=[r for r in all_rows if r['phase']==str(p)]
    assert len(rows)==expected, (p,len(rows))
    assert not any(r['clinical_decision_APPROVE_REVISE_REJECT'] for r in rows)
    dest=ROOT/'review'/f'doktor_kontrol_faz{p}.csv'
    with dest.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    print(f'Phase {p}: {len(rows)} entries -> {dest}')
