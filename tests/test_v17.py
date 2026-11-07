"""KALE v1.7 first-aid read-only offline catalogue regression tests."""
import json,re,ast,sqlite3,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'
class FirstAidV17Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((WEB/'assets/first-aid.json').read_text('utf-8'))
 def test_catalog_safety_contract(self):
  d=self.data
  self.assertEqual(d['format'],'KALE-FIRSTAID-1')
  self.assertEqual(d['emergency_phones'],{'emergency':'112','poison':'114'})
  self.assertEqual(len(d['cards']),24)
  ids=set()
  for x in d['cards']:
   self.assertNotIn(x['id'],ids);ids.add(x['id'])
   self.assertEqual(x['reviewed_by'],None)
   self.assertIn('UZMAN ONAYI YOK',x['review_status'])
   self.assertIn('112',x['call112']) if x['urgency'] not in ('SAĞLIK DEĞERLENDİRMESİ',) else self.assertIn('acil',x['call112'].lower())
   for key in ('title','summary','category','diagram','urgency'):self.assertTrue(x[key])
   self.assertGreaterEqual(len(x['steps']),3)
   self.assertGreaterEqual(len(x['avoid']),2)
   self.assertGreaterEqual(len(x['sources']),1)
   self.assertTrue((WEB/x['diagram'].lstrip('/')).is_file())
   for src in x['sources']:
    self.assertTrue(src['url'].startswith('https://'))
    self.assertTrue(src['title'])
  self.assertEqual(len(ids),24)
 def test_turkey_phonelines_and_critical_words(self):
  html=(WEB/'ilk-yardim.html').read_text('utf-8')
  self.assertIn('href="tel:112"',html)
  self.assertIn('href="tel:114"',html)
  self.assertIn('klinik uzman',html.lower())
  js=(WEB/'assets/first-aid.js').read_text('utf-8')
  self.assertIn('tel:112',js)
  self.assertNotIn('localStorage',js)
  self.assertNotIn('innerHTML',js)
  self.assertNotIn('eval(',js)
  self.assertIn("fetch('/assets/first-aid.json')",js)
  self.assertNotIn('XMLHttpRequest',js)
 def test_pwa_bundles_all_24_local_diagrams(self):
  sw=(WEB/'sw.js').read_text('utf-8')
  self.assertEqual(sw,(WEB/'service-worker.js').read_text('utf-8'))
  self.assertIn('kale-v2.4.0',sw)
  m=re.search(r'const CORE=(\[.*?\]);',sw,re.S)
  self.assertIsNotNone(m)
  files=ast.literal_eval(m.group(1))
  self.assertEqual(len(files),len(set(files)))
  for key in ('/ilk-yardim.html','/assets/first-aid.css','/assets/first-aid.js','/assets/first-aid.json'):
   self.assertIn(key,files)
  for i in range(1,25):self.assertIn(f'/assets/diagrams/aid-{i:02d}.svg',files)
  self.assertTrue(all((WEB/x.lstrip('/')).exists() for x in files if x not in ('/','/api/catalog')))
 def test_preserve_existing_catalog(self):
  with sqlite3.connect(ROOT/'data/kale.db') as db:
   self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
   self.assertEqual(db.execute('select count(*) from medicines').fetchone()[0],707)
   self.assertEqual(db.execute('select count(*) from entries').fetchone()[0],146)
 def test_supported_urgencies_and_explicit_112(self):
  allowed={'112 HEMEN','112 GEREKEBİLİR','112 / 114','SAĞLIK DEĞERLENDİRMESİ'}
  cards=self.data['cards']
  self.assertTrue(all(x['urgency'] in allowed for x in cards))
  for num in range(1,9):self.assertEqual(cards[num-1]['urgency'],'112 HEMEN')
  self.assertTrue(any(x['category']=='Zehirlenme' for x in cards))
  self.assertTrue(any('Bebek' in x['avoid'][0] or 'bebek' in ' '.join(x['avoid']).lower() for x in cards))
 def test_doctor_review_is_untouched(self):
  self.assertTrue((ROOT/'review/KALE_707_Ilac_Doktor_Inceleme_Formatli.xlsx').is_file())
  self.assertIn("VERSION = '2.4.0'",(ROOT/'server.py').read_text('utf-8'))
  self.assertIn('def do_POST(', (ROOT/'server.py').read_text('utf-8'))
 def test_offline_diagnostic_reads_catalog(self):
  s=(WEB/'assets/offline.js').read_text('utf-8')
  self.assertIn('kale-v2.4.0',s)
  self.assertIn("n===24;extra=n+' ilk yardım kartı'",s)
 def test_original_diagrams_are_noninteractive(self):
  for i in range(1,25):
   src=(WEB/'assets/diagrams'/f'aid-{i:02d}.svg').read_text('utf-8')
   self.assertIn('<svg',src)
   self.assertNotIn('<script',src)
   self.assertNotIn('foreignObject',src)
   self.assertNotIn('href="http://',src)
if __name__=='__main__':unittest.main()
