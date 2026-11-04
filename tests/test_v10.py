import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('kale_server_v10',ROOT/'server.py')
server=importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

class V10Modules(unittest.TestCase):
    def test_field_guides_and_local_sources(self):
        payload=json.loads((ROOT/'web/assets/field-guides.json').read_text())
        self.assertGreaterEqual(len(payload['guides']),8)
        for guide in payload['guides']:
            self.assertEqual(guide['review_status'],'EDİTORYAL TASLAK')
            self.assertGreaterEqual(len(guide['steps']),4)
            self.assertTrue((ROOT/'web'/guide['diagram'].lstrip('/')).is_file())
            for src in guide['sources']:self.assertTrue(src['url'].startswith('https://'))

    def test_plant_catalogue_no_edible_guidance(self):
        payload=json.loads((ROOT/'web/assets/poisonous-plants.json').read_text())
        self.assertEqual(len(payload['plants']),28)
        for plant in payload['plants']:
            self.assertFalse(plant['consumable'])
            self.assertTrue(plant['source_url'].startswith('https://'))
            self.assertIn('KONTROL',plant['review_status'])

    def test_offline_precache_complete(self):
        txt=(ROOT/'web/sw.js').read_text()
        from ast import literal_eval
        import re
        match=re.search(r'const CORE=(\[.*?\]);',txt,flags=re.S)
        self.assertIsNotNone(match)
        core=literal_eval(match.group(1))
        for path in core:
            if path in ('/','/api/catalog'):continue
            self.assertTrue((ROOT/'web'/path.lstrip('/')).is_file(),path)
        self.assertIn('/harita.html',core)
        self.assertIn('/doga.html',core)
        self.assertIn('/saha.html',core)

    def test_mbtiles_without_file(self):
        with patch.object(server,'MAP_DB',Path('/___kale___no_map___/missing.mbtiles')):
            self.assertFalse(server.map_details()['installed'])
            self.assertIsNone(server.read_map_tile(3,2,2))

    def test_mbtiles_tms_y_flip_and_validation(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'test.mbtiles'
            import base64
            png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL/nwAAAABJRU5ErkJggg==')
            with sqlite3.connect(path) as c:
                c.execute('CREATE TABLE metadata(name TEXT,value TEXT)')
                c.execute('CREATE TABLE tiles(zoom_level INTEGER,tile_column INTEGER,tile_row INTEGER,tile_data BLOB)')
                c.executemany('INSERT INTO metadata VALUES(?,?)',[('name','KALE test'),('format','png'),('minzoom','0'),('maxzoom','6')])
                # z=2, XYZ y=1 should become TMS row 2
                c.execute('INSERT INTO tiles VALUES(2,1,2,?)',(png,))
            with patch.object(server,'MAP_DB',path):
                self.assertTrue(server.map_details()['installed'])
                mime,blob=server.read_map_tile(2,1,1)
                self.assertEqual(mime,'image/png');self.assertEqual(blob,png)
                self.assertIsNone(server.read_map_tile(2,1,2))
                self.assertIsNone(server.read_map_tile(99,1,1))
                self.assertIsNone(server.read_map_tile(2,100,1))
                self.assertIsNone(server.read_map_tile(2,1,-1))

    def test_vector_mbtiles_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'v.mbtiles'
            with sqlite3.connect(path) as c:
                c.execute('CREATE TABLE metadata(name TEXT,value TEXT)')
                c.execute('CREATE TABLE tiles(zoom_level INTEGER,tile_column INTEGER,tile_row INTEGER,tile_data BLOB)')
                c.execute('INSERT INTO metadata VALUES("format","pbf")')
            with patch.object(server,'MAP_DB',path):
                self.assertFalse(server.map_details()['installed'])
                self.assertIsNone(server.read_map_tile(2,1,1))

    def test_no_medicine_approvals(self):
        with sqlite3.connect(ROOT/'data/kale.db') as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM medicines').fetchone()[0],707)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM medicines WHERE review_status NOT LIKE '%BEKLİYOR%' AND review_status NOT LIKE '%ONAYI YOK%' ").fetchone()[0],0)

if __name__=='__main__':unittest.main()
