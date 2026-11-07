"""KALE 2.1: vector tiles, secure BRouter proxy, downloader and Wi-Fi chat."""
import gzip
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import routing
import chat_core

# Construct a valid tiny protobuf MVT containing a two-point road line.
def varint(v):
    result=bytearray()
    while v>127:result.append((v&127)|128);v>>=7
    result.append(v);return bytes(result)
def f(n,v,wire=2):return varint((n<<3)|wire)+(varint(len(v))+v if wire==2 else varint(v))
def road_tile():
    val=f(1,b'primary')
    feat=f(2,b'\x00\x00')+f(3,2,0)+f(4,b'\x09\x80\x20\x80\x20\x0a\x80\x20\x00')
    layer=f(1,b'transportation')+f(2,feat)+f(3,b'class')+f(4,val)+f(5,4096,0)+f(15,2,0)
    return f(3,layer)

class OfflineMapTest(unittest.TestCase):
    def test_mvt_read_compressed_and_tms_y(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'turkiye-street.mbtiles').parent.mkdir(exist_ok=True)
            path=folder/'turkiye-street.mbtiles'
            with sqlite3.connect(path) as c:
                c.executescript('''CREATE TABLE metadata(name TEXT,value TEXT);
                    CREATE TABLE tiles(zoom_level INTEGER,tile_column INTEGER,tile_row INTEGER,tile_data BLOB);''')
                c.executemany('INSERT INTO metadata VALUES (?,?)',[('name','Sokak test'),('format','pbf'),('minzoom','4'),('maxzoom','14')])
                c.execute('INSERT INTO tiles VALUES (5,10,21,?)',(gzip.compress(road_tile()),)) # xyz y=10
            with patch.object(routing,'MAP_DIR',folder):
                self.assertTrue(routing.inspect_street_map()['installed'])
                data=routing.read_vector_tile(5,10,10)
                self.assertEqual(data[1],road_tile())
                self.assertIsNone(routing.read_vector_tile(5,10,11))
                self.assertIsNone(routing.read_vector_tile(100,10,10))

    def test_reject_fake_street_mbtiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'turkiye-street.mbtiles'
            with sqlite3.connect(p) as c:c.executescript('CREATE TABLE metadata(name TEXT,value TEXT); INSERT INTO metadata VALUES ("format","png"); CREATE TABLE tiles(zoom_level INT,tile_column INT,tile_row INT,tile_data BLOB);')
            with patch.object(routing,'MAP_DIR',Path(tmp)):
                self.assertFalse(routing.inspect_street_map()['installed'])

    def test_10_regions_coverage(self):
        self.assertEqual(len(routing.SEGMENTS),10)
        self.assertIn('E45_N40.rd5',routing.SEGMENTS)
        self.assertIn('E25_N35.rd5',routing.SEGMENTS)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(routing,'ROUTING_DIR',Path(tmp)):
                self.assertEqual(routing.get_routing_status()['segments_found'],0)

    def test_route_proxy_passes_only_known_profiles_to_loopback(self):
        out={'type':'FeatureCollection','features':[{'geometry':{'type':'LineString','coordinates':[[27.14,38.42],[27.15,38.425]]},'properties':{'track-length':'1400','total-time':'900'}}]}
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,n):return json.dumps(out).encode('utf-8')
        calls=[]
        def opener(url,timeout):calls.append((url,timeout));return Response()
        result=routing.calculate_route(38.42,27.14,38.425,27.15,'walk',opener=opener)
        self.assertEqual(result['features'][0]['properties']['track_length_m'],1400)
        self.assertIn('127.0.0.1:17777',calls[0][0]);self.assertIn('profile=shortest',calls[0][0]);self.assertIn('%7C',calls[0][0])
        with self.assertRaises(routing.RoutingError):routing.calculate_route(38.42,27.14,38.425,27.15,'http://evil',opener=opener)
        with self.assertRaises(routing.RoutingError):routing.calculate_route(99,27.14,38.425,27.15,'walk',opener=opener)
        with self.assertRaises(routing.RoutingError):routing.calculate_route(38.42,27.14,38.42,27.14,'walk',opener=opener)

    def test_route_does_not_invent_lines_when_engine_unavailable(self):
        def unavailable(url,timeout):raise ConnectionRefusedError('no BRouter')
        with self.assertRaises(routing.RoutingError) as c:routing.calculate_route(38.42,27.14,38.425,27.15,'walk',opener=unavailable)
        self.assertEqual(c.exception.status,503)

    def test_download_is_explicit_online_and_10_segments(self):
        path=ROOT/'tools/turkiye_full.py'
        self.assertTrue(path.is_file())
        code=path.read_text()
        self.assertIn('brouter.de/brouter/segments4/',code)
        self.assertIn('turkey.osm.mbtiles-shortbread.zip',code)
        self.assertNotIn('tile.openstreetmap.org',code)
        self.assertIn('if a.dry_run:',code)

    def test_chat_multiple_users_roster_and_no_db(self):
        chat=chat_core.LANChat(ttl=30)
        a=chat.join('Deniz',now=1000);b=chat.join('Mert',now=1000)
        self.assertEqual(chat.snapshot(a['token'],now=1000)['online'],['Deniz','Mert'])
        chat.send(a['token'],'Merhaba Wi-Fi!',now=1001)
        self.assertEqual(chat.snapshot(b['token'],now=1002)['messages'][0]['text'],'Merhaba Wi-Fi!')
        with self.assertRaises(chat_core.ChatError):chat.join('Deniz',now=1004)
        chat.leave(a['token'])
        self.assertEqual(chat.snapshot(b['token'],now=1005)['online'],['Mert'])

    def test_frontend_bundle(self):
        sw=(ROOT/'web/sw.js').read_text()
        for item in ('/assets/vector-tile.js','/assets/route.js','/rota.html','/sohbet.html','/baglan.html'):
            self.assertIn(item,sw)
        for html in ('harita.html','rota.html'):
            txt=(ROOT/'web'/html).read_text()
            for field in ('routeFind','routeMode','routeStartLat','routeEndLat','routeExport'):
                self.assertIn(field,txt)

if __name__=='__main__':unittest.main()
