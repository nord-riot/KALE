import importlib.util
import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('kale_import_guides',ROOT/'tools'/'import_guides.py')
imp=importlib.util.module_from_spec(spec);spec.loader.exec_module(imp)

class V12EditorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prev=json.loads((ROOT/'data/content.json').read_text('utf8'))

    def payload(self):
        return {'format':'KALE-EDITOR-v1','entries':json.loads(json.dumps(self.prev['entries']))}

    def test_more_guides_and_local_diagrams(self):
        data=json.loads((ROOT/'web/assets/field-guides.json').read_text('utf8'))
        self.assertEqual(len(data['guides']),28)
        for g in data['guides']:
            self.assertGreaterEqual(len(g['steps']),4)
            self.assertIn('TASLAK',g['review_status'])
            self.assertTrue((ROOT/'web'/g['diagram'].lstrip('/')).is_file())
            for s in g['sources']:self.assertTrue(s['url'].startswith('https://'))
        self.assertIn('Kimyasal kirlilik şüphesinde su kararı',[g['title'] for g in data['guides']])

    def test_editor_is_local_export_workflow(self):
        html=(ROOT/'web/atolye.html').read_text('utf8')
        js=(ROOT/'web/assets/editor.js').read_text('utf8')
        self.assertIn('editor.js',html)
        self.assertIn('JSON DIŞA AKTAR',html)
        self.assertIn('localStorage',js)
        self.assertNotIn('fetch(',js.replace("fetch('/api/catalog')",''))
        self.assertNotIn('POST',js)
        self.assertTrue((ROOT/'tools/import_guides.py').exists())

    def test_schema_and_no_fake_approval(self):
        p=self.payload()
        entries,changes,added=imp.validate(p,self.prev)
        self.assertEqual(changes,0);self.assertEqual(added,0)
        p['entries'][0]['title']='GÜNCELLEME TESTİ'
        p['entries'][0]['review_status']='UZMAN ONAYI VERİLDİ'
        entries,changes,added=imp.validate(p,self.prev)
        self.assertEqual(changes,1)
        self.assertIn('onayı bekliyor',entries[0]['review_status'])
        self.assertIsNone(entries[0]['last_reviewed'])

    def test_refuse_deletion_duplicate_or_bad_source(self):
        for case in ['deleted','duplicate','badurl','badbody']:
            p=self.payload()
            if case=='deleted':p['entries'].pop()
            elif case=='duplicate':p['entries'].append(dict(p['entries'][0]))
            elif case=='badurl':p['entries'][0]['sources']=['http://127.0.0.1/']
            elif case=='badbody':p['entries'][0]['body']=''
            with self.subTest(case=case):
                with self.assertRaises(ValueError):imp.validate(p,self.prev)

    def test_publishing_preserves_medicines_and_backups(self):
        p=self.payload();p['entries'][0]['title']='Deneme / içerik düzenle';rows,changes,new=imp.validate(p,self.prev)
        output=dict(self.prev);output['entries']=rows;output['version']='1.2.0'
        with tempfile.TemporaryDirectory() as d:
            temp=Path(d)
            (temp/'data').mkdir()
            shutil.copy(ROOT/'data/kale.db',temp/'data/kale.db')
            shutil.copy(ROOT/'data/content.json',temp/'data/content.json')
            with patch.object(imp,'ROOT',temp),patch.object(imp,'DB',temp/'data/kale.db'),patch.object(imp,'CATALOG',temp/'data/content.json'):
                back_json,back_db=imp.apply(output)
            self.assertTrue(back_json.is_file());self.assertTrue(back_db.is_file())
            with sqlite3.connect(temp/'data/kale.db') as c:
                self.assertEqual(c.execute('SELECT count(*) FROM medicines').fetchone()[0],707)
                self.assertEqual(c.execute('SELECT title FROM entries WHERE id=1').fetchone()[0],'Deneme / içerik düzenle')
                self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(json.loads((temp/'data/content.json').read_text())['entries'][0]['title'],'Deneme / içerik düzenle')

    def test_server_page_exposed_but_no_write_api(self):
        import sys
        sys.path.insert(0,str(ROOT))
        from server import Handler,VERSION
        self.assertEqual(VERSION,'2.4.0')
        self.assertTrue(hasattr(Handler,'do_POST'))  # only ephemeral LAN chat uses POST

if __name__=='__main__':unittest.main()
