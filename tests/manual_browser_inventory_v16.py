"""Standalone Chromium UI integration test with stubbed localStorage.
No network/server access; run only if Playwright+Chromium available.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'
html=(WEB/'envanter.html').read_text('utf-8')
css=(WEB/'assets/module.css').read_text('utf-8')+'\n'+(WEB/'assets/inventory.css').read_text('utf-8')
core=(WEB/'assets/inventory-core.js').read_text('utf-8')
script=(WEB/'assets/inventory.js').read_text('utf-8')
html=html.replace('<link rel="stylesheet" href="/assets/module.css">','').replace('<link rel="stylesheet" href="/assets/inventory.css">','')
html=html.replace('<script src="/assets/inventory-core.js" defer></script>','').replace('<script src="/assets/inventory.js" defer></script>','')
html=html.replace('</head>',f'<style>{css}</style></head>')
fixture='''<script>
const __memory = {};
Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:(k)=>__memory[k]||null,setItem:(k,v)=>{__memory[k]=v},removeItem:(k)=>{delete __memory[k]}}});
</script>'''
html=html.replace('</body>',fixture+'<script>'+core+'</script><script>'+script+'</script></body>')
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':1340,'height':900},accept_downloads=True)
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html,wait_until='load')
 assert page.locator('#total').inner_text()=='0'
 page.locator('#name').fill('Pirinç 5 kg')
 page.locator('#category').select_option('gida')
 page.locator('#unit').select_option('kg')
 page.locator('#quantity').fill('5')
 page.locator('#minQuantity').fill('10')
 page.locator('#expiry').fill('2020-11-10')
 page.locator('#dateType').select_option('TETT')
 page.locator('#itemForm button[type=submit]').click()
 assert page.locator('#total').inner_text()=='1'
 assert page.locator('#low').inner_text()=='1'
 assert page.locator('#past').inner_text()=='1'
 page.locator('#name').fill('Su 5 litrelik bidon')
 page.locator('#category').select_option('su')
 page.locator('#unit').select_option('L')
 page.locator('#quantity').fill('20')
 page.locator('#minQuantity').fill('15')
 page.locator('#potable').check()
 page.locator('#itemForm button[type=submit]').click()
 assert page.locator('#total').inner_text()=='2'
 assert '20 L' in page.locator('#waterResult').inner_text()
 page.locator('#categoryFilter').select_option('su')
 assert page.locator('#inventoryRows tr').count()==1
 page.locator('#categoryFilter').select_option('')
 assert page.locator('#inventoryRows tr').count()==2
 page.on('dialog',lambda d: d.accept('-4'))
 page.locator('#inventoryRows tr').filter(has_text='Su 5 litrelik bidon').get_by_role('button',name='± Miktar').click()
 assert '16 L' in page.locator('#waterResult').inner_text()
 with page.expect_download() as dl:page.locator('#exportJSON').click()
 obj=json.loads(dl.value.path().read_text('utf-8'))
 assert len(obj['items'])==2 and obj['format']=='KALE-STOK-v1'
 with page.expect_download() as dl:page.locator('#exportCSV').click()
 csv=dl.value.path().read_text('utf-8')
 assert 'Pirinç 5 kg' in csv and 'Su 5 litrelik bidon' in csv
 # Validate import with an intentional replacement; no network used.
 new_backup={**obj,'items':[obj['items'][0]]}
 page.locator('#importJSON').set_input_files({'name':'stok.json','mimeType':'application/json','buffer':json.dumps(new_backup,ensure_ascii=False).encode('utf-8')})
 assert page.locator('#total').inner_text()=='1'
 # Duplicate IDs must be rejected and the previous state preserved.
 broken={**obj,'items':[obj['items'][0],obj['items'][0]]}
 page.locator('#importJSON').set_input_files({'name':'broken.json','mimeType':'application/json','buffer':json.dumps(broken,ensure_ascii=False).encode('utf-8')})
 assert page.locator('#total').inner_text()=='1'
 assert 'REDDEDİLDİ' in page.locator('#backupMessage').inner_text()
 # Re-import complete backup to produce a useful preview.
 page.locator('#importJSON').set_input_files({'name':'all.json','mimeType':'application/json','buffer':json.dumps(obj,ensure_ascii=False).encode('utf-8')})
 assert page.locator('#total').inner_text()=='2'
 page.screenshot(path='/mnt/data/KALE-v1.6-Stok-Envanteri-Onizleme.png',full_page=True)
 print('CHROMIUM UI: add food, water, SKT/TETT, low stock, water calculation, filter, adjust, JSON/CSV export, import, duplicate rejection OK')
 print('PAGE ERRORS',errors)
 assert not errors
 browser.close()
