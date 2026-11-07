"""v2.4 - offline Shortbread streets, one-command installation and safe downloads."""
import contextlib
import hashlib
import importlib.util
import io
import json
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import routing
spec=importlib.util.spec_from_file_location('turkiye_full',ROOT/'tools/turkiye_full.py')
full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)

def varint(v):
    x=bytearray()
    while v>=128:x.append((v&127)|128);v>>=7
    x.append(v);return bytes(x)
def field(n,v,wire=2):
    return varint((n<<3)|wire)+(varint(len(v))+v if wire==2 else varint(v))
def shortbread_tile():
    geometry=b'\x09\x80\x10\x80\x10\x0a\x80\x08\x00'
    def layer(name,key,value):
        feature=field(2,b'\x00\x00')+field(3,2,0)+field(4,geometry)
        return field(3,field(1,name.encode())+field(2,feature)+field(3,key.encode())+
                     field(4,field(1,value.encode()))+field(5,4096,0)+field(15,2,0))
    return layer('streets','kind','primary')+layer('street_labels','name','Atatürk Caddesi')

class MapV24(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Node runtime yok; yalnız tarayıcıda çalışır')
    def test_shortbread_street_and_name_are_actually_painted(self):
        tile=shortbread_tile()
        js=f'''const fs=require('fs'); const vm=require('vm');
        const window={{}};vm.runInNewContext(fs.readFileSync({json.dumps(str(ROOT/'web/assets/vector-tile.js'))},'utf8'),
          {{window,TextDecoder,Uint8Array}});
        const layers=window.KALEVector.decode(Uint8Array.from(Buffer.from('{tile.hex()}','hex')));
        const report={{names:layers.map(l=>l.name),strokes:[],texts:[]}};
        const ctx={{save(){{}},restore(){{}},beginPath(){{}},rect(){{}},clip(){{}},moveTo(){{}},lineTo(){{}},
          fill(){{}},closePath(){{}},setLineDash(){{}},stroke(){{report.strokes.push(this.strokeStyle)}},
          strokeText(t){{report.texts.push(t)}},fillText(t){{report.texts.push(t)}}}};
        window.KALEVector.paint(ctx,layers,0,0,256,14);
        console.log(JSON.stringify(report));'''
        r=subprocess.run(['node','-e',js],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr)
        report=json.loads(r.stdout)
        self.assertIn('streets',report['names'])
        self.assertIn('#f0d295',report['strokes'])
        self.assertIn('Atatürk Caddesi',report['texts'])

    def test_real_mbtiles_install_from_mocked_large_zip(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);source=folder/'source.mbtiles';z=folder/'external.zip';target=folder/'maps';target.mkdir()
            with sqlite3.connect(source) as db:
                db.executescript('CREATE TABLE metadata(name TEXT,value TEXT);'
                                 'CREATE TABLE tiles(zoom_level INT,tile_column INT,tile_row INT,tile_data BLOB);'
                                 'CREATE TABLE filler(blob BLOB);')
                db.executemany('INSERT INTO metadata VALUES (?,?)', [('format','pbf'),('name','Turkey Shortbread'),('minzoom','4'),('maxzoom','14')])
                db.execute('INSERT INTO tiles VALUES (14,9000,6100,?)',(shortbread_tile(),))
                db.execute('INSERT INTO filler VALUES (zeroblob(1500000))')
            from zipfile import ZipFile,ZIP_DEFLATED
            with ZipFile(z,'w',compression=ZIP_DEFLATED) as archive:
                archive.write(source,'region/sample.mbtiles')
            with patch.object(full,'MAPS',target),patch.object(routing,'MAP_DIR',target):
                with patch.object(full,'stream',side_effect=lambda u,p:(shutil.copyfile(z,p), 'fake digest')):
                    full.install_map();self.assertTrue(routing.inspect_street_map()['installed'])
                    self.assertTrue((target/'turkiye-street.mbtiles').exists())
                    self.assertFalse((target/'turkiye-shortbread.zip').exists())
                    full.install_map() # No repeated download.

    def test_versioned_brouter_jar_zip_is_accepted(self):
        from zipfile import ZipFile
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);zipfile=folder/'brouter.zip';dest=folder/'routing';dest.mkdir()
            with ZipFile(zipfile,'w') as z:
                z.writestr('brouter-1.7.10/brouter-1.7.10.jar',b'PKfakeJarExample')
                for n in ['lookups.dat','shortest.brf','fastbike.brf','car-vario.brf']:
                    z.writestr('brouter-1.7.10/profiles2/'+n,b'demo')
            with patch.object(full,'ROUTER_SHA256',hashlib.sha256(zipfile.read_bytes()).hexdigest()),patch.object(full,'ROUTING',dest),patch.object(full,'stream',side_effect=lambda u,p:(shutil.copyfile(zipfile,p),'sha')):
                full.install_engine()
                self.assertEqual((dest/'brouter.jar').read_bytes(),b'PKfakeJarExample')
                self.assertTrue((dest/'profiles2/lookups.dat').exists())
                self.assertFalse((dest/'brouter-release.zip').exists())

    def test_resume_download_requires_consistent_range_and_validator(self):
        class Resp:
            def __init__(self,code,headers,body):self.status=code;self.headers=headers;self.body=io.BytesIO(body)
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def read(self,n):return self.body.read(n)
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'data.rd5';part=Path(str(dest)+'.part');meta=Path(str(dest)+'.part.meta')
            part.write_bytes(b'A'*1024);meta.write_text('"v1"')
            response=Resp(206,{'Content-Length':'2048','Content-Range':'bytes 1024-3071/3072','ETag':'"v1"'},b'B'*2048)
            with patch.object(full.urllib.request,'urlopen',return_value=response):
                size,sha=full.stream('https://example.org/map',dest)
            self.assertEqual(size,3072)
            self.assertEqual(sha,hashlib.sha256(b'A'*1024+b'B'*2048).hexdigest())
            self.assertFalse(part.exists());self.assertFalse(meta.exists())

    def test_bootstrap_shell_and_installer_steps(self):
        a=(ROOT/'deploy/bootstrap-termux.sh').read_text()
        b=(ROOT/'deploy/install-all-termux.sh').read_text()
        self.assertIn('git clone',a);self.assertIn('git -C',a)
        for required in ('turkiye_full.py map','install-24x7.sh install','kale-24x7','turkiye_full.py segments'):
            self.assertIn(required,b)
        self.assertIn('KALE_ENABLE_BROUTER', (ROOT/'deploy/install-24x7.sh').read_text())
        if shutil.which('bash'):
            p=subprocess.run(['bash','-n',str(ROOT/'deploy/bootstrap-termux.sh'),str(ROOT/'deploy/install-all-termux.sh'),str(ROOT/'deploy/install-24x7.sh')],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)

    def test_readme_and_service_worker_version(self):
        self.assertIn('v2.4', (ROOT/'README.md').read_text())
        self.assertIn('kale-v2.',(ROOT/'web/sw.js').read_text())

if __name__=='__main__':unittest.main()
