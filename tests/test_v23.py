"""Data integrity and mobile guide structure: no pretend professional approvals."""
import json,sqlite3,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class DetailedManualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content=json.loads((ROOT/'data/content.json').read_text('utf8'))
    def test_every_guide_expanded_with_topic_specific_steps(self):
        entries=self.content['entries']
        self.assertEqual(len(entries),146)
        self.assertEqual({e['id'] for e in entries},set(range(1,147)))
        for e in entries:
            with self.subTest(e=e['id']):
                self.assertGreaterEqual(len(e['body']),650)
                for required in ('SAHA UYGULAMA PLANI','KRİTİK HATALAR VE SINIRLAR','TEMEL BİLGİ'):
                    self.assertIn(required,e['body'])
                self.assertNotIn('ONAYLANDI',e['review_status'].upper())
    def test_database_sync_and_medical_untouched(self):
        with sqlite3.connect(ROOT/'data/kale.db') as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM entries').fetchone()[0],146)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM medicines').fetchone()[0],707)
            rows=dict(db.execute('SELECT id,body FROM entries'))
            for e in self.content['entries']:
                self.assertEqual(rows[e['id']],e['body'])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM medicines WHERE review_status LIKE '%ONAYLANDI%'").fetchone()[0],0)
    def test_sources_and_js_safe_text_rendering(self):
        e={e['id']:e for e in self.content['entries']}
        for key in (8,15,38,43,60,61,91):self.assertTrue(e[key]['sources'])
        js=(ROOT/'web/assets/app.js').read_text()
        self.assertIn('renderGuideText',js)
        self.assertIn("container.replaceChildren()",js)
        self.assertIn("$('detailText'),e.body",js)
    def test_idempotent_editor_and_cache_version(self):
        from tools.expand_field_manual_v23 import FOCUS,CATEGORY
        self.assertEqual(len(FOCUS),146)
        self.assertGreaterEqual(len(CATEGORY),14)
        self.assertIn("kale-v2.4.0",(ROOT/'web/sw.js').read_text())
        self.assertIn("kale-v2.4.0",(ROOT/'web/service-worker.js').read_text())
