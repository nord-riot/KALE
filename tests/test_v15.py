"""v1.5 food, safe cooking, energy and winter module tests."""
import ast
import json
import re
import sqlite3
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

class FoodEnergyWinterV15(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.payload=json.loads((WEB/'assets/food-energy-winter.json').read_text('utf-8'))
  cls.cards=cls.payload['cards']

 def test_24_records_four_groups(self):
  self.assertEqual(len(self.cards),24)
  self.assertEqual(Counter(x['category'] for x in self.cards),{'gida':6,'pisirme':6,'enerji':6,'kis':6})
  self.assertEqual(len(set(x['slug'] for x in self.cards)),24)
  self.assertEqual(len(set(x['id'] for x in self.cards)),24)
  self.assertEqual([x['id'] for x in self.cards],list(range(1,25)))

 def test_guides_have_warning_sources_and_steps(self):
  for x in self.cards:
   with self.subTest(name=x['title']):
    self.assertGreaterEqual(len(x['steps']),4)
    self.assertTrue(x['materials'] and x['stop'] and x['warning'])
    self.assertIn('ONAYI BEKLİYOR',x['review_status'])
    self.assertTrue(all(u['url'].startswith('https://') for u in x['sources']))
    self.assertFalse(x.get('medical_review_approved',False))

 def test_svg_count_and_valid_structure(self):
  for x in self.cards:
   with self.subTest(name=x['id']):
    pic=WEB/x['diagram'].lstrip('/')
    self.assertTrue(pic.is_file(),pic)
    self.assertEqual(ET.parse(pic).getroot().tag,'{http://www.w3.org/2000/svg}svg')
    self.assertIn('Uzman onayı bekleniyor',pic.read_text('utf-8'))
    self.assertNotIn('<script',pic.read_text('utf-8'))

 def test_cold_food_safety_not_approved(self):
  food=' '.join(x['warning']+' '+' '.join(x['steps']) for x in self.cards if x['category']=='gida')
  cook=' '.join(x['warning']+' '+' '.join(x['steps']) for x in self.cards if x['category']=='pisirme')
  cold=' '.join(x['warning']+' '+' '.join(x['steps']) for x in self.cards if x['category']=='kis')
  for word in ('4 saat','48 saat','24 saat','şüphe'):self.assertIn(word,food)
  for word in ('karbonmonoksit','74°C','71°C'):self.assertIn(word,cook.lower() if word=='karbonmonoksit' else cook)
  for word in ('112','Hipotermi','donma'):self.assertIn(word,cold)

 def test_calculator_critical_branches(self):
  js=(WEB/'assets/food-energy.js').read_text('utf-8')
  for code in ('verified===\'warm\'','door!==\'yes\'','h>=limit','const available=cap*(eff/100)*(1-res/100)','flags.includes(\'confusion\')','flags.includes(\'frost\')'):
   self.assertIn(code,js)
  self.assertIn('tüketilebilir onayı verilemez',js)
  self.assertNotIn('localStorage',js)
  self.assertNotIn('XMLHttpRequest',js)

 def test_precache_and_public_page(self):
  sw=(WEB/'sw.js').read_text('utf-8')
  match=re.search(r'const CORE=(\[.*?\]);',sw,re.S)
  self.assertIsNotNone(match)
  paths=ast.literal_eval(match.group(1))
  self.assertEqual(len(paths),len(set(paths)))
  self.assertIn('kale-v1.8.0',sw)
  for name in ('/gida-enerji.html','/assets/food-energy.js','/assets/food-energy.css','/assets/food-energy-winter.json'):
   self.assertIn(name,paths)
   self.assertTrue((WEB/name.lstrip('/')).is_file())
  for i in range(1,25):self.assertIn(f'/assets/diagrams/ge-{i:02d}.svg',paths)
  self.assertIn('gida-enerji.html',(ROOT/'server.py').read_text('utf-8'))
  self.assertIn('gida-enerji.html',(WEB/'index.html').read_text('utf-8'))
  self.assertEqual((WEB/'service-worker.js').read_text('utf-8'),sw)

 def test_prior_data_preserved(self):
  with sqlite3.connect(ROOT/'data/kale.db') as db:
   self.assertEqual(db.execute('select count(*) from entries').fetchone()[0],146)
   self.assertEqual(db.execute('select count(*) from medicines').fetchone()[0],707)
   self.assertEqual(db.execute('pragma integrity_check').fetchone()[0],'ok')
  self.assertEqual(len(json.loads((WEB/'assets/shelter-water.json').read_text('utf-8'))['cards']),18)
  self.assertEqual(len(json.loads((WEB/'assets/field-guides.json').read_text('utf-8'))['guides']),28)
  self.assertEqual(len(json.loads((WEB/'assets/poisonous-plants.json').read_text('utf-8'))['plants']),28)
  self.assertEqual(len(json.loads((WEB/'assets/dangerous-mushrooms.json').read_text('utf-8'))['mushrooms']),16)

if __name__=='__main__':unittest.main()
