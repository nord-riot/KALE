import csv
import json
import sqlite3
import unittest
from medicines_path_fix import ROOT

class Phase2Test(unittest.TestCase):
    def test_all_70_drafts_match_plan_and_are_unapproved(self):
        phase2=json.loads((ROOT/'data/medicine_phase2_tr.json').read_text('utf8'))
        with (ROOT/'review/ilac_10_faz_plani.csv').open(encoding='utf-8-sig') as f:
            planned={r['ilac_adi'] for r in csv.DictReader(f) if r['faz']=='2'}
        self.assertEqual(len(phase2),70)
        self.assertEqual({row['name'] for row in phase2},planned)
        required=('indications','effects','side_effects','allergies','contraindications','interactions','warnings','pregnancy','storage','inactive_ingredients')
        for row in phase2:
            for col in required:
                self.assertGreater(len(row[col]),32,(row['name'],col))
            self.assertFalse(row['medical_review_approved'])
            self.assertEqual(row['phase'],2)
            self.assertEqual(row['source_updated'],'')
            self.assertIn('doğrulaması yapılmadı',row['source'])
        with sqlite3.connect(ROOT/'data/kale.db') as db:
            for row in phase2:
                current=db.execute('SELECT indications,review_status FROM medicines WHERE name=?',(row['name'],)).fetchone()
                self.assertEqual(current[0],row['indications'])
                self.assertTrue(current[1].startswith('FAZ 2'))

    def test_total_no_duplicates_and_review_files(self):
        with sqlite3.connect(ROOT/'data/kale.db') as db:
            total=db.execute('SELECT COUNT(*) FROM medicines').fetchone()[0]
            unique=db.execute('SELECT COUNT(DISTINCT name) FROM medicines').fetchone()[0]
            explained=db.execute("SELECT COUNT(*) FROM medicines WHERE review_status LIKE '%TASLAK%' OR review_status LIKE '%ÖZET%'").fetchone()[0]
            name_only=db.execute("SELECT COUNT(*) FROM medicines WHERE review_status='SADECE İSİM DİZİNİ'").fetchone()[0]
            reviewed=db.execute("SELECT COUNT(*) FROM medicines WHERE review_status LIKE '%ONAYLANDI%'").fetchone()[0]
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        self.assertEqual((total,unique,explained,name_only,reviewed),(707,707,707,0,0))
        with (ROOT/'review/doktor_kontrol_listesi.csv').open(encoding='utf-8-sig') as f:
            all_rows=list(csv.DictReader(f))
        with (ROOT/'review/doktor_kontrol_faz2.csv').open(encoding='utf-8-sig') as f:
            phase2_rows=list(csv.DictReader(f))
        self.assertEqual(len(all_rows),707)
        self.assertEqual(len({r['name'] for r in all_rows}),707)
        self.assertEqual(len(phase2_rows),70)
        self.assertEqual(len({r['name'] for r in phase2_rows}),70)
        self.assertTrue(all(not r['clinical_decision_APPROVE_REVISE_REJECT'] for r in all_rows))

    def test_phase2_caution_flags(self):
        with sqlite3.connect(ROOT/'data/kale.db') as db:
            sample={name:db.execute('SELECT warnings,contraindications FROM medicines WHERE name=?',(name,)).fetchone() for name in ('Alteplaz','Amikasin','Aspirin (asetilsalisilik asit)','Biktegravir','Amoksisilin/klavulanat')}
        self.assertIn('HASTANE',sample['Alteplaz'][0])
        self.assertIn('HASTANE',sample['Amikasin'][0])
        self.assertIn('çift',sample['Aspirin (asetilsalisilik asit)'][0].lower())
        self.assertIn('kombinasyon',sample['Biktegravir'][0].lower())
        self.assertIn('ALİAS',sample['Amoksisilin/klavulanat'][0])

if __name__=='__main__': unittest.main()
