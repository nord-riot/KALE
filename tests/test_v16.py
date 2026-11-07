"""Inventory v1.6 packaging and JS data-validation integration."""
import ast
import json
import re
import shutil
import sqlite3
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

class InventoryV16Tests(unittest.TestCase):
 def test_preserves_previous_catalog(self):
  with sqlite3.connect(ROOT/'data/kale.db') as c:
   self.assertEqual(c.execute('SELECT COUNT(*) FROM medicines').fetchone()[0],707)
   self.assertEqual(c.execute('SELECT COUNT(*) FROM entries').fetchone()[0],146)
   self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
  self.assertEqual(len(json.loads((WEB/'assets/shelter-water.json').read_text())['cards']),18)
  self.assertEqual(len(json.loads((WEB/'assets/food-energy-winter.json').read_text())['cards']),24)

 def test_inventory_ui_and_core(self):
  html=(WEB/'envanter.html').read_text('utf-8')
  for field in ('itemForm','name','category','quantity','unit','minQuantity','expiry','dateType','potable','location','batch','notes','exportJSON','exportCSV','importJSON','waterResult','history'):
   self.assertIn(f'id="{field}"',html)
  self.assertIn('/assets/inventory-core.js',html)
  self.assertIn('/assets/inventory.js',html)
  self.assertIn('SKT',html)
  self.assertIn('TETT',html)

 def test_private_browser_only_storage(self):
  js=(WEB/'assets/inventory.js').read_text('utf-8')
  self.assertIn('localStorage',js)
  self.assertNotIn('fetch(',js)
  self.assertNotIn('XMLHttpRequest',js)
  self.assertNotIn('innerHTML',js)
  self.assertIn('K.validateBackup',js)
  self.assertIn('window.print()',js)

 def test_precache_and_version(self):
  sw=(WEB/'sw.js').read_text('utf-8')
  self.assertEqual(sw,(WEB/'service-worker.js').read_text('utf-8'))
  self.assertIn('kale-v2.2.0',sw)
  hit=re.search(r'const CORE=(\[.*?\]);',sw,re.S)
  self.assertIsNotNone(hit)
  precache=ast.literal_eval(hit.group(1))
  self.assertEqual(len(precache),len(set(precache)))
  for path in ('/envanter.html','/assets/inventory.js','/assets/inventory-core.js','/assets/inventory.css'):
   self.assertIn(path,precache)
  self.assertIn('/envanter.html',(WEB/'index.html').read_text('utf-8'))
  self.assertIn('envanter.html',(ROOT/'server.py').read_text('utf-8'))
  self.assertTrue(all((WEB/p.lstrip('/')).exists() for p in precache if p not in ('/','/api/catalog')))

 @unittest.skipUnless(shutil.which('node'),'Node.js needed only to run JS unit tests, not to serve KALE')
 def test_core_logic(self):
  script=r'''
const assert=require('node:assert/strict');
const K=require('./web/assets/inventory-core.js');
const base={id:'ka123456789abc',name:'Su 5L',category:'su',quantity:20,unit:'L',minQuantity:25,location:'Raf',batch:'A1',expiry:'2026-11-10',dateType:'SKT',potable:true,notes:''};
const item=K.validateItem(base);
assert.equal(K.status(item,new Date(2026,10,3)).date,'soon');
assert.equal(K.status(item,new Date(2026,10,11)).date,'past');
assert.equal(K.status(item,new Date(2026,10,3)).low,true);
let stats=K.metrics([item],4,2.5,new Date(2026,10,3));
assert.equal(stats.waterLiters,20);assert.equal(stats.waterDays,2);
stats=K.metrics([item],4,2.5,new Date(2026,10,11));assert.equal(stats.waterLiters,0);
const ml=K.validateItem({...base,id:'kb123456789abc',quantity:1500,unit:'mL',potable:true,expiry:''});
assert.equal(K.metrics([item,ml],3,1,new Date(2026,10,11)).waterLiters,1.5);
assert.throws(()=>K.validateItem({...base,category:'ilac',potable:true}));
assert.throws(()=>K.validateItem({...base,expiry:'2026-02-30'}));
assert.throws(()=>K.validateItem({...base,quantity:-1}));
assert.throws(()=>K.validateItem({...base,quantity:NaN}));
assert.throws(()=>K.validateItem({...base,name:'x'.repeat(101)}));
assert.throws(()=>K.validateBackup({format:'KALE-STOK-v1',people:4,perPersonDay:3,items:[item,item]}));
const backup={format:'KALE-STOK-v1',people:4,perPersonDay:3,items:[item,ml]};
assert.equal(K.validateBackup(backup).items.length,2);
let csv=K.toCSV([{...item,name:'=1+2',notes:'+SUM(1,2)'}]);
assert(csv.includes("'=1+2"));assert(csv.includes("'+SUM"));
assert.equal(K.status(item,new Date(2026,10,3),3).date,'dated');
console.log('KALE inventory core: validation, status, water conversion, back-ups and CSV injection checks OK');
'''
  r=subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True,timeout=15)
  self.assertEqual(r.returncode,0,r.stderr)

 def test_read_only_server_contract(self):
  s=(ROOT/'server.py').read_text('utf-8')
  self.assertIn("VERSION = '2.2.0'",s)
  self.assertIn('def do_POST(',s)  # RAM-only chat; no content DB writes
  self.assertNotIn('doctor_reviews.sqlite3',str(WEB))

if __name__=='__main__':unittest.main()
