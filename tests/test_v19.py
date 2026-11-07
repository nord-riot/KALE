"""KALE v1.9 Android/Termux and offline map regression tests."""
import base64
import importlib.util
import json
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
import server
spec=importlib.util.spec_from_file_location('kale_map_pack',ROOT/'tools/map_pack.py')
mp=importlib.util.module_from_spec(spec);spec.loader.exec_module(mp)
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL/nwAAAABJRU5ErkJggg==')

def make_map(path,fmt='png',blob=PNG):
    with sqlite3.connect(path) as c:
        c.executescript('''CREATE TABLE metadata(name TEXT,value TEXT);
            CREATE TABLE tiles(zoom_level INTEGER,tile_column INTEGER,tile_row INTEGER,tile_data BLOB);
            CREATE UNIQUE INDEX idx_t ON tiles(zoom_level,tile_column,tile_row);''')
        c.execute('INSERT INTO metadata VALUES (?,?)',('format',fmt))
        c.execute('INSERT INTO metadata VALUES (?,?)',('name','İzmir test haritası'))
        c.execute('INSERT INTO tiles VALUES (?,?,?,?)',(0,0,0,blob))

class AndroidMapV19(unittest.TestCase):
    def test_termux_gps_only_localhost(self):
        payload,status=server.gps_from_termux('192.168.1.2',finder=lambda name:'/usr/bin/fake')
        self.assertEqual(status,403);self.assertIn('sadece',payload['error'])
        payload,status=server.gps_from_termux('127.0.0.1',finder=lambda name:None)
        self.assertEqual(status,503)

    def test_termux_gps_one_shot(self):
        calls=[]
        def run(cmd,**kw):
            calls.append((cmd,kw))
            return subprocess.CompletedProcess(cmd,0,stdout=json.dumps({'latitude':38.42,'longitude':27.14,'accuracy':8}),stderr='')
        data,status=server.gps_from_termux('::1',runner=run,finder=lambda name:'/somewhere/termux-location')
        self.assertEqual(status,200);self.assertAlmostEqual(data['latitude'],38.42)
        self.assertEqual(calls[0][0],['/somewhere/termux-location','-p','gps','-r','once'])
        self.assertEqual(calls[0][1]['timeout'],18)
        self.assertFalse(data['cached'])

    def test_termux_gps_bad_coord_and_timeout(self):
        def bad(cmd,**kw):return subprocess.CompletedProcess(cmd,0,stdout='{"latitude":999,"longitude":0}',stderr='')
        data,status=server.gps_from_termux('127.0.0.1',runner=bad,finder=lambda name:'termux-location')
        self.assertEqual(status,503)
        def slow(cmd,**kw):raise subprocess.TimeoutExpired(cmd,kw['timeout'])
        data,status=server.gps_from_termux('127.0.0.1',runner=slow,finder=lambda name:'termux-location')
        self.assertEqual(status,503)

    def test_map_pack_inspection_and_server_xyz_tms(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);path=folder/'izmir.mbtiles';make_map(path)
            info=mp.inspect(path)
            self.assertEqual(info['tiles'],1);self.assertEqual(info['minzoom'],0)
            target=folder/'data/maps/turkiye.mbtiles'
            result,msg=mp.install(path,target=target)
            self.assertTrue(target.exists())
            self.assertEqual(result['format'],'png')
            with patch.object(server,'MAP_DB',target):
                self.assertTrue(server.map_details()['installed'])
                mime,blob=server.read_map_tile(0,0,0)
                self.assertEqual(mime,'image/png');self.assertEqual(blob,PNG)
                self.assertIsNone(server.read_map_tile(1,4,0))
            with self.assertRaises(FileExistsError):mp.install(path,target=target)

    def test_map_pack_wrong_format_or_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.mbtiles';make_map(p,'pbf')
            with self.assertRaisesRegex(ValueError,'Vektör'):mp.inspect(p)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.mbtiles';make_map(p,'png',b'not a png')
            with self.assertRaisesRegex(ValueError,'biçimi'):mp.inspect(p)

    def test_map_pack_replacement_preserves_backup(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);src=folder/'src.mbtiles';make_map(src)
            target=folder/'maps/turkiye.mbtiles';mp.install(src,target)
            with self.assertRaises(FileExistsError):mp.install(src,target)
            _,msg=mp.install(src,target,replace=True)
            self.assertTrue(target.with_suffix('.mbtiles.previous').exists())
            with self.assertRaises(FileExistsError):mp.install(src,target,replace=True)

    def test_phone_ui_and_permissions_policy(self):
        html=(ROOT/'web/harita.html').read_text('utf8')
        js=(ROOT/'web/assets/map.js').read_text('utf8')
        source=(ROOT/'server.py').read_text('utf8')
        for id in ('gpsBrowser','gpsTermux','gpsToPoint','gpsStatus','targetStatus'):
            self.assertIn('id="'+id+'"',html)
        self.assertIn('getCurrentPosition',js)
        self.assertNotIn('watchPosition(',js)
        self.assertIn('/api/gps/once',js)
        self.assertIn("geolocation=(self)",source)
        self.assertEqual(server.VERSION,'2.4.0')

    def test_termux_installer_and_user_docs(self):
        p=ROOT/'deploy/install-termux.sh'
        self.assertTrue(p.is_file())
        self.assertEqual(subprocess.run(['bash','-n',str(p)],capture_output=True).returncode,0)
        self.assertTrue((ROOT/'tools/map_pack.py').exists())

if __name__=='__main__':unittest.main()
