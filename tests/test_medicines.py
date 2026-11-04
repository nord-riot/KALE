import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from medicines_path_fix import ROOT

class MedicinesTest(unittest.TestCase):
    def test_seed_data(self):
        with sqlite3.connect(ROOT/'data/kale.db') as conn:
            self.assertGreaterEqual(conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0],700)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM medicines WHERE review_status='SADECE İSİM DİZİNİ'").fetchone()[0],0)
            row=conn.execute("SELECT indications, contraindications, allergies FROM medicines WHERE name='İbuprofen'").fetchone()
            self.assertTrue('inflamasyon' in row[0].lower() or 'iltihap' in row[0].lower())
            self.assertIn('kanama', row[1].lower())
            self.assertIn('alerji', row[2].lower())


    def test_editorial_drafts_are_unapproved_and_complete(self):
        import json
        drafts=json.loads((ROOT/'data/medicine_drafts_tr.json').read_text(encoding='utf8'))
        self.assertEqual(len(drafts),88)
        required=('name','indications','effects','side_effects','allergies','contraindications','interactions','warnings','source_url')
        for row in drafts:
            for key in required:
                self.assertTrue(row.get(key),f'{row.get("name")} missing {key}')
        with sqlite3.connect(ROOT/'data/kale.db') as conn:
            n=conn.execute("SELECT COUNT(*) FROM medicines WHERE review_status LIKE '%TASLAK%'").fetchone()[0]
            self.assertEqual(n,699) # 707 total minus 8 legacy summaries
            self.assertEqual(conn.execute("SELECT count(*) FROM medicines WHERE review_status LIKE '%ONAYLANDI%'").fetchone()[0],0)

    def test_import_json_zip_and_preserve_ambiguity(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);db=base/'test.db';shutil.copy2(ROOT/'data/kale.db',db)
            record={
                'set_id':'9de0a100-1111-4444-9999-222222222222','id':'unique_record_1',
                'effective_time':'20260812',
                'openfda':{'generic_name':['TEST MEDICINE'],'brand_name':['TEST BRAND'],
                           'substance_name':['TEST SUBSTANCE']},
                'indications_and_usage':['Indication from original label'],
                'adverse_reactions':['Source side effect text'],
                'contraindications':['Source contraindications'],
                'inactive_ingredient':['Tablet binder'],
                'drug_interactions':['Source interaction warning']
            }
            payload={'results':[record]}; raw=json.dumps(payload).encode()
            zp=base/'medicines.json.zip'
            with zipfile.ZipFile(zp,'w') as z:z.writestr('drug-label.json',raw)
            script=ROOT/'tools/import_openfda.py'
            completed=subprocess.run([sys.executable,str(script),str(zp),'--db',str(db)],capture_output=True,text=True)
            self.assertEqual(completed.returncode,0,completed.stderr)
            with sqlite3.connect(db) as conn:
                rec=conn.execute("SELECT name,indications,side_effects,allergies,contraindications,inactive_ingredients,source_url,locale,source_updated FROM medicines WHERE name='TEST BRAND'").fetchone()
            self.assertIsNotNone(rec)
            self.assertEqual(rec[1],'Indication from original label')
            self.assertEqual(rec[2],'Source side effect text')
            self.assertEqual(rec[3],'')   # Never hallucinate a drug allergen
            self.assertEqual(rec[4],'Source contraindications')
            self.assertEqual(rec[5],'Tablet binder')
            self.assertIn('dailymed.nlm.nih.gov',rec[6])
            self.assertEqual(rec[7],'en')
            self.assertEqual(rec[8],'2026-08-12')

if __name__=='__main__':unittest.main()
