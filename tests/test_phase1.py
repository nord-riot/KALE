import csv
import json
import sqlite3
import unittest
from pathlib import Path
from medicines_path_fix import ROOT

class Phase1Test(unittest.TestCase):
    def test_number_and_review_statuses(self):
        phase=json.loads((ROOT/'data/medicine_phase1_tr.json').read_text('utf8'))
        self.assertEqual(len(phase),71)
        self.assertEqual(len({x['name'] for x in phase}),71)
        necessary=('indications','effects','side_effects','allergies','contraindications','interactions','warnings','pregnancy','storage','inactive_ingredients','source_url')
        with sqlite3.connect(ROOT/'data/kale.db') as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM medicines').fetchone()[0],707)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM medicines WHERE review_status='SADECE İSİM DİZİNİ'").fetchone()[0],0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM medicines WHERE review_status LIKE '%TASLAK%' OR review_status LIKE '%ÖZET%'").fetchone()[0],707)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM medicines WHERE review_status LIKE '%ONAYLANDI%'").fetchone()[0],0)
            for row in phase:
                for fld in necessary: self.assertTrue(row.get(fld), (row['name'],fld))
                self.assertFalse(row['medical_review_approved'])
                actual=db.execute('SELECT indications,warnings,review_status FROM medicines WHERE name=?',(row['name'],)).fetchone()
                self.assertIsNotNone(actual,row['name'])
                self.assertEqual(actual[0],row['indications'])
                self.assertTrue('FAZ 1' in actual[2])
    def test_phase_plan(self):
        with (ROOT/'review/ilac_10_faz_plani.csv').open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),707)
        self.assertEqual(len({r['ilac_adi'] for r in rows}),707)
        self.assertEqual(set(int(r['faz']) for r in rows),set(range(1,11)))
        self.assertEqual(sum(r['faz']=='1' for r in rows),71)
        self.assertTrue(all(r['doktor_onayi']=='BEKLİYOR' for r in rows))
    def test_review_csv(self):
        with (ROOT/'review/doktor_kontrol_listesi.csv').open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),707)
        self.assertEqual(sum(r['phase']=='1' for r in rows),71)
        self.assertEqual(sum(bool(r['clinical_decision_APPROVE_REVISE_REJECT']) for r in rows),0)
