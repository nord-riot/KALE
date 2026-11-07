import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
from tools.review_import import get_cells_from_xlsx,validate_records,save_reviews,export_audit,content_hash

class ReviewImportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with sqlite3.connect(ROOT/'data/kale.db') as c:
            c.row_factory=sqlite3.Row
            cls.meds={r['id']:dict(r) for r in c.execute('SELECT * FROM medicines')}
        cls.path=ROOT/'review/KALE_707_Ilac_Doktor_Inceleme_Formatli.xlsx'

    def rows(self):return get_cells_from_xlsx(self.path)

    def reviewed_one(self,decision='DÜZELT'):
        rows=self.rows();row=rows[0]
        row['F']=decision;row['G']='Dr. Deneme Test';row['H']='2026-11-03'
        row['I']='Doktor tarafından resmî prospektüsle tekrar kontrol edilmeli.'
        return rows

    def test_template_exact_ids_and_unreviewed(self):
        rows=self.rows()
        self.assertEqual(len(rows),707)
        self.assertEqual(validate_records(rows,self.meds),[])
        self.assertEqual(set(r['Y'] for r in rows),set(self.meds))

    def test_valid_correction_saves_only_review(self):
        rows=self.reviewed_one()
        changes=validate_records(rows,self.meds)
        self.assertEqual(len(changes),1)
        self.assertEqual(changes[0]['decision'],'DÜZELT')
        with tempfile.TemporaryDirectory() as tmp:
            sidecar=Path(tmp)/'reviews.sqlite3'
            self.assertEqual(save_reviews(sidecar,changes,'review.xlsx'),1)
            self.assertEqual(save_reviews(sidecar,changes,'review.xlsx'),0)  # idempotent
            with sqlite3.connect(sidecar) as c:
                self.assertEqual(c.execute('SELECT COUNT(*) FROM doctor_reviews').fetchone()[0],1)
                self.assertEqual(c.execute('SELECT COUNT(*) FROM review_audit').fetchone()[0],1)
            csv=Path(tmp)/'audit.csv';export_audit(sidecar,csv)
            self.assertIn('Dr. Deneme Test',csv.read_text('utf-8-sig'))

    def test_approval_requires_document(self):
        rows=self.reviewed_one('ONAYLA')
        with self.assertRaisesRegex(ValueError,'KÜB/KT'):
            validate_records(rows,self.meds)
        rows[0]['X']='Türkiye ürün KÜB/KT belge kodu: Fiktif-12345'
        rows[0]['AA']='DOĞRULANDI'
        self.assertEqual(validate_records(rows,self.meds)[0]['decision'],'ONAYLA')

    def test_modified_clinical_text_rejected(self):
        rows=self.reviewed_one()
        rows[0]['K']='Taslak değiştirildi.'
        with self.assertRaisesRegex(ValueError,'klinik taslak'):
            validate_records(rows,self.meds)

    def test_wrong_id_and_missing_reviewer_rejected(self):
        rows=self.reviewed_one();rows[0]['Y']='random-id'
        with self.assertRaises(ValueError):validate_records(rows,self.meds)
        rows=self.reviewed_one();rows[0]['G']=''
        with self.assertRaisesRegex(ValueError,'hekim/eczacı'):
            validate_records(rows,self.meds)

    def test_catalog_still_has_drafts_and_no_fake_approval(self):
        with sqlite3.connect(ROOT/'data/kale.db') as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM medicines').fetchone()[0],707)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM medicines WHERE review_status LIKE '%ONAYLANDI%'").fetchone()[0],0)

    def test_offline_snapshot_complete_and_medical_warning(self):
        path=ROOT/'web/assets/medicines-offline.json'
        data=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(len(data['medicines']),707)
        self.assertTrue(all('review_status' in x and 'warnings' in x and 'contraindications' in x for x in data['medicines']))
        sw=(ROOT/'web/sw.js').read_text(encoding='utf-8')
        self.assertIn('medicines-offline.json',sw)
        self.assertIn('kale-v2.',sw)

if __name__=='__main__': unittest.main()
