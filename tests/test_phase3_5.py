import csv
import json
import sqlite3
import unittest
from medicines_path_fix import ROOT

class Phase3To5Tests(unittest.TestCase):
    def test_phase_coverage_and_safety_flags(self):
        with (ROOT/'review/ilac_10_faz_plani.csv').open(encoding='utf-8-sig') as f:
            plan=list(csv.DictReader(f))
        self.assertEqual(len(plan),707)
        for p,count in ((3,71),(4,71),(5,70)):
            phase=json.loads((ROOT/'data'/f'medicine_phase{p}_tr.json').read_text('utf8'))
            self.assertEqual(len(phase),count)
            self.assertEqual({r['name'] for r in phase}, {r['ilac_adi'] for r in plan if int(r['faz'])==p})
            for rec in phase:
                for field in ('indications','effects','side_effects','allergies','contraindications','interactions','warnings','pregnancy','storage','inactive_ingredients'):
                    self.assertGreater(len(rec[field]),25,(p,rec['name'],field))
                self.assertEqual(rec['phase'],p)
                self.assertFalse(rec['medical_review_approved'])
                self.assertFalse(rec['source_updated'])
                self.assertIn('TASLAK',rec['review_status'])
                self.assertIn('doğrulama yapılmadı',rec['source'])
                self.assertTrue(rec['source_url'].startswith('https://'))
                self.assertEqual(rec['locale'],'tr')
            with (ROOT/'review'/f'doktor_kontrol_faz{p}.csv').open(encoding='utf-8-sig') as f:
                review=list(csv.DictReader(f))
            self.assertEqual(len(review),count)
            self.assertFalse(any(x['clinical_decision_APPROVE_REVISE_REJECT'] for x in review))
            self.assertEqual({x['name'] for x in review},{x['name'] for x in phase})

    def test_database_counts_and_uniqueness(self):
        with sqlite3.connect(ROOT/'data/kale.db') as db:
            count=db.execute('SELECT count(*) FROM medicines').fetchone()[0]
            explained=db.execute("SELECT count(*) FROM medicines WHERE review_status LIKE '%TASLAK%' OR review_status LIKE '%ÖZET%'").fetchone()[0]
            names=db.execute("SELECT count(*) FROM medicines WHERE review_status='SADECE İSİM DİZİNİ'").fetchone()[0]
            unique=db.execute('SELECT count(distinct name) FROM medicines').fetchone()[0]
            approved=db.execute("SELECT count(*) FROM medicines WHERE review_status LIKE '%ONAYLANDI%'").fetchone()[0]
            self.assertEqual((count,explained,names,unique,approved),(707,707,0,707,0))
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            for key in ('Clozapin','Dabigatran','Fentanil','İnsülin glarjin','İzotretinoin','Klopidogrel bisülfat','Gepant'):
                record=db.execute('SELECT indications,side_effects,contraindications,warnings,review_status FROM medicines WHERE name=?',(key,)).fetchone()
                self.assertTrue(record,key)
                self.assertTrue(all(record[:4]),key)
                self.assertRegex(record[4],r'FAZ [345]')
        with (ROOT/'review/doktor_kontrol_listesi.csv').open(encoding='utf-8-sig') as f:
            review=list(csv.DictReader(f))
        self.assertEqual(len(review),707)
        self.assertEqual(len({r['name'] for r in review}),707)
        self.assertFalse(any(r['clinical_decision_APPROVE_REVISE_REJECT'] for r in review))

    def test_revised_specific_safety_labels(self):
        with sqlite3.connect(ROOT/'data/kale.db') as db:
            for name,contains in [('Dabigatran','kanama'),('Clozapin','kan sayımı'),('Fentanil','solunum'),('İnsülin aspart','hızlı'),('İnsülin glarjin','bazal'),('Gepant','SINIF ADI'),('Fluokinonid','AD DOĞRULAMA'),('Klopidogrel bisülfat','çift doz')]:
                r=db.execute('SELECT indications||" "||side_effects||" "||warnings FROM medicines WHERE name=?',(name,)).fetchone()
                self.assertIn(contains.casefold(),r[0].casefold(),name)

if __name__=='__main__':unittest.main()
