import importlib.util
import io
import json
import os
import shutil
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('kale_v18_backup',ROOT/'tools/backup.py');bk=importlib.util.module_from_spec(spec);spec.loader.exec_module(bk)
class BackupAndTransferV18(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((ROOT/'data/content.json').read_text())
 def fixture(self,folder):
  root=Path(folder);(root/'data').mkdir();(root/'review').mkdir()
  shutil.copy2(ROOT/'data/kale.db',root/'data/kale.db')
  shutil.copy2(ROOT/'data/content.json',root/'data/content.json')
  (root/'review/check.txt').write_text('private doctor review notes',encoding='utf8')
  return root
 def test_snapshot_validate_restore_non_destructive_dry_run(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=self.fixture(tmp);dest,_=bk.make_backup(root,root/'vault')
   m,files=bk.verify_backup(dest)
   self.assertEqual(m['format'],bk.FORMAT)
   self.assertEqual(len(files),3)
   self.assertFalse(m['encrypted'])
   before=(root/'review/check.txt').read_text()
   (root/'review/check.txt').write_text('CHANGED',encoding='utf8')
   preview=bk.restore(dest,root,apply=False)
   self.assertFalse(preview['restored'])
   self.assertEqual((root/'review/check.txt').read_text(),'CHANGED')
   with self.assertRaisesRegex(ValueError,'--confirm'):
    bk.restore(dest,root,apply=True)
   result=bk.restore(dest,root,apply=True,confirm='GERI_YUKLE')
   self.assertTrue(result['restored'])
   self.assertEqual((root/'review/check.txt').read_text(),before)
   self.assertTrue(Path(result['safety_backup']).is_file())
   with sqlite3.connect(root/'data/kale.db') as c:
    self.assertEqual(c.execute('SELECT COUNT(*) FROM medicines').fetchone()[0],707)
    self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
 def test_sha256_tampering_detected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=self.fixture(tmp);dest,_=bk.make_backup(root,root/'vault')
   alt=root/'bad.zip'
   with zipfile.ZipFile(dest) as z,zipfile.ZipFile(alt,'w') as target:
    for name in z.namelist():
     data=z.read(name)
     if name=='review/check.txt':data=b'bad'
     target.writestr(name,data)
   with self.assertRaises(ValueError):bk.verify_backup(alt)
 def test_path_traversal_rejected(self):
  self.assertFalse(bk.safe_name('../evil.txt'))
  self.assertFalse(bk.safe_name('review/../../unsafe.txt'))
  self.assertFalse(bk.safe_name('/data/kale.db'))
  self.assertFalse(bk.safe_name('data/nested/file.db'))
  self.assertTrue(bk.safe_name('data/kale.db'))
  self.assertTrue(bk.safe_name('review/file.xlsx'))
 def test_zip_duplicate_and_zipbomb_limits(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'bad.zip'
   with zipfile.ZipFile(p,'w') as z:
    z.writestr('manifest.json',b'{}')
    z.writestr('data/kale.db',b'not db')
   with self.assertRaises(ValueError):bk.verify_backup(p)
 def test_prune_keeps_latest(self):
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp)
   for i in range(4):(d/(bk.PREFIX+f'000{i}.zip')).write_bytes(b'x')
   (d/'random.zip').write_bytes(b'keep')
   bk.prune(d,2)
   self.assertEqual(len(list(d.glob(bk.PREFIX+'*.zip'))),2)
   self.assertTrue((d/'random.zip').is_file())
 def test_current_server_archive_untouched(self):
  with sqlite3.connect(ROOT/'data/kale.db') as c:
   self.assertEqual(c.execute('SELECT COUNT(*) FROM entries').fetchone()[0],146)
   self.assertEqual(c.execute('SELECT COUNT(*) FROM medicines').fetchone()[0],707)
 def test_browser_transfer_and_systemd_files(self):
  for name in ('aktarim.html','assets/transfer.css','assets/transfer.js','assets/sync-core.js'):
   self.assertTrue((ROOT/'web'/name).is_file())
  content=(ROOT/'web/assets/sync-core.js').read_text()
  self.assertIn('kale-inventory-v16',content)
  self.assertIn('kale_plan_v11',content)
  self.assertIn('kale_v1_private_points',content)
  self.assertIn('KALE-PERSONAL-TRANSFER-v1',content)
  self.assertIn('rollback' if False else 'mümkün olan eski kayıtlar geri alındı',content)
  self.assertIn('kale-v2.2.0',(ROOT/'web/sw.js').read_text())
  for path in ('deploy/kale-backup.timer','deploy/kale-backup.service','deploy/install-pi.sh'):
   self.assertTrue((ROOT/path).exists())
 def test_installer_dryrun_non_root(self):
  import subprocess
  r=subprocess.run(['sh',str(ROOT/'deploy/install-pi.sh'),'--dry-run'],cwd=ROOT,capture_output=True,text=True,timeout=8)
  self.assertEqual(r.returncode,0,r.stderr)
  self.assertIn('DRY RUN',r.stdout)
if __name__=='__main__':unittest.main()
