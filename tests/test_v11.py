"""KALE 1.1 regression tests for personal plan and offline packaging."""
import ast
import json
import re
import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

class ElementCollector(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=set();self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        if tag in ('script','link'):
            self.links.append(a.get('src') or a.get('href',''))

class V11Features(unittest.TestCase):
    def test_plan_fields_and_scripts(self):
        parser=ElementCollector();parser.feed((WEB/'plan.html').read_text())
        for name in ('people','water','daily','meeting','contact','taskList','progress','uploadPlan','downloadPlan','printPlan','clearPlan'):
            self.assertIn(name,parser.ids)
        self.assertIn('/assets/plan.js',parser.links)
        self.assertIn('/assets/plan.css',parser.links)

    def test_offline_checker_fields(self):
        parser=ElementCollector();parser.feed((WEB/'offline.html').read_text())
        for name in ('prepare','recheck','checks','summary','overall','actionMessage'):
            self.assertIn(name,parser.ids)
        self.assertIn('/assets/offline.js',parser.links)

    def test_serviceworker_bundle_complete(self):
        js=(WEB/'sw.js').read_text()
        self.assertIn("CACHE='kale-v2.4.0'",js)
        self.assertEqual(js,(WEB/'service-worker.js').read_text())
        match=re.search(r'const CORE=(\[.*?\]);',js,flags=re.S)
        self.assertIsNotNone(match)
        core=ast.literal_eval(match.group(1))
        self.assertEqual(len(core),len(set(core)))
        for path in core:
            if path in ('/','/api/catalog'):continue
            self.assertTrue((WEB/path.lstrip('/')).is_file(),path)
        for resource in ('/plan.html','/assets/plan.js','/offline.html','/assets/offline.js','/api/catalog','/assets/medicines-offline.json'):
            self.assertIn(resource,core)

    def test_catalogue_snapshot_counts(self):
        import sqlite3
        with sqlite3.connect(ROOT/'data/kale.db') as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM medicines').fetchone()[0],707)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM entries').fetchone()[0],146)
        medicines=json.loads((WEB/'assets/medicines-offline.json').read_text())
        self.assertEqual(len(medicines['medicines']),707)

    def test_private_plan_is_not_transmitted(self):
        js=(WEB/'assets/plan.js').read_text()
        self.assertIn('localStorage',js)
        self.assertNotIn('fetch(',js)
        self.assertNotIn('XMLHttpRequest',js)
        self.assertIn('KALE-PLAN-1.1',js)
        self.assertIn('JSON.stringify',js)

    def test_no_untrusted_remote_code(self):
        for p in ('plan.html','offline.html'):
            s=(WEB/p).read_text()
            self.assertNotIn('src="https://',s)
            self.assertNotIn('href="http://',s)

if __name__=='__main__':unittest.main()
