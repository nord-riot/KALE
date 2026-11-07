"""KALE v1.4: shelter/water content integrity and regression tests."""
import ast
import json
import re
import sqlite3
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

class ShelterWaterV14(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((WEB/'assets/shelter-water.json').read_text('utf8'))
        cls.cards=cls.data['cards']

    def test_18_cards_nine_each(self):
        self.assertEqual(len(self.cards),18)
        self.assertEqual([sum(x['category']==c for x in self.cards) for c in ('barinak','su')],[9,9])
        self.assertEqual(len({x['id'] for x in self.cards}),18)
        self.assertEqual(len({x['slug'] for x in self.cards}),18)

    def test_guides_describe_safety_and_sources(self):
        for x in self.cards:
            with self.subTest(id=x['id']):
                self.assertGreaterEqual(len(x['steps']),4)
                self.assertTrue(x['materials'])
                self.assertTrue(x['stop'])
                self.assertTrue(x['warning'])
                self.assertIn('ONAYI BEKLİYOR',x['review_status'])
                self.assertTrue(x['sources'])
                self.assertTrue(all(u['url'].startswith('https://') for u in x['sources']))

    def test_all_original_svg_diagrams_wellformed(self):
        for x in self.cards:
            path=WEB/x['diagram'].lstrip('/')
            self.assertTrue(path.is_file(),path)
            root=ET.parse(path).getroot()
            self.assertEqual(root.tag,'{http://www.w3.org/2000/svg}svg')
            self.assertTrue(root.attrib.get('aria-label'))
            self.assertIn('Uzman onayı',path.read_text('utf8'))

    def test_water_and_carbon_monoxide_critical_warnings(self):
        water=' '.join(x['warning']+' '+x['summary']+' '+' '.join(x['stop']) for x in self.cards if x['category']=='su').lower()
        shelter=' '.join(x['warning']+' '+' '.join(x['stop']) for x in self.cards if x['category']=='barinak').lower()
        for phrase in ('kimyasal','kaynat','güvenli'):
            self.assertIn(phrase,water)
        for phrase in ('karbonmonoksit','yıldırım','sel'):
            self.assertIn(phrase,shelter)

    def test_site_and_water_screen_branch_warnings(self):
        script=(WEB/'assets/shelter-water.js').read_text('utf8')
        for token in ("chemical==='yes'", "chemical==='unknown'", "src==='unknown'", "boil!=='yes'", "value==='yes'", "value==='unknown'", 'BU EKRAN SUYU İÇİLEBİLİR OLARAK ONAYLAMAZ'):
            self.assertIn(token,script)
        self.assertNotIn('localStorage',script)
        self.assertNotIn('XMLHttpRequest',script)

    def test_offline_files_and_entry_points(self):
        sw=(WEB/'sw.js').read_text('utf8')
        m=re.search(r'const CORE=(\[.*?\]);',sw,re.S)
        self.assertIsNotNone(m)
        files=ast.literal_eval(m.group(1))
        self.assertEqual(len(files),len(set(files)))
        for url in ('/barinak-su.html','/assets/shelter-water.css','/assets/shelter-water.js','/assets/shelter-water.json'):
            self.assertIn(url,files)
            self.assertTrue((WEB/url.lstrip('/')).is_file())
        for n in range(1,19):self.assertIn(f'/assets/diagrams/bs-{n:02d}.svg',files)
        self.assertIn('/barinak-su.html',(WEB/'index.html').read_text('utf8'))
        self.assertIn('barinak-su.html',(ROOT/'server.py').read_text('utf8'))
        self.assertIn('kale-v2.4.0',sw)

    def test_existing_core_data_untouched(self):
        with sqlite3.connect(ROOT/'data/kale.db') as db:
            self.assertEqual(db.execute('select count(*) from entries').fetchone()[0],146)
            self.assertEqual(db.execute('select count(*) from medicines').fetchone()[0],707)
            self.assertEqual(db.execute('pragma integrity_check').fetchone()[0],'ok')
        plants=json.loads((WEB/'assets/poisonous-plants.json').read_text('utf8'))['plants']
        mushrooms=json.loads((WEB/'assets/dangerous-mushrooms.json').read_text('utf8'))['mushrooms']
        self.assertEqual((len(plants),len(mushrooms)),(28,16))

if __name__=='__main__':unittest.main()
