import ast
import json
import re
import sqlite3
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

class V13NatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((WEB/'assets/poisonous-plants.json').read_text('utf-8'))['plants']
        cls.m=json.loads((WEB/'assets/dangerous-mushrooms.json').read_text('utf-8'))['mushrooms']

    def test_44_entries_no_edible_approvals(self):
        self.assertEqual((len(self.p),len(self.m)),(28,16))
        for row in self.p+self.m:
            self.assertIs(row['consumable'],False)
            self.assertIs(row['expert_verified'],False)
            self.assertIn('doğrulanmadı',row['region'].lower())
            self.assertTrue(row['source_url'].startswith('https://'))
            self.assertTrue(row['latin'] and row['name'] and row['warning'])
            self.assertTrue(row['review_status'])

    def test_unique_names_and_taxonomic_names(self):
        for rows in (self.p,self.m):
            self.assertEqual(len({r['id'] for r in rows}),len(rows))
            self.assertEqual(len({r['latin'] for r in rows}),len(rows))
            self.assertTrue(all(' ' in r['latin'] for r in rows))

    def test_mushroom_source_matches_warning_and_calls(self):
        document=(WEB/'doga.html').read_text('utf-8')
        for text in ('112','114','mantar','bitki','Kusturmaya'):
            self.assertIn(text,document)
        self.assertIn('dangerous-mushrooms.json',(WEB/'assets/nature.js').read_text())
        self.assertIn('consumable!==false',(WEB/'assets/nature.js').read_text())

    def test_offline_precache_integrity(self):
        sw=(WEB/'sw.js').read_text('utf-8')
        m=re.search(r'const CORE=(\[.*?\]);',sw,re.S)
        self.assertIsNotNone(m)
        files=ast.literal_eval(m.group(1))
        for name in ('/assets/dangerous-mushrooms.json','/assets/nature.js','/assets/nature.css'):
            self.assertIn(name,files)
            self.assertTrue((WEB/name.lstrip('/')).is_file())
        for i in range(25,29):
            self.assertIn(f'/assets/diagrams/guide-{i:02d}.svg',files)

    def test_core_kale_no_changes(self):
        with sqlite3.connect(ROOT/'data/kale.db') as conn:
            self.assertEqual(conn.execute('select count(*) from medicines').fetchone()[0],707)
            self.assertEqual(conn.execute('select count(*) from entries').fetchone()[0],146)
            self.assertEqual(conn.execute('pragma integrity_check').fetchone()[0],'ok')

    def test_28_guides_still_all_drafts(self):
        guides=json.loads((WEB/'assets/field-guides.json').read_text('utf8'))['guides']
        self.assertEqual(len(guides),28)
        self.assertTrue(all(g['review_status']=='EDİTORYAL TASLAK' for g in guides))
        self.assertTrue(all((WEB/g['diagram'].lstrip('/')).is_file() for g in guides))

if __name__=='__main__':unittest.main()
