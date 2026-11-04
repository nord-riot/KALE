import http.client
import json
import subprocess
import sys
import time
import unittest
from pathlib import Path
from socket import socket
ROOT = Path(__file__).resolve().parents[1]

class AppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sock=socket();cls.sock.bind(('127.0.0.1',0));cls.port=cls.sock.getsockname()[1];cls.sock.close()
        import os
        env=dict(os.environ,KALE_HOST='127.0.0.1',KALE_PORT=str(cls.port))
        cls.proc=subprocess.Popen([sys.executable,'server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        for _ in range(60):
            try:
                c=http.client.HTTPConnection('127.0.0.1',cls.port,timeout=1)
                c.request('GET','/api/health');r=c.getresponse();r.read();c.close()
                if r.status==200:break
            except OSError:time.sleep(.1)
        else:raise RuntimeError('Server did not start')

    @classmethod
    def tearDownClass(cls):cls.proc.terminate();cls.proc.wait(timeout=5)

    def get(self,path):
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=3)
        c.request('GET',path);r=c.getresponse();body=r.read();headers=dict(r.getheaders());code=r.status;c.close()
        return code,headers,body

    def test_health(self):
        status,headers,body=self.get('/api/health')
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['app'],'KALE')
        self.assertIn('X-Content-Type-Options',headers)

    def test_catalog(self):
        status,headers,body=self.get('/api/catalog')
        self.assertEqual(status,200)
        d=json.loads(body)
        self.assertGreaterEqual(len(d['entries']),140)
        self.assertGreaterEqual(len({e['category'] for e in d['entries']}),15)
        self.assertTrue(all('regions' in e for e in d['entries']))
        self.assertEqual(len({e['id'] for e in d['entries']}),len(d['entries']))
        self.assertTrue(all(e['review_status'] for e in d['entries']))

    def test_static(self):
        for path in ['/','/assets/style.css','/assets/app.js','/favicon.svg','/sw.js','/manifest.webmanifest','/assets/kale-emblem.webp']:
            with self.subTest(path=path):self.assertEqual(self.get(path)[0],200)

    def test_stats(self):
        status,headers,body=self.get('/api/stats')
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['entries'],146)

    def test_search(self):
        status,headers,body=self.get('/api/search?q=karbonmonoksit')
        self.assertEqual(status,200)
        r=json.loads(body)
        self.assertGreaterEqual(r['total'],1)
        self.assertTrue(any('karbonmonoksit' in e['body'].lower() or 'karbonmonoksit' in e['title'].lower() for e in r['entries']))

    def test_detail(self):
        status,headers,body=self.get('/api/entry/38')
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['id'],38)

    def test_sqlite_search_and_pagination(self):
        from urllib.parse import quote
        code,_,body=self.get('/api/search?q='+quote('deprem')+'&limit=2&offset=0')
        self.assertEqual(code,200)
        data=json.loads(body)
        self.assertGreater(data['total'],2)
        self.assertEqual(len(data['entries']),2)
        self.assertTrue(all('deprem' in (e['title']+e['body']+e['tags']).lower() for e in data['entries']))

    def test_search_turkish_diacritic(self):
        from urllib.parse import quote
        code,_,body=self.get('/api/search?q='+quote('soguk')+'&limit=50')
        self.assertEqual(code,200)
        self.assertGreater(json.loads(body)['total'],0)

    def test_sql_injection_is_text_not_sql(self):
        from urllib.parse import quote
        for q in ("' OR 1=1 --", '%_', 'notexistingvalue123456'):
            code,_,body=self.get('/api/search?q='+quote(q)+'&limit=5')
            self.assertEqual(code,200)
            self.assertEqual(json.loads(body)['total'],0)

    def test_categories_and_entry(self):
        code,_,body=self.get('/api/categories')
        self.assertEqual(code,200)
        self.assertEqual(len(json.loads(body)['categories']),15)
        code,_,body=self.get('/api/entry/1')
        self.assertEqual(code,200)
        self.assertEqual(json.loads(body)['title'],'İlk 5 dakika')
        self.assertEqual(self.get('/api/entry/999999')[0],404)
        self.assertEqual(self.get('/api/search?limit=bad')[0],400)

    def test_medicines_api(self):
        from urllib.parse import quote
        code,_,body=self.get('/api/medicines/stats')
        self.assertEqual(code,200)
        self.assertEqual(json.loads(body)['name_only_records'],0)
        self.assertEqual(json.loads(body)['turkish_summaries'],707)
        code,_,body=self.get('/api/medicines?q='+quote('ibuprofen'))
        self.assertEqual(code,200)
        # Turkish seed name is İbuprofen, should be accent/case tolerant.
        self.assertGreaterEqual(json.loads(body)['total'],1)
        key=next(row['id'] for row in json.loads(body)['items'] if row['name']=='İbuprofen')
        code,_,body=self.get('/api/medicines/'+key)
        self.assertEqual(code,200)
        drug=json.loads(body)
        self.assertIn('contraindications',drug)
        self.assertIn('side_effects',drug)
        self.assertTrue(drug['review_status'].startswith('FAZ 5'))
        self.assertIn('böbrek',drug['contraindications'].lower())
        self.assertEqual(self.get('/api/medicines/notexists')[0],404)
        self.assertEqual(self.get('/api/medicines?q=%25%5f')[0],200)
        self.assertEqual(self.get('/api/medicines?limit=nope')[0],400)

    def test_medicines_static(self):
        for p in ('/ilaclar.html','/assets/medicines.js','/assets/medicines.css'):
            with self.subTest(path=p):self.assertEqual(self.get(p)[0],200)
        _,_,page=self.get('/ilaclar.html')
        self.assertIn('İlaç ansiklopedisi'.encode(),page)

    def test_offline_pwa_assets(self):
        for path in ('/assets/tools.js','/assets/icon.svg','/service-worker.js'):
            with self.subTest(path=path): self.assertEqual(self.get(path)[0],200)
        _,_,body=self.get('/sw.js')
        self.assertIn(b'/api/catalog',body)
        self.assertIn(b'/assets/tools.js',body)


    def test_v09_review_api_is_read_only_and_private(self):
        code,_,body=self.get('/api/reviews/stats')
        self.assertEqual(code,200)
        self.assertEqual(json.loads(body)['reviewed'],0)
        code,_,body=self.get('/api/medicines?limit=1')
        self.assertEqual(code,200)
        key=json.loads(body)['items'][0]['id']
        code,_,body=self.get('/api/medicines/'+key)
        self.assertEqual(code,200)
        review=json.loads(body)['doctor_review']
        self.assertFalse(review['verified_clinical_safety'])
        self.assertNotIn('reviewer',review)
        self.assertEqual(self.get('/doktor.html')[0],200)
        self.assertEqual(self.get('/assets/medicines-offline.json')[0],200)
        self.assertEqual(self.get('/data/doctor_reviews.sqlite3')[0],404)
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=3)
        c.request('POST','/api/reviews/stats',body='{}',headers={'Content-Type':'application/json'})
        response=c.getresponse();response.read()
        self.assertNotEqual(response.status,200)
        c.close()

    def test_deny_internal(self):
        for path in ['/server.py','/data/content.json','/api/nope','/../../server.py']:
            with self.subTest(path=path):self.assertEqual(self.get(path)[0],404)

if __name__ == '__main__':unittest.main()
